# -*- coding: utf-8 -*-
"""Признаки будущих сделок: компания сама заявила о планах, но сделки ещё нет.

ЗАЧЕМ. Партнёр владельца и практика M&A (19 октября 2026): полезно видеть,
у каких компаний вероятна сделка, — НЕ процентом, а доводами с датой и
ссылкой: «продаём агроактивы», «выходим из непрофильного», «ищем
инвестора», «готовимся к IPO», «рассматриваем покупку», актив выставлен на
торги. Фильтр притока (`classify.py`) такие новости отбрасывает — это не
сделка, и в карточку их превращать нельзя. Здесь они не теряются, а
ложатся отдельным файлом `static/data/signals.json`, привязанные к профилю
компании.

ТРИ ИСТОЧНИКА ЗАПИСЕЙ (поле `origin`):
  * `news` — новость притока, которую фильтр не пустил как сделку
    (`data/inbox/triage/<день>.json`, вердикт `not_a_deal`), или черновик,
    придержанный воротами (`data/inbox/hold/<день>.json`). Признак ищется
    в ЗАГОЛОВКЕ, как и признак сделки (`classify.looks_like_deal`):
    обзоры упоминают чужие планы мимоходом.
  * `card` — карточка базы в статусе «Обсуждается» не старше двух лет:
    стороны обсуждаемой сделки — тот же довод, уже прочитанный. Эти записи
    собираются заново при каждом `--write` (статус сменился — записи нет).
  * `card_text` — прочитанное заявление компании о планах из текста
    карточки (`eco.context`, `extra`): список `CARD_STATEMENTS` ниже,
    каждое — с датой заявления и источником карточки. Механически из прозы
    не вынимается: 102 совпадения «планирует / рассматривает / стратегия» в
    текстах карточек — почти всё стратегические цели уже закрытых сделок и
    прошлые планы; в список взято только то, что прочитано и верно.

ТОЧНОСТЬ ВАЖНЕЕ ПОЛНОТЫ. Запись без профиля компании не сохраняется —
«Тайвань намерен купить ракеты» или «житель регионов рассматривает покупку
жилья» профиля не найдут. Имя ищется теми же ключами, что привязка сторон
(`link_parties.company_key` / `build_index`: только имена профилей, без
псевдонимов `match_keys`, омоним — нет привязки), плюс падежное окончание
(«активы «Лукойла»»). Недвижимость, вещи, госорганы-продавцы и отрицания
(«не планирует IPO») отсекаются. Новость, чей адрес уже стоит источником
карточки, — сделка, а не признак: её покажет карточка.

ПЕРЕСКАЗ, А НЕ ЦИТАТА. `summary` собирается шаблоном из вида признака и
имён профилей («ВТБ — возможная продажа: «Росгосстрах»»), а не из текста
заголовка — правило дословности (`docs/sources_legal.md`).

Запуск:
    python3 pipeline/ingest/signals.py              # что добавится (сухой прогон)
    python3 pipeline/ingest/signals.py --write      # записать signals.json
    python3 pipeline/ingest/signals.py --all        # разобрать всё сырьё и все hold-файлы
    python3 pipeline/ingest/signals.py --measure    # замер на заголовках базы и разметке
"""
import glob
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import classify                                     # noqa: E402
import link_parties                                 # noqa: E402

sys.path.insert(0, os.path.dirname(HERE))           # pipeline/source_names.py
import source_names                                 # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OUT = os.path.join(ROOT, 'static', 'data', 'signals.json')
TRIAGE = os.path.join(ROOT, 'data', 'inbox', 'triage')
HOLD = os.path.join(ROOT, 'data', 'inbox', 'hold')
LABELS = os.path.join(HERE, 'signal_labels.json')

# Вид признака -> подпись для человека (сайт, ассистент, подборка).
KINDS = {
    'sell': 'готовит продажу',
    'for_sale': 'компанию или долю продают',
    'buy': 'присматривает покупки',
    'investor': 'ищет инвестора или партнёра',
    'ipo': 'готовится к размещению акций',
    'exit': 'выходит из бизнеса или рынка',
    'strategy': 'заявила рост через покупки',
    'state_sale': 'государство готовит продажу',
}
# «Сильный» признак: сама компания (или государство-владелец) заявила о
# продаже, выходе или размещении, либо актив выставлен на торги. Одного
# такого хватает, чтобы компания попала в еженедельную подборку.
STRONG_KINDS = {'sell', 'for_sale', 'ipo', 'exit', 'state_sale'}
# Карточки «Обсуждается» старше этого — не признак, а старая история.
CARD_WINDOW_DAYS = 730

