# -*- coding: utf-8 -*-
"""Приток: страницы со списком сделок на сайтах консультантов (13 ноября 2026).

ЗАЧЕМ. Инвестбанк или юрфирма ведет на своем сайте список сделок, которые
сопровождала: плитки «tombstones» (Advance Capital, Aspring Capital) или
ленту пресс-релизов («BIRCH сопровождала…»). Приток читал СМИ и телеграм, а
сайты фирм стояли в реестре выключенными — и у Advance Capital на сайте было
28 сделок с 2022 года, а в базе фирма названа в трех (владелец, 13 ноября
2026: «добавь сайты advance и aspring в проверку притока так и других
консультантов которые публикуют сделки»).

КАК УСТРОЕНО. Один разборщик и правило на фирму (`PAGES`): чем страница
режется на блоки, где в блоке заголовок, дата, ссылка, текст и роль фирмы.
Запись уходит в сырье в том же виде, что новость из ленты или пост канала
(`{source_id, url, title, summary, published}`), и дальше идет ОБЫЧНЫМ путем:
`triage.py` → `match.py` (карточка уже есть — `enrich`/`card_news`, которые
берут консультанта из шапки «<Фирма> выступил …» правилом
`advisors.lead_advisor`, как у постов @LawFirms) → иначе `draft.py` и ворота.
Отдельной дороги в базу у сайтов фирм нет.

ТРИ ПРАВИЛА, РАДИ КОТОРЫХ ЭТО НЕ ПРОСТО «ЕЩЕ ОДНА ЛЕНТА».
  * ПАМЯТЬ. Страница отдает все свои сделки каждый раз, а сырье в git не
    хранится. Виденное лежит в `deal_pages_seen.json` (в git, его коммитит
    `sweep.py`): запись идет в сырье один раз.
  * ЗАСЕВ. Источник, которого в памяти еще нет, при первом заборе помечает
    виденным ВСЕ, что на странице уже есть, и не отдает ничего: старые
    сделки очередь владельцу не заваливают. Дальше идет только новое.
  * НЕ СДЕЛКА — НЕ ИДЕТ. Обезличенная плитка («Продажа крупного
    производителя яблок стратегическому инвестору») — сделку по ней не
    опознать; реструктуризация облигаций — не M&A; в ленте новостей фирмы
    берется только объявление о сопровождении сделки (`NEED_*`), без
    рейтингов, конференций и назначений (`SKIP_NEWS`).

Запуск (сети не нужно, если дать сохраненную страницу):
    python3 pipeline/ingest/deal_pages.py                      # все страницы: что видно и что ново
    python3 pipeline/ingest/deal_pages.py --only firm:advancecap
    python3 pipeline/ingest/deal_pages.py --only firm:aspring --file page.html
    python3 pipeline/ingest/deal_pages.py --match               # и сверка с карточками базы
    python3 pipeline/ingest/deal_pages.py --seed --write        # засеять память заново (новый источник)
"""
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from urllib.parse import urljoin

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import advisors  # noqa: E402

SEEN = os.path.join(HERE, 'deal_pages_seen.json')
SINCE = 2022                     # сделки старше в сырье не идут
MAX_AGE_DAYS = 365               # новая запись со старой датой: помним, но не отдаем
BROWSER_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')
TRIES, PAUSE_S, TIMEOUT = 4, 3, 30

# Объявление о сопровождении сделки в ленте новостей фирмы: глагол
# сопровождения И слово сделки — оба в заголовке. Новость о рейтинге,
# конференции, назначении или судебном споре глагол иногда несет
# («выступил на форуме»), поэтому отдельно — чего в заголовке быть не должно.
NEED_ADVISED = re.compile(
    r'консультир|сопровожд|сопровод|представл\w+ интерес|выступил\w* (?:\w+ ){0,2}(?:консультант|советник)'
    r'|юридическ\w+ поддержк|правов\w+ поддержк|advis', re.I)
NEED_DEAL = re.compile(
    r'сделк|приобрет|покупк|продаж|выкуп|слияни|объединени|совместн\w+ предприят|\bIPO\b|\bSPO\b'
    r'|дол[июейя]\b|акци[йяи]\b|инвестици|инвестирова|M&A|M&amp;A', re.I)