# --- признаки намерения в заголовке ----------------------------------------
_W = r'[а-яёa-z]'
_INTENT = r'(?:рассматрива\w+|изуча\w+|обсужда\w+|прорабатыва\w+|оценива\w+\s+возможност\w+)'
_WANT = (r'(?:намерен\w*|намерева\w+|планиру\w+|собира\w+|хоч\w+|хотят|готов(?:а|ы|ит|ят|ится|ятся)?'
         r'|решил\w*|задумал\w*|может|могут|не\s+исключа\w+)')
SELL_RX = re.compile(
    _INTENT + r'\s+(?:возможност\w+\s+)?(?:\w+\s+(?:или|и)\s+)?(?:продаж\w+|продать)'
    r'|' + _WANT + r'\s+(?:\w+\s+){0,2}?(?:продать|продавать|избавиться\s+от|реализовать\s+(?:долю|пакет|акци))'
    r'|ищ(?:ет|ут|ем)\s+покупател\w+|подыскива\w+\s+покупател\w+|поиск\w*\s+покупател\w+'
    r'|готов(?:ит|ят|ится|ятся)\s+к\s+продаже|выставля\w+\s+на\s+продажу|выставил\w*\s+на\s+продажу'
    r'|выставлен\w*\s+на\s+продажу|выставит\w*\s+на\s+продажу|может\s+быть\s+продан\w*', re.I)
BUY_RX = re.compile(
    _INTENT + r'\s+(?:возможност\w+\s+)?(?:\w+\s+(?:или|и)\s+)?(?:покупк\w+|приобретени\w+|поглощени\w+|выкуп\w*)'
    r'|' + _WANT + r'\s+(?:\w+\s+){0,2}?(?:купить|приобрести|выкупить|поглотить)'
    r'|интересу\w+\s+(?:покупк\w+|приобретени\w+)|заинтересова\w+\s+в\s+(?:покупк\w+|приобретени\w+)'
    r'|ищ(?:ет|ут)\s+(?:активы|цели|объекты|компании)\s+(?:для\s+)?(?:покупк|приобрет|поглощ)'
    r'|присматрива\w+\s+(?:актив|компани|бизнес)', re.I)
INVESTOR_RX = re.compile(
    r'ищ(?:ет|ут)\s+(?:\w+\s+){0,2}(?:инвестор\w*|партн[её]р\w*|соинвестор\w*|акционер\w*)'
    r'|поиск\w*\s+(?:\w+\s+){0,2}(?:инвестор\w*|партн[её]р\w*)'
    r'|' + _WANT + r'\s+(?:\w+\s+){0,2}?привлеч\w*\s+(?:\w+\s+){0,2}(?:инвестор\w*|партн[её]р\w*|акционер\w*)'
    r'|' + _INTENT + r'\s+(?:возможност\w+\s+)?(?:привлечени\w+\s+)?(?:\w+\s+){0,2}(?:инвестор\w*|партн[её]р\w*)', re.I)
IPO_RX = re.compile(
    r'(?:' + _WANT + r'|' + _INTENT + r'|готов\w+\s+к|подготовк\w+\s+к|подготавлива\w+\s+к|назвал\w*\s+(?:\d{4}\s+)?(?:год\s+)?срок\w*)'
    r'[^.;]{0,40}?(?:\bipo\b|\bspo\b|pre-?ipo|размещени\w+\s+акци\w+|выход\w*\s+на\s+бирж\w+|выйти\s+на\s+бирж\w+)', re.I)
EXIT_RX = re.compile(
    r'(?:выход\w*|выйти|уход\w*|уйти|избав\w+)\s+(?:из\s+|от\s+)?непрофильн\w+'
    r'|непрофильн\w+\s+актив\w*[^.;]{0,30}(?:прода|избав|выстав)'
    r'|' + _INTENT + r'\s+(?:возможност\w+\s+)?(?:полного\s+)?(?:уход\w*|выход\w*)\s+(?:из|с)\s+(?:росси|рф|российск)'
    r'|' + _WANT + r'\s+(?:\w+\s+)?(?:уйти|выйти)\s+(?:из|с)\s+(?:росси|рф|российск)', re.I)
STRATEGY_RX = re.compile(
    r'стратеги\w+[^.;]{0,50}(?:\bm&a\b|слияни\w+|поглощени\w+|покупк\w+|приобретени\w+)'
    r'|рост\w*\s+(?:за\s+сч[её]т|через)\s+(?:покупк\w+|приобретени\w+|m&a|сделк\w+\s+m&a)'
    r'|(?:развива\w+|расширя\w+)\s+[^.;]{0,40}(?:через|за\s+сч[её]т)\s+(?:покупк\w+|приобретени\w+|m&a)'
    r'|\bm&a-стратеги\w+', re.I)
STATE_RX = re.compile(
    r'приватизац\w+|план\w*\s+приватизаци\w+|продаж\w+\s+госпакет\w*|госпакет\w*\s+[^.;]{0,30}прода', re.I)
# Порядок важен: первый подошедший вид и есть вид признака.
DETECTORS = (('exit', EXIT_RX), ('ipo', IPO_RX), ('state_sale', STATE_RX), ('investor', INVESTOR_RX),
             ('sell', SELL_RX), ('buy', BUY_RX), ('strategy', STRATEGY_RX))

# «Не планирует IPO», «опроверг продажу» — признака нет. «Не исключает» —
# есть (ловится в _WANT выше и не считается отрицанием).
NEGATION = re.compile(
    r'\bне\s+(?:планиру\w+|намерен\w*|рассматрива\w+|собира\w+|видит\s+перспектив\w*|будет|хочет|готов\w*'
    r'|вед[её]т|ведут|станет|продаст|купит)|опроверг\w*|отказал\w*(?:ся|ась|ись)?\s+от|отрица\w+|нет\s+планов', re.I)
# Не бизнес: жильё, здания, вещи, оружие, частные покупки. Продажу ЗДАНИЯ
# компанией признаком её будущей сделки не считаем — это хозяйственная
# операция, а не смена владельца бизнеса (так же решено для лотов Дом.РФ).
NOT_A_BUSINESS = re.compile(
    r'квартир\w*|особняк\w*|усадьб\w*|помещени\w*|земельн\w*|участ(?:ок|ка|ки|ков)\b|гектар\w*|здани\w*'
    r'|\bдом(?:а|ом)?\b|дач\w*|гардероб\w*|вещ(?:и|ей)\b|картин\w*|автомобил\w*|rolls|ракет\w*|оружи\w*'
    r'|бил[её]т\w*|жиль\w*|недостро\w*|торгов\w+\s+центр\w*|\bтц\b|\bтрк\b|офис\w*|вокзал\w*|палат(?:ы|ах)\b'
    r'|ипотек\w*|товар\w*|валют\w*|облигаци\w*|акци\w+\s+(?:сбер|газпром)\w*\s+(?:выросл|упал)'
    r'|бизнес-парк\w*|бизнес-центр\w*|\bбц\b|торгово-развлекательн\w*|\bтрц\b|склад\w*|жил\w+\s+комплекс\w*|\bжк\b'
    r'|гостиниц\w*|(?<![а-яё])отел(?:ь|я|ем|и|ей)\b|комплекс\w*\s+здани\w*|недвижимост\w*', re.I)
# Подлежащее — государство, ведомство или город: это не компания, у которой
# готовится сделка (их продажи — лоты, карточки «Продажа с торгов»).
STATE_ACTOR = re.compile(
    r'^(?:россия|российская\s+федерация|правительств\w*|росимуществ\w*|минфин\w*|минэк\w*|мэри\w*|москва'
    r'|власти\b|ао\s+«?дом\.рф|дом\.рф|ппк\s+«?фонд\s+развития|фонд\s+развития\s+территорий|банк\s+россии'
    r'|центральный\s+банк|цб\b|фас\b|росреестр|росимущество)', re.I)

_QUOTED = re.compile(r'«([^«»]{2,60}(?:«[^«»]{1,40}»[^«»]{0,20})?)»|"([^"]{2,60})"')
# Латинский бренд (Shein, OpenAI, X5 Group) или заглавное русское слово.
_CAP = re.compile(r'(?<![\w«"])((?:[A-ZА-ЯЁ][\w&.+-]*|[A-Z0-9]{2,})(?:\s+(?:[A-ZА-ЯЁ][\w&.+-]*|Group|Capital|Holding))*)')
_CASE_ENDINGS = ('ами', 'ями', 'ого', 'его', 'ому', 'ему', 'ой', 'ей', 'ом', 'ем', 'ам', 'ям', 'ах', 'ях',
                 'а', 'я', 'у', 'ю', 'е', 'ы', 'и')