SKIP_NEWS = re.compile(
    r'рейтинг|рэнкинг|ренкинг|сделк\w+ года|сделок года|преми[яию]|наград|номинаци|лауреат|признан\w*|в топ\b|топ-\d'
    r'|форум|конференц|вебинар|семинар|круглый стол|лекци|выступил\w* на\b|назнач|присоедин\w+ к команде'
    r'|дайджест|обзор|комментар|интервью|стать[яеи]\b|арбитраж|\bспор|\bсуд|банкротств|взыскани|итоги'
    r'|тренд|лидер|отмечен|\bмы\b|подход\w* в|кредит|долгов|\bдолга\b|облигаци', re.I)

# Не сделки M&A на страницах инвестбанков: долговые истории.
NOT_MNA = re.compile(r'реструктуризаци\w+ (?:\w+ ){0,3}(?:облигаци|еврооблигаци|долг|задолженност|кредит)'
                     r'|consent solicitation|согласи\w+ держателей|выкуп\w* (?:евро)?облигаци'
                     r'|замещающ\w+ облигаци|размещени\w+ облигаци', re.I)

_FIN_ROLE = re.compile(r'^(?:эксклюзивный\s+)?финансовый\s+(консультант|советник)\b\s*(.*)$', re.I)

# Правила на фирму. Ключ — id источника в `sources.json`.
#   page   — адрес страницы со списком;   firm — имя фирмы, как в базе;
#   block  — регулярка НАЧАЛА одного блока (страница режется по ней);
#   title / text / role / date / link — регулярки внутри блока, группа 1;
#   kind   — 'tombstone' (плитка инвестбанка: заголовок — сама сделка, роль
#            отдельной строкой; фильтр — обезличенность и NOT_MNA), 'project'
#            (плитка проекта юрфирмы: то же плюс слово сделки в заголовке) или
#            'news' (по умолчанию; лента: заголовок — объявление фирмы; фильтр
#            NEED_* и SKIP_NEWS).
PAGES = {
    'firm:advancecap': {
        'firm': 'Advance Capital', 'page': 'https://advancecapital.ru/sdelki/', 'kind': 'tombstone',
        'block': r'<div class="slide-d">',
        'title': r'<h3 class="title-slide">(.*?)</h3>',
        'text': r'<div class="hover-text">\s*<div>(.*?)</div>',
        'role': r'<p class="bottom-text tx-01">(.*?)</p>',
        'date': r'<p class="bottom-text tx-02">(.*?)</p>',
        'link': r'href="([^"]*/press-releases/\d+/?)"',
    },
    'firm:aspring': {
        'firm': 'Aspring Capital', 'page': 'https://aspring.capital/services', 'kind': 'tombstone',
        'block': r'<div class="services--item_wrap">',
        'title': r'<h3 class="deal-item__title[^"]*">(.*?)</h3>',
        'text': r'<div class="bullet-text_wrapper">\s*<h3[^>]*>(.*?)</h3>',
        'date': r'<div class="deal-card__date-2[^"]*">(.*?)</div>\s*</div>',
    },
    # Юрфирмы: лента пресс-релизов. Берется только объявление о сделке.
    'firm:birch': {
        'firm': 'BIRCH', 'page': 'https://birchlegal.ru/projects/',
        'block': r'<div class="media_item">',
        'title': r'<strong>\s*<a href="[^"]+">(.*?)</a>', 'text': r'</strong>\s*<p>(.*?)</p>',
        'date': r'<span>([^<]*20\d\d)</span>', 'link': r'<a href="(/projects/\d+/)"',
    },
    'firm:level': {
        'firm': 'LEVEL Legal Services', 'page': 'https://www.level-legal.com/news',
        'block': r'<div class="LayoutPostCard post"',
        'title': r'class="title typo-paragraph"[^>]*>(.*?)</div>',
        'text': r'class="desc typo-small-paragraph"[^>]*>(.*?)</div>',
        'date': r'class="typo-caption"[^>]*>(.*?)</div>', 'link': r'<a href="(/news/[^"]+)"',
    },
    'firm:orion': {
        'firm': 'Orion', 'page': 'https://orion-law.com/news',
        'block': r'<div class="sm:grid grid-cols-2 gap-20 relative group"',
        'title': r'class="typ-title-2xl[^"]*"[^>]*>(.*?)</div>',
        'text': r'class="typ-text-base[^"]*"[^>]*>(.*?)</a>',
        'date': r'class="typ-title-xs[^"]*"[^>]*>(.*?)</div>', 'link': r'<a href="(/news/[^"]+)"',
    },
    'firm:stonebridge': {
        'firm': 'Stonebridge Legal', 'page': 'https://www.stonebridgelegal.ru/ru/news/',
        'block': r'<li class="news-list__item',
        'title': r'<h2 class="n-card__title">(.*?)</h2>', 'text': r'<div class="n-card__desc">(.*?)</div>',
        'date': r'<div class="n-card__date">(.*?)</div>', 'link': r'<a class="n-card" href="([^"]+)"',
    },
    'firm:dgp': {
        'firm': 'Дякин, Горцунян и Партнеры', 'page': 'https://dgpartners.legal/mediaportal/',
        'block': r'<a href="/mediaportal/news/',
        'title': r'<h3 class="card__desc">(.*?)</h3>',
        'date': r'class="t2 card__date[^"]*">(.*?)</div>', 'link': r'<a href="(/mediaportal/news/[^"]+)"',
    },
    'firm:whitesquare': {
        'firm': 'White Square', 'page': 'https://www.whitesquarepartners.com/ru/news',
        'block': r'<div role="listitem" class="team-collection-item',
        'title': r'<h4[^>]*>(.*?)</h4>',
        'date': r'<p class="news-card-date">(.*?)</p>', 'link': r'href="(/ru/news/[^"]+)"',
    },
    'firm:epam': {
        'firm': 'ЕПАМ', 'page': 'https://epam.ru/ru/news',
        'block': r'<div class="post">',
        'title': r'<h3>\s*<a[^>]*>(.*?)</a>', 'text': r'</h3>\s*<p>(.*?)</p>',
        'date': r'<span class="date">(.*?)</span>', 'link': r'<a href="(https://epam\.ru/ru/news/view/[^"]+)"',
    },
    'firm:ivanyan': {
        'firm': 'Иванян и партнеры', 'page': 'https://ivanyan.partners/news/',
        'block': r'<div class="news-card[ "]',
        'title': r'<a class="news-card__title" href="[^"]+">(.*?)</a>',
        'date': r'pubdate">(.*?)</div>', 'link': r'<a class="news-card__title" href="([^"]+)"',
    },
    'firm:nikolaev': {
        'firm': 'Николаев и партнеры', 'page': 'https://nikolaew.ru/media/',
        'block': r'<a data-tabitem=',
        'title': r'<h4>(.*?)</h4>',
        'date': r'<div class="bottom__tags">\s*<span>(.*?)</span>', 'link': r'href="(/media/[^"]+)"',
    },
    'firm:asari': {
        'firm': 'Asari Legal', 'page': 'https://asari.legal/news/',
        'block': r'<div class="news-card ',
        'title': r'<h3 class="news-card__title">(.*?)</h3>', 'text': r'<p class="news-card__text">(.*?)</p>',
        'date': r'news-card__date">(.*?)</span>', 'link': r'<a class="news-card__link[^"]*" href="([^"]+)"',
    },
    'firm:althaus': {
        'firm': 'Althaus', 'page': 'https://althausgroup.ru/news/',
        'block': r'<div class="item__wrapper">',
        'title': r'<p class="__name">(.*?)</p>',
        'date': r'<p class="__date">(.*?)</p>', 'link': r'<a href="(/news/[^"?]+/)" class="__btn',
    },
    'firm:denuo': {
        'firm': 'Denuo', 'page': 'https://denuo.legal/ru/insights/releases/',
        'block': r'<a href="/ru/insights/releases/\w+/"\s+class="news-card"',
        'title': r'<span class="news-card__title">(.*?)</span>', 'text': r'<div class="news-card__text">(.*?)</div>',
        'date': r'<div class="news-card__date">(.*?)</div>', 'link': r'<a href="(/ru/insights/releases/\w+/)"',
    },
    # Плитки проектов без даты: имя клиента и описание. Заголовком идет
    # описание («Сопровождение … в сделке по продаже …»).
    'firm:betterchance': {
        'firm': 'Better Chance', 'page': 'https://betterchance.ru/projects/', 'kind': 'project',
        'block': r'<li class="card projects__item">',
        'prefix': r'projects__item_title">(.*?)</h4>', 'title': r'projects__item_descr">(.*?)</p>',
        'link': r'<a href="(/media_center/news/[^"]+)"',
    },
    'firm:alumni': {
        'firm': 'ALUMNI Partners', 'page': 'https://www.alumnipartners.ru/projects/', 'kind': 'project',
        'block': r'<div class="CommonListing-tile"',
        'title': r'CommonTilesProject-description">(.*?)</div>',
        'link': r'<a href="(/projects/\d+/)"',
    },
}