# Слова, которые пишутся с заглавной в начале заголовка или как источник, но
# компанией не являются.
NOT_NAMES = {'смИ'.lower(), 'сми', 'ft', 'bloomberg', 'reuters', 'рбк', 'forbes', 'cnbc', 'cnn', 'wsj', 'интерфакс',
             'тасс', 'риа', 'коммерсантъ', 'ведомости', 'известия', 'российская', 'российский', 'россия',
             'китайская', 'китайский', 'американский', 'американская', 'крупный', 'крупная', 'компания',
             'группа', 'холдинг', 'банк', 'минфин', 'москва', 'власти', 'основатель', 'совладелец',
             'акционеры', 'инвестор', 'инвесторы', 'источники', 'глава', 'гендиректор', 'сша', 'ес'}


def detect(title):
    """(вид, совпавший фрагмент) или None — признак будущей сделки в заголовке.

    Отказ — по самому заголовку: отрицание, не-бизнес и чужие классы шума
    фильтра сделок (котировки, отчётность, суды, назначения)."""
    t = ' '.join(str(title or '').split())
    if not t:
        return None
    if NEGATION.search(t) or NOT_A_BUSINESS.search(t) or classify.NEGATIVE.search(t):
        return None
    for kind, rx in DETECTORS:
        m = rx.search(t)
        if m:
            return kind, m
    return None


class Profiles:
    """Поиск профиля по имени — ключом привязки сторон (`link_parties`).

    Сначала имя профиля (как `link_parties.build_index`), затем — запасным
    путём — псевдоним из `match_keys` («Сбер», «Лента», «МТС» — у профилей
    имена «Сбербанк», «Группа Лента», «ПАО «МТС»»). Ловушка, из-за которой
    привязка сторон псевдонимы не берёт (голое имя матери у профиля «Knauf
    (российский бизнес)»), здесь закрыта тем же правилом: профиль с пометкой
    российской части по псевдониму не находится. Псевдоним, ведущий в два
    профиля, не годится."""

    def __init__(self, companies, match_keys=None):
        self.companies = companies or {}
        self.index = link_parties.build_index(self.companies)
        self.alias = {}
        for cid, aliases in (match_keys or {}).items():
            name = (self.companies.get(cid) or {}).get('name') or ''
            if not name or link_parties.SUBSIDIARY_MARK.search(name):
                continue
            for a in aliases or []:
                k = link_parties.company_key(a)
                # Короткий псевдоним («мир», «мтс») — обычное слово заголовка:
                # «система «Мир»» уходила в профиль «МИР» (медицинские решения).
                if len(k) >= 4:
                    self.alias.setdefault(k, set()).add(cid)

    def ok(self, cid):
        c = self.companies.get(cid) or {}
        return bool(c) and not c.get('asset') and not c.get('lot')

    def find(self, name):
        name = str(name or '').strip(' «»"\'.,:;—-')
        if len(name) < 2 or name.lower() in NOT_NAMES:
            return None
        variants = [name]
        last = name.split()[-1] if name.split() else name
        if re.search(r'[а-яё]$', last, re.I):
            for end in _CASE_ENDINGS:
                if last.lower().endswith(end) and len(last) - len(end) >= 3:
                    variants.append(name[: len(name) - len(end)])
        for table in (self.index, self.alias):
            for v in variants:
                found = table.get(link_parties.company_key(v))
                if found and len(found) == 1:
                    cid = next(iter(found))
                    if self.ok(cid):
                        return cid
        return None

    def name(self, cid):
        return (self.companies.get(cid) or {}).get('name') or ''


def _candidates(text):
    """Имена в куске заголовка: сначала в кавычках, потом заглавные слова."""
    out = []
    for m in _QUOTED.finditer(text):
        out.append(m.group(1) or m.group(2))
    plain = _QUOTED.sub(' ', text)
    for m in _CAP.finditer(plain):
        out.append(m.group(1))
        words = m.group(1).split()
        if len(words) > 1:
            out.extend(words)
    return out


def _strip_attribution(title):
    """«FT: …», «СМИ: …», «Bloomberg узнал, что …» — источник, не подлежащее."""
    t = re.sub(r'^\s*[\w .&-]{1,25}:\s+', '', title)
    t = re.sub(r'^(?:СМИ|Источники)\s+(?:узнали|сообщили)[^,]{0,30},?\s*(?:что\s+)?', '', t)
    return t


def parties(title, match, profiles):
    """([кто заявил, …], о ком речь) — id профилей до и после признака.

    Подлежащих бывает несколько («RWB, Ozon, МТС и «Яндекс» интересуются
    покупкой доли в НСПК») — признак получает каждое."""
    t = _strip_attribution(title)
    m = match.re.search(t) or match
    before, after = t[: m.start()], t[m.end():]
    actors = []
    if not STATE_ACTOR.search(before.strip(' «"')):
        for name in _candidates(before):
            cid = profiles.find(name)
            if cid and cid not in actors:
                actors.append(cid)
    obj = None
    for name in _candidates(after):
        cid = profiles.find(name)
        if cid and cid not in actors:
            obj = cid
            break
    return actors, obj


def summary_for(kind, actor_name, obj_name='', extra=''):
    """Пересказ одной фразой — шаблоном, без слов источника."""
    who = actor_name
    if kind == 'sell':
        s = '%s — возможная продажа: %s' % (who, obj_name) if obj_name else '%s — готовит продажу части бизнеса' % who
    elif kind == 'for_sale':
        s = '%s — компанию или долю в ней готовят к продаже' % who
    elif kind == 'buy':
        s = '%s — возможная покупка: %s' % (who, obj_name) if obj_name else '%s — присматривает новые покупки' % who
    elif kind == 'investor':
        s = '%s — ищет инвестора или партнёра' % who
    elif kind == 'ipo':
        s = '%s — готовится к размещению акций' % who
    elif kind == 'exit':
        s = '%s — планирует выйти из части бизнеса' % who
    elif kind == 'strategy':
        s = '%s — заявила рост через покупки' % who
    elif kind == 'state_sale':
        s = '%s — государство готовит продажу пакета' % who
    else:
        s = who
    return s + (('; ' + extra) if extra else '')


def _sid(*parts):
    return 's' + hashlib.sha1('|'.join(str(p) for p in parts).encode('utf-8')).hexdigest()[:9]


def _source_name(src, url):
    name = str(src or '')
    if name.startswith('web:') or not name:
        host = re.sub(r'^https?://(?:www\.)?', '', str(url or '')).split('/')[0]
        name = host or name
    return name


def _superseded(company, kind, day, data_cards):
    """Признак уже стал сделкой: у компании есть карточка в той же роли, не
    раньше даты признака («Росатом планирует выкупить «Дело»» в августе —
    карточка закрытия в октябре). Такую новость показывает карточка."""
    roles = {'buy': ('buyer',), 'sell': ('seller_id',), 'exit': ('seller_id',),
             'for_sale': ('target', 'asset_id'), 'ipo': ('target',), 'investor': ('target', 'asset_id'),
             'state_sale': ('target', 'asset_id'), 'strategy': ('buyer',)}.get(kind, ())
    for card in data_cards:
        if any(card.get(r) == company for r in roles) and str(card.get('date') or '') >= day:
            return True
    return False


def from_item(title, url, day, source_name, profiles, known_urls, cards=()):
    """Признаки из одной новости притока — список (пустой, если признака нет)."""
    if not url or url in known_urls:
        return []
    # Агрегатор — способ узнать, а не источник факта (docs/sources_legal.md,
    # правило 2): признак со ссылкой на mergers.ru или @dealsma не пишем —
    # та же новость приходит и от первоисточника.
    if source_names.is_aggregator(url):
        return []
    hit = detect(title)
    if not hit:
        return []
    kind, m = hit
    actors, obj = parties(title, m, profiles)
    rows = []
    if kind == 'state_sale':
        target = obj or (actors[0] if actors else None)
        if target:
            rows.append((target, kind, None))
    elif actors:
        rows.extend((a, kind, obj) for a in actors)
    elif obj and kind in ('sell', 'exit'):
        # «Семейный бизнес X готовят к продаже» — подлежащего-компании нет,
        # продают саму компанию.
        rows.append((obj, 'for_sale', None))
    elif obj and kind == 'buy':
        # «Американский инвестор планирует выкупить активы «Лукойла»» —
        # покупатель без профиля, признак — у того, чьи активы покупают.
        rows.append((obj, 'interest', None))
    out = []
    for company, k, other in rows:
        name = profiles.name(company)
        if k == 'interest':
            k, text = 'for_sale', '%s — к активам компании присматриваются покупатели' % name
        elif k == 'exit' and re.search(r'росси|\bрф\b', title, re.I):
            text = '%s — рассматривает уход из России' % name
        else:
            text = summary_for(k, name, profiles.name(other) if other else '')
        if _superseded(company, k, day, cards):
            continue
        rec = {'id': _sid('news', url, company, k), 'company_id': company, 'date': day, 'kind': k,
               'summary': text, 'source': [source_name, url], 'origin': 'news',
               'strength': 'strong' if k in STRONG_KINDS else 'normal'}
        if other:
            rec['object_id'] = other
        out.append(rec)
    return out