def label_of(src_id):
    """Имя источника для людей: «сайт Advance Capital»."""
    rule = PAGES.get(src_id) or {}
    return 'сайт %s' % rule.get('firm', src_id)


# ---------- сеть ----------

def http_get(url, tries=TRIES, pause=PAUSE_S):
    """Страница сайта фирмы с повторами: связь из контейнера рвется
    (Connection reset by peer), вторая-третья попытка обычно проходит.
    Отказ сайта (403, проверка «вы не робот») не обходится — это ошибка
    источника, она попадет в отчет забора."""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': BROWSER_UA, 'Accept-Language': 'ru,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml'})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404, 410):
                raise
            last = e
        except Exception as e:                                  # noqa: BLE001
            last = e
        if i + 1 < tries:
            time.sleep(pause)
    raise last


# ---------- разбор ----------

def clean(fragment):
    text = re.sub(r'<br\s*/?>', ' ', str(fragment or ''))
    text = html.unescape(re.sub(r'<[^>]+>', ' ', text)).replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', text).strip()


_MONTHS = ('январ', 'феврал', 'март', 'апрел', 'ма', 'июн', 'июл', 'август', 'сентябр', 'октябр', 'ноябр', 'декабр')
_MONTH_RX = (r'(январ[ьяе]|феврал[ьяе]|март[ае]?|апрел[ьяе]|ма[йяе]|июн[ьяе]|июл[ьяе]|август[ае]?'
             r'|сентябр[ьяе]|октябр[ьяе]|ноябр[ьяе]|декабр[ьяе])')