# --- карточки базы -----------------------------------------------------------
def _short_asset(card, companies):
    tid = card.get('target') or card.get('asset_id')
    if tid and tid in companies:
        return companies[tid].get('name') or ''
    asset = str(card.get('asset') or '').strip()
    if asset and len(asset) <= 70 and not re.search(r'[.;]', asset):
        return asset
    return ''


# Блоги и форумы частных инвесторов — не источник для читателя, если у
# карточки есть издание.
WEAK_HOSTS = ('smart-lab.ru', 't.me', 'vc.ru', 'pikabu.ru', 'dzen.ru')


def _card_source(card):
    """Первый источник карточки, который годится читателю: не агрегатор и не
    блог, если такой есть; иначе — первый как есть."""
    src = [s for s in card.get('src') or [] if isinstance(s, (list, tuple)) and len(s) >= 2 and s[1]]
    if not src:
        return None
    good = [s for s in src if not source_names.is_aggregator(s[1])
            and not any(h in str(s[1]) for h in WEAK_HOSTS)]
    best = (good or src)[0]
    return [str(best[0]), str(best[1])]


def from_cards(data, today=None):
    """Стороны обсуждаемых сделок — признаки с источником карточки."""
    today = today or date.today()
    since = (today - timedelta(days=CARD_WINDOW_DAYS)).isoformat()
    companies = data.get('companies') or {}
    ok = lambda cid: bool(cid) and cid in companies and not companies[cid].get('asset') \
        and not companies[cid].get('lot') and not STATE_ACTOR.search(companies[cid].get('name') or '')
    out = []
    for card in data.get('deals') or []:
        if card.get('status') != 'Обсуждается':
            continue
        day = str(card.get('date') or '')
        if not re.match(r'\d{4}-\d{2}', day) or day < since:
            continue
        src = _card_source(card)
        if not src:
            continue
        # Продажа здания, участка или офиса — хозяйственная операция, а не
        # будущая смена владельца бизнеса: «ГК ПИК — участок 5,3 га» не довод
        # о сделках компании. Тот же отсев, что у новостей.
        if NOT_A_BUSINESS.search(' '.join(str(card.get(k) or '') for k in ('title', 'asset'))):
            continue
        typ = card.get('type') or ''
        buyer, seller = card.get('buyer'), card.get('seller_id')
        target = card.get('target') or card.get('asset_id')
        asset = _short_asset(card, companies)
        rows = []
        if typ == 'IPO':
            if ok(target):
                rows.append((target, 'ipo', '%s — обсуждается размещение акций' % companies[target]['name']))
        elif typ == 'Продажа с торгов':
            if ok(target):
                extra = ('; продавец — %s' % companies[seller]['name']) if seller in companies else ''
                rows.append((target, 'for_sale', '%s — выставлена на торги%s' % (companies[target]['name'], extra)))
        elif typ == 'Создание СП':
            for a, b in ((buyer, target), (target, buyer)):
                if ok(a):
                    other = (' с %s' % companies[b]['name']) if b in companies else ''
                    rows.append((a, 'investor', '%s — обсуждается совместное предприятие%s' % (companies[a]['name'], other)))
        elif typ == 'Временное управление':
            continue
        else:
            invest = typ == 'Инвестиция'
            # Предмет не назван коротко — строка называет саму сделку (наш
            # заголовок карточки), иначе «ВТБ — обсуждается продажа» ни о чём.
            deal_title = ' '.join(str(card.get('title') or '').split())
            if ok(buyer):
                what = ('вложение в %s' % asset) if (invest and asset) else (('покупка: %s' % asset) if asset else '')
                rows.append((buyer, 'buy', ('%s — обсуждается %s' % (companies[buyer]['name'], what)) if what
                             else '%s — обсуждается сделка «%s»' % (companies[buyer]['name'], deal_title)))
            if ok(seller):
                rows.append((seller, 'sell', ('%s — обсуждается продажа: %s' % (companies[seller]['name'], asset))
                             if asset else '%s — обсуждается сделка «%s»' % (companies[seller]['name'], deal_title)))
            if ok(target):
                if invest:
                    text = '%s — обсуждается вход инвестора в капитал' % companies[target]['name']
                    kind = 'investor'
                else:
                    text = '%s — обсуждается продажа компании или доли' % companies[target]['name']
                    kind = 'for_sale'
                if buyer in companies:
                    text += '; возможный покупатель — %s' % companies[buyer]['name']
                rows.append((target, kind, text))
        seen = set()
        for cid, kind, text in rows:
            if cid in seen:
                continue
            seen.add(cid)
            out.append({'id': _sid('card', card['id'], cid, kind), 'company_id': cid, 'date': day[:10],
                        'kind': kind, 'summary': text, 'source': src, 'origin': 'card',
                        'deal_id': card['id'], 'strength': 'strong' if kind in STRONG_KINDS else 'normal'})
    return out