_DATE_NUM = re.compile(r'(?<!\d)(\d{1,2})\s*[./]\s*(\d{1,2})\s*[./]\s*(20\d\d)(?!\d)')
_DATE_WORD = re.compile(r'(?<!\d)(\d{1,2})\s+' + _MONTH_RX + r'\s+(20\d\d)', re.I)
_DATE_MONTH = re.compile(r'(?<![а-яё])' + _MONTH_RX + r'\s+(20\d\d)', re.I)


def _month_no(word):
    word = word.lower()
    # «ма» (май) — приставка «март»: длинные основы проверяются первыми.
    for i in sorted(range(12), key=lambda k: -len(_MONTHS[k])):
        if word.startswith(_MONTHS[i]):
            return i + 1
    return None


def find_date(text, today=None):
    """Дата из текста блока: «05.11.2026», «05 / 11 / 2026», «5 ноября 2026»,
    «Октябрь 2026». Месяц без дня — середина месяца, но не позже сегодня:
    плитка «Ноябрь 2026», появившаяся 3 ноября, не должна стать сделкой из
    будущего. Не нашлось — пустая строка (разбор возьмет день забора)."""
    text = clean(text)
    today = today or date.today()
    try:
        m = _DATE_NUM.search(text)
        if m:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        m = _DATE_WORD.search(text)
        if m:
            return date(int(m.group(3)), _month_no(m.group(2)), int(m.group(1))).isoformat()
        m = _DATE_MONTH.search(text)
        if m:
            return min(date(int(m.group(2)), _month_no(m.group(1)), 15), today).isoformat()
    except (ValueError, TypeError):
        pass
    return ''


# Слова с заглавной или латиницей, которые именем компании не являются.
_NOT_A_NAME = re.compile(r'\b(?:IT|ИТ|IPO|SPO|M&A|ГК|РФ|СНГ|B2B|B2C|FMCG|HoReCa|DIY|Росси[ияюей]|Москв[аеыу]'
                         r'|Европ[аеыу]|Ази[ияю]|Китa[яе]|Китае?|Казахстан\w*|США)\b')


def is_nameless(title):
    """Плитка без названия компании: «Продажа крупного производителя яблок
    стратегическому инвестору». Имя — это кавычки, латиница или слово с
    заглавной буквы не в начале заголовка."""
    text = _NOT_A_NAME.sub(' ', str(title or ''))
    text = re.sub(r'^\W*\w+', ' ', text, count=1)          # первое слово всегда с заглавной
    return not re.search(r'[«"“]\w|[A-Za-z]{2}|(?<![\w-])[А-ЯЁ][а-яёА-ЯЁ]', text)


def role_phrase(firm, role, legal=False):
    """Шапка записи: «Advance Capital выступил финансовым консультантом
    продавцов» — в том виде, в каком ее узнает `advisors.lead_advisor`.
    Русское имя из нескольких слов берется в кавычки, иначе правило разрежет
    «Николаев и партнеры» на две фирмы."""
    name = '«%s»' % firm if re.search(r'[а-яё]', firm) and ' ' in firm else firm
    role = clean(role)
    m = _FIN_ROLE.match(role)
    if m:
        noun = 'консультантом' if m.group(1).lower() == 'консультант' else 'советником'
        return ('%s выступил финансовым %s %s' % (name, noun, m.group(2).strip())).strip()
    if legal:
        return '%s выступил юридическим консультантом в сделке' % name
    return '%s выступил финансовым консультантом в сделке%s' % (name, (' (%s)' % role) if role else '')


def _names_firm(text, firm):
    """Текст — объявление самой фирмы: правило притока читает из его начала
    ровно ее имя (а не «Объединенная команда юристов АБ …»)."""
    lead = advisors.lead_advisor(text)
    return bool(lead and [f.lower() for f in lead[0]] == [firm.lower()])


def title_key(title):
    return 't:' + re.sub(r'[^0-9a-zа-я]+', '', str(title or '').lower().replace('ё', 'е'))[:80]


def _first(rx, block):
    if not rx:
        return ''
    m = re.search(rx, block, re.S | re.I)
    return m.group(1) if m else ''


def parse(body, src_id, today=None):
    """Страница -> список записей сырья. Только разбор и отсев по смыслу
    (обезличено, не M&A, не объявление о сделке, старше SINCE); память о
    виденном — отдельно, в `fresh()`."""
    rule = PAGES[src_id]
    text = body.decode('utf-8', 'ignore') if isinstance(body, bytes) else str(body)
    text = re.sub(r'<script\b.*?</script>|<style\b.*?</style>|<svg\b.*?</svg>', ' ', text, flags=re.S | re.I)
    firm, page, kind = rule['firm'], rule['page'], rule.get('kind', 'news')
    out, seen = [], set()
    for block in re.split('(?=%s)' % rule['block'], text, flags=re.S)[1:]:
        title = clean(_first(rule.get('title'), block))
        if len(title) < 8:
            continue
        prefix = clean(_first(rule.get('prefix'), block))      # имя клиента над описанием проекта
        if prefix and prefix.lower() not in title.lower():
            title = '%s: %s' % (prefix, title)
        body_text = clean(_first(rule.get('text'), block))
        role = clean(_first(rule.get('role'), block))
        day = find_date(_first(rule['date'], block) if rule.get('date') else block, today)
        if day and int(day[:4]) < SINCE:
            continue
        blob = '%s %s' % (title, body_text)
        if kind == 'tombstone':
            if is_nameless(title) or NOT_MNA.search(blob):
                continue
        elif kind == 'project':
            if is_nameless(title) or not NEED_DEAL.search(title) or SKIP_NEWS.search(title) or NOT_MNA.search(blob):
                continue
        else:
            if not (NEED_ADVISED.search(blob) and NEED_DEAL.search(title)) or SKIP_NEWS.search(title) \
                    or NOT_MNA.search(blob):
                continue
        link = _first(rule.get('link'), block)
        if link:
            url = urljoin(page, html.unescape(link).strip())
        else:
            url = '%s#deal-%s' % (page, hashlib.sha1(title_key(title).encode('utf-8')).hexdigest()[:8])
        if url in seen:
            continue
        seen.add(url)
        # Шапка «<Фирма> выступил …» нужна, когда сам текст объявлением фирмы
        # не является: по ней `advisors.lead_advisor` узнает консультанта —
        # тем же правилом, что у постов @LawFirms.
        own = '%s. %s' % (title, body_text) if body_text else title
        summary = next((t for t in (own, body_text) if t and _names_firm(t, firm)), None)
        if summary is None:
            summary = '%s. Сделка: %s' % (role_phrase(firm, role, legal=kind != 'tombstone'), own)
        out.append({'source_id': src_id, 'source_name': label_of(src_id), 'url': url, 'title': title[:300],
                    'summary': re.sub(r'\s+', ' ', summary).strip(' .')[:900], 'published': day,
                    'advisor': firm, 'advisor_role': role})
    return out


# ---------- память о виденном ----------