# Заявления о планах из текста карточек — прочитаны 19 октября 2026, каждое
# сверено с прозой карточки (`eco.context` / `extra`). Дата — день, когда
# заявление прозвучало (если текст его называет), иначе дата карточки.
# Пересказ — своими словами. Чтобы добавить: прочитать карточку, убедиться,
# что компания заявила о БУДУЩЕМ шаге и он ещё не случился, вписать строку.
CARD_STATEMENTS = (
    # «компания рассматривает покупку ещё нескольких активов в Московском регионе»
    {'deal_id': 'gf5c8e14e', 'role': 'buyer', 'kind': 'buy', 'date': None,
     'summary': '{name} — собирается купить ещё несколько активов связи в Московском регионе '
                '(заявление «Ситителекома», куда сводятся купленные операторы)'},
    # «Just AI планирует pre-IPO в 2026 году»
    {'deal_id': 'g14fd5ba9', 'role': 'target', 'kind': 'ipo', 'date': None,
     'summary': '{name} — готовит предварительное размещение акций (pre-IPO) в 2026 году'},
    # «в июне 2026 года акционеры одобрили преобразование в ПАО и подтвердили
    # намерение провести IPO до конца 2027 года»
    {'deal_id': 'gaa7602e7', 'role': 'target', 'kind': 'ipo', 'date': '2026-06',
     'summary': '{name} — акционеры подтвердили план выйти на биржу до конца 2027 года'},
    # «в перспективе ROBO рассматривает IPO как инструмент привлечения капитала»
    {'deal_id': 'g676504a3', 'role': 'target', 'kind': 'ipo', 'date': None,
     'summary': '{name} — в перспективе рассматривает выход на биржу'},
    # «продавать активы не планирует, но не исключает привлечения партнёра»
    {'deal_id': 'g934ee51b', 'role': 'buyer', 'kind': 'investor', 'date': None,
     'summary': '{name} — не исключает привлечения партнёра (продавать активы не собирается)'},
    # «кластер «X.Технологии», через который «Ростелеком» ищет новые точки
    # роста за счёт инвестиций, сделок M&A и партнёрств»
    # Покупатель в карточке — фонд «КоммИТ Кэпитал», заявление — о самом
    # «Ростелекоме», поэтому профиль назван явно.
    {'deal_id': 'gadcc1f58', 'role': 'buyer', 'company_id': 'g00f14033', 'kind': 'strategy', 'date': None,
     'summary': '{name} — ищет рост через покупки и инвестиции в технологические компании'},
    # «В мае 2026 года гендиректор «Астры» подтвердил, что компания не
    # исключает привлечения крупного стратегического инвестора»
    {'deal_id': 'g9d9e7ab6', 'role': 'target', 'kind': 'investor', 'date': '2026-05',
     'summary': '{name} — руководство подтвердило, что готово привлечь крупного стратегического инвестора'},
)


def _role_id(card, role):
    if role == 'target':
        return card.get('target') or card.get('asset_id')
    if role == 'seller':
        return card.get('seller_id')
    return card.get('buyer')


def from_statements(data, statements=CARD_STATEMENTS):
    by_id = {c['id']: c for c in data.get('deals') or []}
    companies = data.get('companies') or {}
    out = []
    for st in statements:
        card = by_id.get(st['deal_id'])
        if not card:
            continue
        cid = st.get('company_id') or _role_id(card, st['role'])
        src = _card_source(card)
        if not cid or cid not in companies or not src:
            continue
        day = st.get('date') or str(card.get('date') or '')[:10]
        kind = st['kind']
        out.append({'id': _sid('text', card['id'], cid, kind), 'company_id': cid, 'date': day, 'kind': kind,
                    'summary': st['summary'].format(name=companies[cid]['name']), 'source': src,
                    'origin': 'card_text', 'deal_id': card['id'],
                    'strength': 'strong' if kind in STRONG_KINDS else 'normal'})
    return out