def load_seen(path=None):
    try:
        return json.load(open(path or SEEN, encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save_seen(seen, path=None):
    out = {k: {'seeded': v.get('seeded'), 'keys': sorted(set(v.get('keys') or []))}
           for k, v in sorted(seen.items())}
    with open(path or SEEN, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write('\n')


def keys_of(item):
    return [item['url'], title_key(item['title'])]


def fresh(src_id, items, seen, day=None):
    """Записи, которых этот источник еще не отдавал; память дополняется.

    Источника в памяти нет — это первое включение: все, что на странице уже
    есть, помечается виденным и НЕ отдается (засев). Запись узнается по
    адресу ИЛИ по заголовку: фирма дописала к старой плитке ссылку на
    пресс-релиз — адрес новый, сделка та же."""
    day = day or datetime.now(timezone.utc).strftime('%Y-%m-%d')
    if src_id not in seen:
        if items:               # пустая страница памятью не становится: это сбой разбора
            seen[src_id] = {'seeded': day, 'keys': sorted({k for it in items for k in keys_of(it)})}
        return []
    known = set(seen[src_id].get('keys') or [])
    new = [it for it in items if not (set(keys_of(it)) & known)]
    for it in new:
        known.update(keys_of(it))
    seen[src_id]['keys'] = sorted(known)
    # Давняя сделка, всплывшая на странице только сейчас (фирма убрала свежую
    # запись, и на первую страницу ленты вернулась старая; дописала плитку за
    # прошлые годы), запоминается, но в очередь не идет.
    return [it for it in new if not it.get('published') or _age_days(it['published'], day) <= MAX_AGE_DAYS]


def _age_days(published, day):
    try:
        return (date.fromisoformat(day[:10]) - date.fromisoformat(published[:10])).days
    except ValueError:
        return 0


# ---------- сухой прогон и сверка с базой ----------

def match_base(items, data=None):
    """[(запись, id карточки или None, причина)] — та же сверка, что в
    `triage.py`: по ней видно, что уйдет в дополнение карточек, а что в
    черновики."""
    sys.path.insert(0, HERE)
    import draft
    import match as matcher
    import triage
    data = data or json.load(open(os.path.join(ROOT, 'static', 'data', 'deals_promoted.json'), encoding='utf-8'))
    idx = matcher.index_base(data['deals'], data.get('companies'), data.get('match_keys'))
    out = []
    for it in items:
        if not triage.is_deal(it):
            out.append((it, None, 'фильтр: не сделка'))
            continue
        buyer, asset, seller, _ = draft.guess_parties(it['title'])
        deal_id, why = matcher.match({'title': it['title'], 'summary': it.get('summary'), 'url': it['url'],
                                      'buyer': buyer, 'asset': asset, 'seller': seller,
                                      'advisor': it.get('advisor'),
                                      'date': it.get('published') or date.today().isoformat()}, idx)
        if deal_id and not matcher.is_strong(why):
            why = 'похоже, читать: ' + why
        out.append((it, deal_id, why or 'карточки нет'))
    return out


def main(argv):
    def opt(name):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else None
    only, path = opt('--only'), opt('--file')
    seen = load_seen()
    changed = False
    for src_id, rule in PAGES.items():
        if only and src_id != only:
            continue
        try:
            body = open(path, 'rb').read() if path else http_get(rule['page'])
        except Exception as e:                                  # noqa: BLE001
            print('%-20s НЕ ОТКРЫЛАСЬ: %s: %s' % (src_id, type(e).__name__, str(e)[:80]))
            continue
        items = parse(body, src_id)
        if '--seed' in argv:
            seen.pop(src_id, None)
        memory = json.loads(json.dumps(seen))
        new = fresh(src_id, items, memory)
        seeded = src_id not in seen
        print('%-20s %s: записей с %d года %d, %s' % (
            src_id, rule['page'], SINCE, len(items),
            'первое включение — все помечается виденным' if seeded else 'новых %d' % len(new)))
        rows = match_base(items) if '--match' in argv else [(it, None, '') for it in items]
        for it, deal_id, why in rows:
            mark = '+' if it in new else ' '
            print('  %s %-10s %s%s' % (mark, it['published'] or '—', it['title'][:95],
                                       ('  → %s (%s)' % (deal_id or 'нет', why)) if why else ''))
        if '--seed' in argv and items:
            seen = memory
            changed = True
    if changed and '--write' in argv:
        save_seen(seen)
        print('Память записана: %s' % os.path.relpath(SEEN, ROOT))
    elif '--seed' in argv:
        print('Сухой прогон. Запись памяти — с ключом --write.')


if __name__ == '__main__':
    main(sys.argv[1:])