# --- сырьё притока -------------------------------------------------------------
def inbox_items(all_days=False, today=None):
    """(заголовок, адрес, день, источник) из разбора притока и hold-файлов."""
    day = (today or datetime.now(timezone.utc).date()).isoformat()
    items = []
    for path in sorted(glob.glob(os.path.join(TRIAGE, '*.json'))):
        if not all_days and not os.path.basename(path).startswith(day):
            continue
        try:
            rows = json.load(open(path, encoding='utf-8')).get('items') or []
        except (OSError, ValueError):
            continue
        for r in rows:
            if r.get('verdict') == 'not_a_deal':
                items.append((r.get('title'), r.get('url'), str(r.get('date') or day)[:10],
                              _source_name(r.get('source_id'), r.get('url'))))
    for path in sorted(glob.glob(os.path.join(HOLD, '*.json'))):
        name = os.path.basename(path)
        if name.endswith('-enrich.json') or (not all_days and not name.startswith(day)):
            continue
        try:
            drafts = json.load(open(path, encoding='utf-8')).get('drafts') or []
        except (OSError, ValueError):
            continue
        for d in drafts:
            src = (d.get('src') or [[None, None]])[0]
            url = src[1] if len(src) > 1 else None
            items.append((d.get('title'), url, str(d.get('date') or day)[:10], _source_name(src[0], url)))
    return items


def known_urls(data):
    urls = set()
    for card in data.get('deals') or []:
        for s in card.get('src') or []:
            if isinstance(s, (list, tuple)) and len(s) > 1:
                urls.add(s[1])
    urls.update(data.get('consumed_urls') or [])
    return urls


def build(data, items, existing=None, today=None):
    """Новый список признаков: прежние новости + новые новости + карточки заново."""
    profiles = Profiles(data.get('companies'), data.get('match_keys'))
    known = known_urls(data)
    keep = [s for s in (existing or []) if s.get('origin') == 'news'
            and s.get('company_id') in profiles.companies and (s.get('source') or [None, None])[1] not in known]
    seen = {s['id'] for s in keep}
    added = []
    cards = data.get('deals') or []
    for title, url, day, source_name in items:
        for rec in from_item(title, url, day, source_name, profiles, known, cards):
            if rec['id'] not in seen:
                seen.add(rec['id'])
                added.append(rec)
    rows = keep + added + from_cards(data, today) + from_statements(data)
    uniq, ids = [], set()
    for r in rows:
        if r['id'] in ids:
            continue
        ids.add(r['id'])
        uniq.append(r)
    uniq.sort(key=lambda s: (s.get('date') or '', s['id']), reverse=True)
    return uniq, added


def load_existing(path=OUT):
    try:
        return json.load(open(path, encoding='utf-8')).get('signals') or []
    except (OSError, ValueError):
        return []


def measure():
    data = json.load(open(DATA, encoding='utf-8'))
    titles = [(c.get('title') or '', c.get('status')) for c in data['deals']]
    closed = [t for t, s in titles if s == 'Закрыта']
    hits = [t for t in closed if detect(t)]
    print('Закрытые сделки базы, принятые за признак: %d из %d (%.1f%%)'
          % (len(hits), len(closed), 100.0 * len(hits) / max(1, len(closed))))
    for t in hits[:20]:
        print('   ', t[:110], '|', detect(t)[0])
    profiles = Profiles(data.get('companies'), data.get('match_keys'))
    try:
        labels = json.load(open(LABELS, encoding='utf-8'))
    except (OSError, ValueError):
        labels = {}
    tp = fp = fn = 0
    for title, want in labels.items():
        got = bool(from_item(title, 'measure://' + title, '2026-01-01', 'm', profiles, set()))
        if got and want:
            tp += 1
        elif got and not want:
            fp += 1
            print('   ложный признак:', title[:110])
        elif want and not got:
            fn += 1
    if labels:
        print('Разметка живого потока (%d заголовков): верных %d, ложных %d, пропущено %d'
              % (len(labels), tp, fp, fn))


def main(argv):
    if '--measure' in argv:
        measure()
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    items = inbox_items(all_days='--all' in argv)
    existing = load_existing()
    rows, added = build(data, items, existing)
    by_origin = {}
    for r in rows:
        by_origin[r['origin']] = by_origin.get(r['origin'], 0) + 1
    print('Новостей разобрано: %d | новых признаков из новостей: %d' % (len(items), len(added)))
    for r in added:
        print('  + %s %-9s %s | %s' % (r['date'], r['kind'], r['summary'][:90], r['source'][1][:60]))
    print('Всего признаков: %d (%s), компаний: %d' % (
        len(rows), ', '.join('%s %d' % kv for kv in sorted(by_origin.items())),
        len({r['company_id'] for r in rows})))
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    payload = {'updated': datetime.now(timezone.utc).date().isoformat(), 'signals': rows}
    tmp = OUT + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.replace(tmp, OUT)
    print('Записано: %s' % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
