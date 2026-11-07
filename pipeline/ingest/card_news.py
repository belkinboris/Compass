# -*- coding: utf-8 -*-
"""Приток: новость о сделке, которая УЖЕ ЕСТЬ в базе, — сравнение с карточкой
по фактам и конкретное предложение владельцу (одобрено владельцем 6 ноября 2026).

ЗАЧЕМ. До 6 ноября 2026 у такой новости было два исхода, и оба плохие:
  * слабое совпадение или расхождение ложилось в `data/inbox/hold/*-enrich.json`,
    который никто не читал: пост @LawFirms о юристе покупателя Selectel/M1Cloud
    (NSP) пролежал там семь недель, сделка DDX/Vesper потерялась целиком —
    ворота привязали новость к чужой карточке, которой уже не было в базе;
  * сырье, похожее на карточку, через три часа приходило владельцу
    «⚠️ СОМНИТЕЛЬНОЙ … проверьте, не дубль ли» с кнопками «Это сделка» /
    «Не сделка». «Это сделка» собирала карточку-дубль, приток ее снимал
    (`drop_pending.py`), и новое из новости в ту карточку доходило не всегда
    (BIRCH у Swordfish потерялся).

КАК ТЕПЕРЬ. Каждая такая новость получает запись в `moderation_state.json`
(`card_news[<номер новости>]`, номер — `draft.draft_id_for`, тот же, что у
сырья по этому адресу) с ОДНИМ из исходов:
  * `same`     — нового нет; снята как дубль, причина записана (`reason`);
  * `apply`    — новое есть, и новость точно о ТОЙ ЖЕ сделке (те же стороны и
                 предмет, факт дословно в тексте): вносится в карточку само,
                 без вопроса владельцу (владелец, 7 ноября 2026), — `apply_ready`;
  * `offer`    — новое есть, но есть и сомнение: в консоль уходит конкретное предложение
                 «К карточке … добавить: <факт> — <цитата>» с кнопками
                 «Добавить в карточку» / «Новый этап сделки» / «Это другая сделка»;
  * `read`     — механика не может решить (расходятся числа, общие только
                 слова заголовка): статью читает агент в рутине притока
                 (`--queue` → ответ → `--apply`), не модель на сайте;
  * `new_deal` — ворота ошиблись карточкой (ее нет в базе или общие с ней
                 только общие слова): новость идет обычным путем новой сделки
                 (`promote.py` берет черновик отсюда, сырье — консоль как раньше);
  * `decided`  — владелец нажал кнопку, решение применено (`approve.py`).

ЧТО СРАВНИВАЕТ МЕХАНИКА — только то, где она надежна: адрес уже в источниках
карточки; сумма (`draft.sum_from_text`) и купленная доля
(`deal_multiples.acquired_percents`) — числа; консультант — имя фирмы из
словаря (каталоги FIRMS/INV_FIRMS сайта и консультанты базы) или голова
объявления фирмы (`advisors.lead_advisor`), рядом с глаголом сопровождения;
этап — слово статуса (`draft.guess_status`), только вперед. Смысловое
сравнение («это та же сделка или другая на том же активе») — чтение агентом.
Расхождения имен сторон с разбором заголовка механика не считает фактом:
`guess_parties` по заголовку против прочитанной карточки — шум (242 таких
«расхождения» в hold-файлах за два месяца, ни одного настоящего).

    python3 pipeline/ingest/card_news.py                    # сводка по исходам
    python3 pipeline/ingest/card_news.py --queue            # что читать агенту
    python3 pipeline/ingest/card_news.py --check ответ.json
    python3 pipeline/ingest/card_news.py --apply ответ.json --write
    python3 pipeline/ingest/card_news.py --auto [--write]   # внести уверенные (`apply`)
    python3 pipeline/ingest/card_news.py --backlog [--write] # разобрать старые hold/*-enrich.json
"""
import json
import os
import re
import sys
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
for _p in (HERE, os.path.dirname(HERE), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import advisors                                     # noqa: E402
import deal_multiples                               # noqa: E402
import draft as drafter                             # noqa: E402
import enrich                                       # noqa: E402
import match as matcher                             # noqa: E402
import promote                                      # noqa: E402
import source_names as editions                     # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
INDEX = os.path.join(ROOT, 'static', 'index.html')
HOLD_DIR = os.path.join(ROOT, 'data', 'inbox', 'hold')
SITE = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')

STATE_KEY = 'card_news'
# Исход, после которого запись больше не пересобирается: решение уже есть.
FINAL = ('same', 'new_deal', 'decided')
# Сколько часов сырье, похожее на карточку, ждет чтения агентом, прежде чем
# уйти владельцу предложением «добавить источник» (то же окно, что было у
# прежнего «ждет притока»: send_drafts.ENRICH_WAIT_H).
READ_WAIT_H = 3
# Предложений за прогон: консоль не должна тонуть в них (как RAW_PER_RUN).
OFFERS_PER_RUN = 5
# Новость, привязанную не к той карточке, ворота получают обратно, пока она
# свежая; старше — ее разбирает агент (`--queue`), а не механика: старая
# новость в ленте ворот без чтения дала бы карточки о давних сделках.
REROUTE_MAX_DAYS = 14
# Вердикты кнопок предложения (app/console.py: mod:<номер>:add|stage|other).
OFFER_VERDICTS = {'card_add': 'add', 'card_stage': 'stage', 'card_other': 'other'}
# Поля, которые может предложить механика или агент (ответ `--apply`).
FACT_FIELDS = ('src', 'sum', 'stake_acquired', 'law.adv', 'buyer_name', 'seller', 'stage')
FACT_LABEL = {'sum': 'Сумма', 'stake_acquired': 'Доля', 'buyer_name': 'Покупатель', 'seller': 'Продавец'}
# ВНОСИТСЯ САМО, БЕЗ ВОПРОСА ВЛАДЕЛЬЦУ (владелец, 7 ноября 2026: «Блин зачем
# ты это предлагаешь? Ты бы и сам по ним легко понял… Тут только wb вообще не
# то. Остальное видно и по сторонам и по тексту»). Механика — только числа и
# консультант (стороны из разбора заголовка — шум, этап двигает статус и
# зовет пост об этапе: это решает владелец кнопкой). Агент, прочитавший
# статью, может внести и сторону; этап — всегда предложением.
AUTO_FIELDS = ('sum', 'stake_acquired', 'law.adv')
AGENT_AUTO_FIELDS = AUTO_FIELDS + ('buyer_name', 'seller')
# Та же сделка по названию предмета — только если новость вышла не дальше
# этого от даты карточки: тот же торговый центр через год — скорее новая продажа.
SAME_DEAL_DAYS = 120
ADV_ROLE = re.compile(r'^(?:Юридический|Финансовый) консультант')
PLACEHOLDER = re.compile(r'раскры|сообща', re.I)


# --- общие мелочи ------------------------------------------------------------
def now_iso(now=None):
    return (now or datetime.now(timezone.utc)).isoformat(timespec='seconds')


def _hours_since(iso, now=None):
    try:
        then = datetime.fromisoformat(str(iso))
    except ValueError:
        return 0.0
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    return ((now or datetime.now(timezone.utc)) - then).total_seconds() / 3600.0


def flat(text):
    return re.sub(r'[^0-9a-zа-я]+', '', str(text or '').lower().replace('ё', 'е'))


def news_id(news):
    """Номер новости — тот же, что у сырья по этому адресу (draft.draft_id_for):
    кнопка предложения и кнопки сырья говорят об одной и той же новости."""
    if news.get('draft_id'):
        return str(news['draft_id'])
    return drafter.draft_id_for({'url': news.get('url'), 'title': news.get('title')})


def news_of_draft(draft):
    """Сырой черновик ворот как новость: заголовок, адрес, дата, источник."""
    src = next((s for s in draft.get('src') or [] if len(s) > 1 and s[1]), [None, None])
    return {'title': draft.get('title'), 'url': src[1], 'date': draft.get('date'),
            'summary': draft.get('summary'), 'source_id': src[0], 'draft_id': draft.get('draft_id')}


def news_text(news):
    """Заголовок и аннотация одним текстом; заголовок без точки в конце
    отделяется точкой, иначе он слипается с первой фразой аннотации в одно
    «предложение» и голова объявления фирмы не находится."""
    title = re.sub(r'\s+', ' ', str(news.get('title') or '')).strip()
    summary = re.sub(r'\s+', ' ', str(news.get('summary') or '')).strip()
    if title and summary and not re.search(r'[.!?…]$', title):
        title += '.'
    return ' '.join(x for x in (title, summary) if x)


def sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?…])\s+', str(text or '')) if s.strip()]


def sentence_with(text, needle):
    """Предложение новости, где стоит `needle` (цитата для факта), или весь текст."""
    for s in sentences(text):
        if needle and needle.lower() in s.lower():
            return s
    return str(text or '')[:300]


def card_urls(card):
    out = set()
    for key in ('src', 'discovery_src'):
        for ref in (card or {}).get(key) or []:
            if isinstance(ref, (list, tuple)) and len(ref) > 1 and ref[1]:
                out.add(str(ref[1]))
    return out


def resolve_id(deal_id, base):
    """Номер карточки после слияний: слитая карточка живет под номером той, в
    которую ее слили (`merged` базы; цепочка — до конца)."""
    merged = base.get('merged') or {}
    seen = set()
    while deal_id in merged and deal_id not in seen:
        seen.add(deal_id)
        deal_id = merged[deal_id]
    return deal_id


def find_card(deal_id, base, pending_cards=()):
    """(карточка, где лежит: 'base' | 'pending') или (None, None). Слитая
    карточка находится под номером той, в которую ее слили."""
    deal_id = resolve_id(deal_id, base)
    for deal in base.get('deals') or []:
        if deal.get('id') == deal_id:
            return deal, 'base'
    for card in pending_cards or []:
        if card.get('id') == deal_id:
            return card, 'pending'
    return None, None


def card_link(deal_id, where):
    return '%s/#/%s/%s' % (SITE, 'deal' if where == 'base' else 'preview', deal_id)


def card_names(card, companies):
    """Имена, по которым новость узнается как новость ОБ ЭТОЙ карточке: стороны
    (профиль и текст) и названия в кавычках из заголовка."""
    names = []
    for ref in ('buyer', 'target', 'asset_id', 'seller_id'):
        row = (companies or {}).get(card.get(ref)) or {}
        names += [row.get('name'), row.get('legal_name')]
    names += [card.get(k) for k in ('buyer_name', 'seller', 'asset')]
    names += list(matcher.quoted(card.get('title') or ''))
    out = []
    for n in names:
        if isinstance(n, str) and len(flat(n)) >= 3 and n not in out:
            out.append(n)
    return out


# Слова имени, по которым его не узнать: правовая форма, род занятий, место.
_NAME_STOP = {w[:6] for w in matcher.STOP} | matcher.GENERIC_STEMS | {
    'россия', 'москва', 'москве', 'петерб', 'санкт-', 'сети', 'сеть', 'холдин', 'бренд', 'бренда',
    'офис', 'здание', 'участо', 'объект', 'проект', 'банк', 'банка', 'фонд', 'фонда'}


def _words(text):
    return re.findall(r'[0-9a-zа-я]+', str(text or '').lower().replace('ё', 'е'))


def name_tokens(name):
    """Собственные слова имени: латиница или слово с заглавной буквы, от 4 букв,
    не правовая форма и не род занятий («российские активы сети Metro Cash &
    Carry» узнается по «Metro», «Cash», «Carry»)."""
    out = []
    for raw in re.findall(r'[0-9A-Za-zА-Яа-яЁё]+', str(name or '')):
        low = raw.lower().replace('ё', 'е')
        if low[:6] in _NAME_STOP or low in _NAME_STOP:
            continue
        latin = bool(re.match(r'[A-Za-z0-9]', raw))
        # Латиница узнается с трех букв (JTI, KFC), аббревиатура заглавными —
        # с двух (VK, МТС); русское слово — с четырех и с заглавной буквы.
        if (raw.isupper() and len(low) >= 2) or (latin and len(low) >= 3) \
                or (len(low) >= 4 and raw[0].isupper()):
            out.append(low)
    return out


def title_names(title):
    """Собственные слова заголовка карточки как имена — у карточки без
    сторон-профилей («Сеть петербургских кофеен Baggins Coffee продали») иначе
    узнавать нечего. Первое слово с заглавной — начало фразы, не имя."""
    words = re.findall(r'[0-9A-Za-zА-Яа-яЁё]+', str(title or ''))
    out = []
    for i, raw in enumerate(words):
        if i == 0 and not re.match(r'[A-Za-z0-9]', raw) and not raw.isupper():
            continue
        out += name_tokens(raw)
    return out


def names_in_text(names, text):
    """Какие имена карточки стоят в новости: имя целиком или хотя бы одно его
    собственное слово с точностью до окончания («Ленты» = «Лента»)."""
    words = set(_words(text))
    body = flat(text)
    hit = []
    for name in names:
        key = flat(name)
        if len(key) >= 4 and key in body:
            hit.append(name)
            continue
        for tok in name_tokens(name):
            stem = tok[:max(4, len(tok) - 2)]
            if (tok in words) if len(tok) < 4 else any(w.startswith(stem) for w in words):
                hit.append(name)
                break
    return hit


_INDEX_CACHE = {}


def rematch(news, base, pending_cards=()):
    """Сильное совпадение новости с карточкой базы или очереди сейчас — номер
    карточки и причина, или (None, None). Нужно, когда прежняя привязка ворот
    больше не годится: старая карточка слита, а сделка живет в другой."""
    key = (id(base), len(base.get('deals') or []), len(pending_cards or []))
    idx = _INDEX_CACHE.get(key)
    if idx is None:
        idx = matcher.index_base(list(base.get('deals') or []) + list(pending_cards or []),
                                 base.get('companies'), base.get('match_keys'))
        _INDEX_CACHE.clear()
        _INDEX_CACHE[key] = idx
    buyer, asset, seller, _ = drafter.guess_parties(news.get('title'))
    found, why = matcher.match({'title': news.get('title'), 'date': news.get('date'), 'url': news.get('url'),
                                'buyer': buyer, 'asset': asset, 'seller': seller,
                                'status': drafter.guess_status(news_text(news))}, idx)
    if found and matcher.is_strong(why):
        return found, why
    return None, None


# --- словарь фирм --------------------------------------------------------------
_FIRMS_CACHE = {}


def firm_dictionary(base, index_path=None):
    """[(имя, 'law' | 'fin')]: каталоги сайта (FIRMS — юридические, INV_FIRMS —
    инвестиционные) и консультанты, уже записанные в карточки базы."""
    index_path = index_path or INDEX
    key = (index_path, len(base.get('deals') or []))
    if key in _FIRMS_CACHE:
        return _FIRMS_CACHE[key]
    out, seen = [], set()

    def add(name, kind):
        name = re.sub(r'\s*\(.*?\)\s*', ' ', str(name or '')).strip()
        if len(flat(name)) < 3 or PLACEHOLDER.search(name) or flat(name) in seen:
            return
        seen.add(flat(name))
        out.append((name, kind))
    try:
        html = open(index_path, encoding='utf-8').read()
    except OSError:
        html = ''
    for const, kind in (('const FIRMS = [', 'law'), ('const INV_FIRMS = [', 'fin')):
        at = html.find(const)
        if at < 0:
            continue
        block = html[at:html.find('\n];', at)]
        for m in re.finditer(r'\bn:"([^"]+)"', block):
            add(m.group(1), kind)
    for deal in base.get('deals') or []:
        for row in (deal.get('law') or {}).get('adv') or []:
            if isinstance(row, list) and len(row) > 1:
                add(row[1], 'fin' if str(row[0]).startswith('Финансов') else 'law')
    _FIRMS_CACHE[key] = out
    return out


_VERB = re.compile(advisors.VERB, re.I)


def advisers_in(text, firms, heads=None):
    """[(фирма, роль, предложение)] — консультанты, о роли которых новость говорит
    прямо: голова объявления фирмы (`advisors.lead_advisor`) или имя из словаря
    СРАЗУ ПЕРЕД глаголом сопровождения в том же предложении («…сделку
    сопровождала BIRCH» не считается: имя должно быть подлежащим)."""
    out, seen = [], set()
    for head in (heads if heads is not None else [text]):
        lead = advisors.lead_advisor(head)
        if not lead:
            continue
        for firm in lead[0]:
            if flat(firm) not in seen:
                out.append((firm, lead[1], lead[2]))
                seen.add(flat(firm))
    for sentence in sentences(text):
        for m in _VERB.finditer(sentence):
            head = sentence[max(0, m.start() - 90):m.start()]
            for name, kind in firms:
                if flat(name) in seen:
                    continue
                hits = list(re.finditer(r'(?<![\w])%s(?![\w])' % re.escape(name), head, re.I))
                # Имя — подлежащее глагола: между ним и глаголом не больше
                # 40 знаков и ни одной запятой («ВТБ продал актив, сделку
                # сопровождал …» — ВТБ здесь сторона, а не консультант).
                gap = head[hits[-1].end():] if hits else None
                if gap is None or len(gap) > 40 or re.search(r'[,;:—]', gap):
                    continue
                role = advisors.role_label(sentence)
                if kind == 'fin':
                    role = role.replace('Юридический', 'Финансовый')
                out.append((name, role, sentence))
                seen.add(flat(name))
    return out


def card_advisers(card):
    names = [str(r[1]) for r in (card.get('law') or {}).get('adv') or []
             if isinstance(r, list) and len(r) > 1 and not PLACEHOLDER.search(str(r[1]))]
    fin = (card.get('eco') or {}).get('finadv')
    if isinstance(fin, str) and not PLACEHOLDER.search(fin) and fin.strip() not in ('', '—'):
        names.append(fin)
    return names


def adviser_known(firm, card):
    key = flat(firm)
    return any(key in flat(n) or (len(flat(n)) >= 3 and flat(n) in key) for n in card_advisers(card))


def card_percents(card):
    out = []
    eco = card.get('eco') or {}
    out += deal_multiples.subject_percents(eco.get('share') if eco.get('share') not in (None, '—') else None)
    out += deal_multiples.subject_percents(card.get('asset'))
    out += deal_multiples.acquired_percents(card.get('title'))
    if card.get('stake_acquired') is not None:
        try:
            out.append(float(card['stake_acquired']))
        except (TypeError, ValueError):
            pass
    return out


def _money(text):
    """Сумма в миллионах (рубль, доллар, евро — без пересчета) или None."""
    got = matcher.amount(text)
    if got is not None:
        return got
    m = re.search(r'(\d{1,3}(?:[ \u00a0]\d{3}){2,})(?:[.,]\d+)?\s*(?:₽|руб)', str(text or ''))
    if m:
        return float(re.sub(r'\D', '', m.group(1))) / 1e6
    return None


def same_money(a, b):
    """Одна сумма, записанная с разной точностью («1,3 млрд» и «1,318 млрд»,
    «6 млрд» и «6 082 198 500 ₽»), — не расхождение: разница до 3%."""
    if enrich.agree(a, b):
        return True
    x, y = _money(a), _money(b)
    return bool(x and y) and abs(x - y) / max(x, y) <= 0.03


def same_share(news_value, card_values):
    """«42%» в новости и «42,152%» в карточке — одна доля, округленная."""
    whole = abs(news_value - round(news_value)) < 1e-9
    return any(abs(news_value - x) < (1 if whole else 0.05) for x in card_values)


def _pct(value):
    text = ('%.3f' % value).rstrip('0').rstrip('.')
    return text.replace('.', ',') + '%'


# --- сравнение с карточкой ----------------------------------------------------
def fact(field, value, label, quote):
    return {'field': field, 'value': value, 'label': label, 'quote': str(quote or '')[:400]}


def strong_now(why, card, news):
    """Сильное ли совпадение СЕЙЧАС. «Тот же адрес источника» устаревает: если
    адреса в карточке больше нет (карточку пересобрали, источник сняли), общего
    у новости с ней ничего не осталось («Софтэкс»/Western Union висел на
    карточке Metro по адресу общего указа)."""
    if not matcher.is_strong(why):
        return False
    if str(why).startswith('тот же адрес') and card is not None:
        return str(news.get('url') or '') in card_urls(card)
    return True


def compare(card, news, base, firms=None, strong=True):
    """Что новость дает карточке: {'facts': [...], 'clashes': [...], 'url_known': bool}.

    Факт — только то, чего в карточке нет; расхождение — новость называет ДРУГОЕ
    число в заполненном поле (сумма, доля): в базу оно само не идет, его читает
    агент. Источник — факт, если адреса нет в карточке."""
    comps = base.get('companies') or {}
    text = news_text(news)
    title = str(news.get('title') or '')
    facts, clashes = [], []
    url = str(news.get('url') or '')
    url_known = bool(url) and url in card_urls(card)
    if url_known:
        # Карточку собирали по этому же тексту — читающий его уже видел; что не
        # попало в карточку, не попало сознательно (242 «расхождения» такого
        # вида в hold-файлах за два месяца — разбор заголовка против чтения).
        return {'facts': [], 'clashes': [], 'url_known': True}
    if url.startswith('http'):
        label = editions.edition_label(url) or news.get('source_name') or news.get('source_id') or 'источник'
        facts.append(fact('src', [label, url], 'Источник', title))

    money = drafter.sum_from_text(text)
    if money:
        current = enrich.current_value(card, 'sum', comps)
        number = re.match(r'[$€]?\s*(\d[\d,.]*)', money)
        quote = sentence_with(text, number.group(1) if number else money)
        # «Сделку оценили в 10 млрд рублей» — оценка, не цена: та же пометка,
        # что требует review.sum_is_supported (иначе факт не внесется ни сам,
        # ни по кнопке владельца — «Город Косино», 7 ноября 2026).
        import review
        if '(по оценке)' not in money and review.sum_is_supported(money + ' (по оценке)', quote) is None:
            money += ' (по оценке)'
        if not current and enrich.is_retracted(card, 'sum', money):
            clashes.append('сумма %s: это значение уже снимали как неверное' % money)
        elif not current:
            facts.append(fact('sum', money, FACT_LABEL['sum'], quote))
        elif current and not same_money(money, current):
            clashes.append('сумма: в новости %s, в карточке %s' % (money, current))

    got = deal_multiples.acquired_percents(text)
    if got:
        have = card_percents(card)
        share = got[0]
        if not have:
            facts.append(fact('stake_acquired', share, '%s %s' % (FACT_LABEL['stake_acquired'], _pct(share)),
                              sentence_with(text, _pct(share)[:-1])))
        elif not same_share(share, have):
            clashes.append('доля: в новости %s, в карточке %s' % (_pct(share), ', '.join(_pct(x) for x in have)))

    parties = {flat(n) for n in card_names(card, comps)}
    heads = [x for x in (news.get('title'), news.get('summary')) if x]
    for firm, role, sentence in advisers_in(text, firms if firms is not None else firm_dictionary(base), heads):
        if adviser_known(firm, card) or flat(firm) in parties:
            continue
        facts.append(fact('law.adv', [role, firm], '%s: %s' % (role, firm), sentence))

    # Сторона из разбора заголовка — факт только при сильном совпадении: при
    # слабом новое имя покупателя скорее говорит о ДРУГОЙ сделке, это решает чтение.
    buyer, _asset, seller, _hint = drafter.guess_parties(title) if strong else (None, None, None, None)
    for field, guess in (('buyer_name', buyer), ('seller', seller)):
        if guess and any(enrich.agree(guess, n) for n in card_names(card, comps)):
            continue                    # то же имя уже стоит в карточке в другой роли
        if guess and not enrich.current_value(card, field, comps) and not enrich.is_retracted(card, field, guess):
            facts.append(fact(field, guess, FACT_LABEL[field], title))

    status = drafter.guess_status(text)
    if status:
        kind = enrich.STAGE_KIND[status]
        current = card.get('status')
        if status == 'Не состоялась':
            forward = current not in ('Не состоялась', 'Закрыта')
        else:
            forward = current != 'Не состоялась' and \
                enrich.STATUS_RANK.get(status, -1) > enrich.STATUS_RANK.get(current, -1)
        has_kind = any(e.get('kind') == kind for e in card.get('events') or [])
        if forward and not has_kind and enrich.is_retracted(card, 'status', status):
            clashes.append('статус «%s» уже снимали как преждевременный — переводить только после '
                           'чтения статьи' % status)
        elif forward and not has_kind:
            facts.append(fact('stage', {'kind': kind, 'status': status, 'date': news.get('date')},
                              'Новый этап: %s' % enrich.STAGE_TITLE[kind].lower(), title))
    return {'facts': facts, 'clashes': clashes, 'url_known': url_known}


def misrouted(deal_id, card, news, why, companies):
    """Причина, по которой ворота привязали новость НЕ к той карточке, или None.

    Два признака: карточки нет ни в базе, ни в очереди (DDX/Vesper: карточку
    «Билайна», к которой ворота привязали две новости, к тому времени слили);
    или совпадение слабое и ни одно имя карточки в новости не стоит — общие
    только слова заголовка («здание в центре Москвы»)."""
    if card is None:
        return 'карточки %s нет ни в базе, ни в очереди' % deal_id
    if strong_now(why, card, news):
        return None
    # Предмет и сторона карточки названы в новости — это она, даже если
    # кавычки разные (SASCO, 7 ноября 2026: у карточки «Дело», в новости
    # «Росатом» и полное имя пароходства — а Шишкарев и SASCO те же).
    if sure_same_deal(card, news, why, companies):
        return None
    text = news_text(news)
    # РАЗНЫЕ НАЗВАНИЯ В КАВЫЧКАХ — РАЗНЫЕ ОБЪЕКТЫ (владелец, 6 ноября 2026: пермский
    # ЖК «Сибирский квартал» предложили дописать к ДЦ «Волна» — общими были только
    # «Перми» и «продают»). Город, отрасль, глагол сделку не опознают; название
    # объекта или компании в кавычках — опознает. У карточки есть свои названия,
    # ни одного нет в новости, а в новости стоит свое — это другая сделка.
    card_quoted = [q for q in matcher.quoted(' '.join(str(card.get(k) or '') for k in ('title', 'asset')))
                   if len(flat(q)) >= 3]
    news_quoted = [q for q in matcher.quoted(text) if len(flat(q)) >= 3]
    if card_quoted and news_quoted and not names_in_text(card_quoted, text) \
            and not any(flat(q) in flat(' '.join(card_quoted)) for q in news_quoted):
        return ('у карточки %s свои названия (%s), в новости другие (%s) — другой объект'
                % (deal_id, ', '.join('«%s»' % q for q in card_quoted[:3]),
                   ', '.join('«%s»' % q for q in news_quoted[:3])))
    names = card_names(card, companies) + title_names(card.get('title'))
    if not names_in_text(names, text):
        return 'с карточкой %s общие только общие слова (%s), ни одного ее имени в новости нет' % (deal_id, why)
    return None


def _day(value):
    try:
        return date.fromisoformat(str(value or '')[:10])
    except ValueError:
        return None


def sure_same_deal(card, news, why, companies):
    """Почему механика уверена, что новость — о ТОЙ ЖЕ сделке, или None.

    Уверенность — одно из трех: сильное совпадение ворот; предмет карточки
    (покупаемая компания, актив) И еще одна ее сторона (покупатель или
    продавец) названы в новости — NSP о Selectel и M1Cloud; название предмета в
    кавычках стоит в новости — торговый центр «Город Косино». Для двух последних
    новость должна выйти не дальше SAME_DEAL_DAYS от даты карточки. Покупка ВТБ
    5% WB Банка у карточки «RWB выкупили офис „Открытия“ у ВТБ» не проходит:
    стороны общие, а предмета карточки (офис «Открытия») в новости нет."""
    if card is None:
        return None
    if strong_now(why, card, news):
        return 'та же сделка (%s)' % why
    a, b = _day(card.get('date')), _day(news.get('date'))
    if not (a and b) or abs((a - b).days) > SAME_DEAL_DAYS:
        return None
    text = news_text(news)
    body = flat(text)

    def names(*refs):
        out = []
        for ref in refs:
            row = (companies or {}).get(card.get(ref)) or {}
            out += [row.get('name'), row.get('legal_name')]
        return [n for n in out if isinstance(n, str) and len(flat(n)) >= 3]
    subject_quoted = [q for q in matcher.quoted(str(card.get('asset') or '')) if len(flat(q)) >= 4]
    hit = [q for q in subject_quoted if flat(q) in body]
    if hit:
        return 'в новости то же название предмета, что в карточке («%s»)' % hit[0]
    subject = names('target', 'asset_id') + ([card['asset']] if card.get('asset') else [])
    sides = names('buyer', 'seller_id') + [card.get(k) for k in ('buyer_name', 'seller')
                                            if isinstance(card.get(k), str)]
    got_subject, got_side = names_in_text(subject, text), names_in_text(sides, text)
    if got_subject and got_side:
        return 'в новости тот же предмет и та же сторона, что в карточке (%s; %s)' % (got_subject[0], got_side[0])
    return None


def doubt_of(card, news, why, companies, cmp):
    """Почему новое из новости нельзя внести самим (None — можно): ровно то,
    что владелец увидит строкой «Почему спрашиваем»."""
    if cmp['clashes']:
        return 'источники расходятся с карточкой: %s' % '; '.join(cmp['clashes'])
    other = [f['label'] for f in cmp['facts'] if f['field'] not in AUTO_FIELDS + ('src',)]
    if other:
        return 'в новости %s — это меняет карточку, решаете вы' % ', '.join(x.lower() for x in other)
    if not sure_same_deal(card, news, why, companies):
        return 'не уверены, что это та же сделка: в новости нет предмета карточки или ее сторон'
    return None


def sort_news(news, deal_id, why, base, pending_cards=(), origin='enrich', card=None, now=None, firms=None):
    """Запись `card_news` для одной новости — с исходом и причиной.

    `card` — карточка после автоматического обогащения (enrich.py: источник и
    пустые поля уже дописаны), иначе берется из базы/очереди."""
    deal_id = resolve_id(deal_id, base)
    found, where = find_card(deal_id, base, pending_cards)
    card = card if card is not None else found
    wrong = misrouted(deal_id, card, news, why, base.get('companies') or {})
    if wrong:
        # Прежняя привязка не годится — может, сделка живет в другой карточке.
        other, other_why = rematch(news, base, pending_cards)
        if other and other != deal_id:
            deal_id, why = other, other_why
            card, where = find_card(deal_id, base, pending_cards)
            wrong = None
    entry = {
        'id': news_id(news), 'deal_id': deal_id, 'where': where, 'origin': origin, 'why': str(why or ''),
        'news': {k: (str(news.get(k))[:1500] if news.get(k) is not None else None)
                 for k in ('title', 'summary', 'url', 'date', 'source_id')},
        'since': now_iso(now), 'facts': [], 'clashes': [],
    }
    if card is not None:
        entry['card_title'] = str(card.get('title') or '')[:200]
    if wrong:
        entry.update(outcome='new_deal', reason=wrong)
        return entry
    strong = strong_now(why, card, news)
    cmp = compare(card, news, base, firms, strong=strong)
    entry['facts'], entry['clashes'] = cmp['facts'], cmp['clashes']
    new = [f for f in cmp['facts'] if f['field'] != 'src']
    comps = base.get('companies') or {}
    if new:
        doubt = doubt_of(card, news, why, comps, cmp)
        if doubt:
            entry.update(outcome='offer', reason='в новости есть то, чего нет в карточке', doubt=doubt)
        else:
            entry.update(outcome='apply', reason='%s; новое внесем сами' % sure_same_deal(card, news, why, comps))
    elif cmp['clashes']:
        entry.update(outcome='read', reason='источники расходятся: %s' % '; '.join(cmp['clashes']))
    elif cmp['url_known']:
        entry.update(outcome='same', reason='источник уже в карточке %s, нового в новости нет' % deal_id)
    elif strong:
        entry.update(outcome='same', reason='та же сделка, что %s (%s); кроме источника, нового нет'
                     % (deal_id, why or 'совпадение ворот'))
    elif sure_same_deal(card, news, why, comps):
        # SASCO (7 ноября 2026): те же Шишкарев и SASCO, та же доля 58,67% —
        # читать тут нечего, это повтор.
        entry.update(outcome='same', reason='%s; нового для карточки %s нет'
                     % (sure_same_deal(card, news, why, comps), deal_id))
    else:
        entry.update(outcome='read', reason='похоже на карточку %s (%s); механика не нашла новых чисел, '
                     'консультантов или этапа — прочитать статью' % (deal_id, why))
    return entry


# --- память -------------------------------------------------------------------
def book(state):
    return state.setdefault(STATE_KEY, {})


def register(state, entry):
    """Записать исход. Запись с решением (исход из FINAL, отправленное
    предложение, прочитанное агентом) не пересобирается — возвращается она."""
    old = book(state).get(entry['id'])
    if old and (old.get('outcome') in FINAL or old.get('sent_at') or old.get('read_by')):
        return old
    if old:
        entry['since'] = old.get('since') or entry['since']
    book(state)[entry['id']] = entry
    if entry['outcome'] == 'same' and entry.get('origin') == 'raw':
        mark_raw(state, entry, 'enrich:%s' % entry['deal_id'])
    return entry


def mark_raw(state, entry, verdict):
    """Сырье по этой новости больше не показывать (та же память, что у
    `raw_screen.py --enrich` и решений владельца)."""
    state.setdefault('decided_raw', {})[entry['id']] = verdict
    title = (entry.get('news') or {}).get('title')
    if title:
        state.setdefault('raw_titles', {})[promote.raw_key(title)] = verdict
    if entry.get('reason') and verdict.startswith('enrich:'):
        state.setdefault('auto_drop_reasons', {})[entry['id']] = entry['reason']


def escalate(entry, now=None):
    """Слабое совпадение, которое агент не прочитал за READ_WAIT_H часов, —
    обычным путем новой сделки, а не вопросом владельцу «та же ли это сделка»
    (владелец, 6 ноября 2026: «это автоматом должно было без меня решиться»).
    Владельцу идут только предложения с конкретным новым фактом."""
    if entry.get('outcome') != 'read' or entry.get('origin') != 'raw' or entry.get('clashes'):
        return False
    if _hours_since(entry.get('since'), now) < READ_WAIT_H:
        return False
    news = entry.get('news') or {}
    text = news_text(news)
    quoted = [q for q in matcher.quoted(entry.get('card_title') or '') if len(flat(q)) >= 3]
    if quoted and names_in_text(quoted, text):
        # Название из карточки в новости есть, нового факта нет — та же сделка.
        entry['outcome'] = 'same'
        entry['reason'] = ('в новости то же название, что в карточке %s (%s), нового для нее нет — '
                           'снята как повтор' % (entry.get('deal_id'), ', '.join('«%s»' % q for q in quoted[:2])))
    else:
        entry['outcome'] = 'new_deal'
        entry['reason'] = ('совпадение с карточкой %s слабое: ее названия в новости нет, нового факта для '
                           'нее нет — новость идет как новая сделка' % entry.get('deal_id'))
    return True


def save_entries(entries, also=None):
    """Перечитать состояние прямо перед записью и положить свои записи поверх
    (другой прогон мог записать его, пока шел этот)."""
    state = promote.load_state()
    for e in entries:
        register(state, e)
    if also:
        also(state)
    promote.save_state(state)
    return state


# --- сообщение в консоль --------------------------------------------------------
def _short(text, limit=220):
    text = re.sub(r'\s+', ' ', str(text or '')).strip()
    return text if len(text) <= limit else text[:limit - 1].rstrip() + '…'


def stage_fact(entry):
    return next((f for f in entry.get('facts') or [] if f['field'] == 'stage'), None)


def offer_message(entry):
    """Текст предложения в консоль: что добавить, цитата, источник, кнопки."""
    news = entry.get('news') or {}
    link = card_link(entry['deal_id'], entry.get('where') or 'base')
    lines = ['🧩 [дополнение %s] — новость о сделке, которая уже есть %s'
             % (entry['id'], 'на сайте' if entry.get('where') != 'pending' else 'в очереди на проверку'),
             '',
             'К карточке «%s» (%s) добавить:' % (_short(entry.get('card_title'), 160), link)]
    facts = sorted(entry.get('facts') or [], key=lambda f: f['field'] == 'src')
    for f in facts:
        if f['field'] == 'src':
            lines.append('• Источник: %s' % f['value'][1])
        else:
            lines.append('• %s — «%s»' % (f['label'], _short(f['quote'])))
    lines.append('')
    lines.append('Новость: «%s»' % _short(news.get('title'), 200))
    if entry.get('read_by') == 'agent' and entry.get('reason'):
        lines.append('Что увидели при чтении: %s' % _short(entry['reason'], 300))
    if entry.get('doubt'):
        lines.append('Почему спрашиваем: %s.' % _short(entry['doubt'], 300).rstrip('.'))
    elif 'не уверены' in str(entry.get('reason') or ''):
        lines.append('Что проверили: %s.' % entry['reason'])
    lines.append('')
    if stage_fact(entry):
        lines.append('✅ «Добавить в карточку» — внесем все, кроме этапа; источник встанет в список.')
        lines.append('📌 «Новый этап сделки» — то же и еще этап в ходе сделки; пост об этапе '
                     'придет сюда отдельно.')
    else:
        lines.append('✅ «Добавить в карточку» — внесем это в карточку, источник встанет в список.')
    lines.append('🆕 «Это другая сделка» — соберем по новости отдельную карточку, она придет '
                 'сюда на проверку. По молчанию ничего не меняется.')
    return '\n'.join(lines)


def offer_keyboard(entry):
    row = [{'text': '✅ Добавить в карточку', 'callback_data': 'mod:%s:add' % entry['id']}]
    second = []
    if stage_fact(entry):
        second.append({'text': '📌 Новый этап сделки', 'callback_data': 'mod:%s:stage' % entry['id']})
    second.append({'text': '🆕 Это другая сделка', 'callback_data': 'mod:%s:other' % entry['id']})
    return {'inline_keyboard': [row, second]}


def plan_offers(state, base, pending_cards=(), limit=OFFERS_PER_RUN, shown=()):
    """Предложения, которые пора показать: исход `offer`, еще не отправлены,
    карточка на месте. Старые — первыми."""
    out = []
    for entry in sorted(book(state).values(), key=lambda e: str(e.get('since') or '')):
        if entry.get('outcome') != 'offer' or entry.get('sent_at'):
            continue
        if ('offer:%s' % entry['id']) in set(shown or ()):
            entry['sent_at'] = entry.get('sent_at') or now_iso()
            continue
        card, where = find_card(entry['deal_id'], base, pending_cards)
        if card is None:
            continue
        entry['where'] = where
        entry['card_title'] = str(card.get('title') or '')[:200]
        out.append(entry)
    return out[:limit] if limit else out


# --- решения владельца (approve.py) --------------------------------------------
def decided_offers(decisions):
    """Последнее решение по каждому предложению: {номер: решение}."""
    out = {}
    for d in decisions or []:
        if d.get('verdict') in OFFER_VERDICTS:
            out[str(d.get('deal_id'))] = d
    return out


def _texts(entry):
    """Тексты, в которых обязана лежать цитата: сама новость и все, что приток
    забрал на этот диск (лента и полные тексты статей)."""
    texts = [news_text(entry.get('news') or {})]
    try:
        import review
        texts += review.source_texts()
    except Exception:                                     # noqa: BLE001
        pass
    return [t for t in texts if t]


def apply_fact(card, f, entry, texts, base):
    """Внести один факт в карточку. None — внесен; иначе — почему нет."""
    import review
    field, value, quote = f['field'], f['value'], f.get('quote') or ''
    comps = base.get('companies') or {}
    url = (entry.get('news') or {}).get('url') or ''
    if field != 'src' and quote and not review.quote_is_real(quote, texts):
        return 'цитаты нет в тексте новости'
    if field == 'src':
        if url and url not in card_urls(card):
            card.setdefault('src', []).append(list(value))
        return None
    if field == 'sum':
        if enrich.current_value(card, 'sum', comps):
            return 'в карточке уже стоит сумма %s' % card.get('sum')
        problem = review.sum_is_supported(value, quote)
        if problem:
            return problem
        enrich.apply_props(card, [('sum', value, 'добавить', '')])
        return None
    if field == 'stake_acquired':
        if card_percents(card):
            return 'в карточке уже есть доля'
        if not any(abs(float(value) - x) < 0.05 for x in deal_multiples.acquired_percents(quote)):
            return 'в цитате нет этого процента рядом со словом о покупке'
        card['stake_acquired'] = float(value)
        eco = card.setdefault('eco', {})
        if eco.get('share') in (None, '', '—'):
            eco['share'] = _pct(float(value))
        return None
    if field == 'law.adv':
        role, firm = value[0], value[1]
        if not ADV_ROLE.match(str(role)):
            return 'роль консультанта не из списка'
        if flat(firm) not in flat(quote):
            return 'имени фирмы нет в цитате'
        if adviser_known(firm, card):
            return None
        law = card.setdefault('law', {})
        rows = [r for r in law.get('adv') or [] if not (isinstance(r, list) and len(r) > 1
                                                       and PLACEHOLDER.search(str(r[1])))]
        rows.append([role, firm, 'Источник: %s' % re.sub(r'^https?://(www\.)?', '', url)])
        law['adv'] = rows
        return None
    if field in ('buyer_name', 'seller'):
        if enrich.current_value(card, field, comps):
            return 'в карточке уже есть %s' % FACT_LABEL[field].lower()
        problem = review.name_is_supported(value, quote) if review.flat(value) not in review.flat(quote) else None
        if problem:
            return problem
        enrich.apply_props(card, [(field, value, 'добавить', '')])
        return None
    if field == 'stage':
        kind, status = value.get('kind'), value.get('status')
        if kind not in enrich.STAGE_TITLE:
            return 'неизвестный этап'
        if not any(w in quote.lower().replace('ё', 'е') for w in review.status_words(status, card.get('type'))):
            return 'в цитате нет слова, подтверждающего этап'
        day = value.get('date') or datetime.now(timezone.utc).date().isoformat()
        event = {'id': '%s-%s' % (kind, day), 'kind': kind, 'date': day, 'title': enrich.STAGE_TITLE[kind],
                 'historicalTitle': str((entry.get('news') or {}).get('title') or ''),
                 'note': _short(quote, 260),
                 'sources': [[editions.edition_label(url) or 'источник', url]] if url else []}
        if any(e.get('kind') == kind and e.get('date') == day for e in card.get('events') or []):
            return None
        props = []
        prior = enrich.prior_stage_event(card, event) if not card.get('events') else None
        if prior:
            props.append(('event', prior, 'добавить', ''))
        props.append(('event', event, 'добавить', ''))
        rank_new, rank_old = enrich.STATUS_RANK.get(status, -1), enrich.STATUS_RANK.get(card.get('status'), -1)
        if (status == 'Не состоялась' and card.get('status') not in ('Не состоялась', 'Закрыта')) \
                or (card.get('status') != 'Не состоялась' and rank_new > rank_old):
            props.append(('status', status, 'обновить', ''))
        enrich.apply_props(card, props)
        return None
    return 'поле %s не из списка' % field


def apply_offer(entry, verdict, base, pending, now=None):
    """Применить «Добавить в карточку» / «Новый этап сделки». Возвращает
    (внесено: [подписи], не внесено: [(подпись, почему)], где лежит карточка)."""
    card, where = find_card(entry['deal_id'], base, (pending or {}).get('cards') or [])
    if card is None:
        # Карточку успели снять или слить — решение не теряется: новость
        # возвращается на чтение агенту (card_news.py --queue).
        entry.update(outcome='read', reason='владелец нажал «добавить», но карточки %s уже нет'
                     % entry['deal_id'], decision=verdict, decided_at=now_iso(now))
        return [], [('карточка', 'карточки уже нет ни на сайте, ни в очереди')], None
    texts = _texts(entry)
    done, failed = [], []
    for f in entry.get('facts') or []:
        if f['field'] == 'stage' and verdict != 'card_stage':
            continue
        why = apply_fact(card, f, entry, texts, base)
        label = 'источник' if f['field'] == 'src' else f['label']
        if why:
            failed.append((label, why))
        else:
            done.append(label)
    url = (entry.get('news') or {}).get('url')
    if url and url.startswith('http') and url not in card_urls(card):
        label = editions.edition_label(url) or 'источник'
        card.setdefault('src', []).append([label, url])
    entry.update(outcome='decided', decision=verdict, decided_at=now_iso(now),
                 applied=done, not_applied=[list(x) for x in failed], where=where)
    return done, failed, where


# Отказ apply_fact, который значит «это уже есть в карточке», а не «факт не
# подтвержден»: уверенную новость он не останавливает (SASCO: доля 58,67% уже
# стоит в предмете карточки — внести остается только источник).
ALREADY = re.compile(r'^в карточке уже')


def apply_sure(entry, base, pending, now=None):
    """Внести уверенную новость (`apply`) тем же `apply_offer`, что кнопка
    «Добавить в карточку», но целиком или никак: факт не подтвердился цитатой
    (`review.quote_is_real`, `sum_is_supported`) — карточка не меняется, новость
    уходит на чтение агенту. Где лежит карточка ('base' | 'pending') или None."""
    card, where = find_card(entry['deal_id'], base, (pending or {}).get('cards') or [])
    if card is None:
        entry.update(outcome='read', reason='внести само не вышло: карточки %s уже нет' % entry['deal_id'])
        return None
    trial = json.loads(json.dumps(card))
    probe = json.loads(json.dumps(entry))
    trial_base = {'deals': [trial] if where == 'base' else [], 'companies': base.get('companies') or {}}
    done, failed, _w = apply_offer(probe, 'card_auto', trial_base,
                                   {'cards': [trial] if where == 'pending' else []}, now)
    bad = [(label, why) for label, why in failed if not ALREADY.search(str(why))]
    if bad:
        entry.update(outcome='read', reason='внести само не вышло (%s) — прочитать статью'
                     % '; '.join('%s: %s' % x for x in bad))
        entry.pop('read_by', None)
        return None
    card.clear()
    card.update(trial)
    entry.update(outcome='decided', decision='card_auto', decided_at=now_iso(now), where=where,
                 applied=done, not_applied=[list(x) for x in failed],
                 decided_by=entry.get('read_by') or 'mechanics')
    return where


def _write_base(data, path):
    """Записать базу так же, как approve.py: факты витрины пересчитаны."""
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import facts as facts_layer
    from pipeline import fns_registry as _fns_registry
    facts_layer.derive_all(data, facts_layer.build_ctx(data, _fns_registry.REGISTRY))
    json.dump(data, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def apply_ready(state=None, pending=None, write=True, now=None, data_path=None):
    """Внести в карточки все уверенные новости (`apply`). Базу перечитывает
    прямо перед записью (другой прогон мог ее записать). `state` и `pending`
    переданы — правятся на месте, записывает их вызвавший (send_drafts.py);
    не переданы — читаются и пишутся здесь. Сообщений в консоль нет: правка
    опубликованной карточки доходит до поста сама (send_telegram.
    card_changes_since_post). `data_path` — база вызвавшего (его DATA).
    Возвращает [(запись, где)]."""
    own_state, own_pending = state is None, pending is None
    state = promote.load_state() if own_state else state
    ready = [e for e in book(state).values() if e.get('outcome') == 'apply']
    if not ready:
        return []
    pending = promote.load_pending() if own_pending else pending
    data_path = data_path or DATA
    data = json.load(open(data_path, encoding='utf-8'))
    out = []
    for entry in sorted(ready, key=lambda e: str(e.get('since') or '')):
        where = apply_sure(entry, data, pending, now)
        out.append((entry, where))
        if where:
            mark_raw(state, entry, 'enrich:%s' % entry['deal_id'])
            print('  ВНЕСЕНО САМО %s -> %s: %s | %s' % (entry['id'], entry['deal_id'],
                                                       ', '.join(entry.get('applied') or []) or 'ничего',
                                                       _short((entry.get('news') or {}).get('title'), 80)))
        else:
            print('  НЕ ВНЕСЕНО  %s -> %s: %s' % (entry['id'], entry['deal_id'], entry.get('reason')))
    if write:
        if any(w == 'base' for _e, w in out):
            _write_base(data, data_path)
        if own_pending and any(w == 'pending' for _e, w in out):
            promote.save_pending(pending)
        if own_state:
            promote.save_state(state)
    return out


def closure_text(entry, card, done, failed, where):
    """Ответ владельцу — честный: «добавлено» только если источник новости
    правда стоит в карточке (перечитано после записи)."""
    news = entry.get('news') or {}
    head = 'По новости «%s»' % _short(news.get('title'), 120)
    if card is None:
        return '%s ничего не добавлено: %s. Новость вернули на проверку — ответим, куда ее отнесли.' % (
            head, failed[0][1] if failed else 'карточки нет')
    link = card_link(card['id'], where)
    url = news.get('url') or ''
    landed = bool(url) and url in card_urls(card)
    shown = [d for d in done if d != 'источник']
    parts = []
    if shown:
        parts.append('в карточку «%s» добавлено: %s' % (_short(card.get('title'), 120), '; '.join(shown)))
    elif landed:
        parts.append('в карточку «%s» добавлен источник' % _short(card.get('title'), 120))
    else:
        parts.append('в карточку «%s» ничего не добавлено' % _short(card.get('title'), 120))
    text = '%s %s' % (head, parts[0])
    if landed and shown:
        text += ', источник встал в список'
    text += '. %s' % link
    if failed:
        text += '\nНе добавлено: %s. Если это неверно, ответьте здесь.' % '; '.join(
            '%s — %s' % (lbl, why) for lbl, why in failed)
    return text


def other_text(entry):
    return ('По новости «%s» собираем отдельную карточку — она придет сюда на проверку.'
            % _short((entry.get('news') or {}).get('title'), 120))


def draft_for(entry, raw_drafts, companies):
    """Черновик для «Это другая сделка»: сырье с этим номером из hold, если оно
    там есть, иначе — сборка из записи новости (тот же draft.build, что у ворот)."""
    for d in raw_drafts or []:
        if str(d.get('draft_id')) == entry['id']:
            return d
    news = dict(entry.get('news') or {})
    return drafter.build(news, companies or {})


# --- новая сделка, которую ворота привязали не туда ----------------------------
def news_age_days(entry, now=None):
    today = (now or datetime.now(timezone.utc)).date()
    try:
        return (today - datetime.strptime(str((entry.get('news') or {}).get('date'))[:10], '%Y-%m-%d').date()).days
    except ValueError:
        return _hours_since(entry.get('since'), now) / 24


def rerouted_drafts(state, companies, cards=(), now=None):
    """Черновики для ворот (`promote.py`): новости из обогащения, которые ворота
    привязали не к той карточке, — пока они свежие. Повтор каждый прогон
    безопасен: ворота сами отсекают решенное (decided_raw, raw_titles); новость,
    по которой карточка уже собрана (адрес в ее источниках), не возвращается."""
    carded = set()
    for card in cards or []:
        carded |= card_urls(card)
    out = []
    for entry in book(state).values():
        if entry.get('outcome') != 'new_deal' or entry.get('origin') == 'raw':
            continue
        news = entry.get('news') or {}
        if news_age_days(entry, now) > REROUTE_MAX_DAYS or news.get('url') in carded:
            continue
        d = drafter.build(dict(news), companies or {})
        d['rerouted_from'] = entry['deal_id']
        out.append(d)
    return out


# --- чтение агентом -------------------------------------------------------------
def queue(state, now=None):
    """Что читать агенту: исход `read`; давние `new_deal`, которые ворота уже не
    возьмут (старше REROUTE_MAX_DAYS); этапы, записанные по решению владельца,
    которым нужен пост."""
    reads, old_new, stages = [], [], []
    for entry in sorted(book(state).values(), key=lambda e: str(e.get('since') or '')):
        if entry.get('outcome') == 'read':
            reads.append(entry)
        elif entry.get('outcome') == 'new_deal' and entry.get('origin') != 'raw' \
                and not entry.get('reread') and news_age_days(entry, now) > REROUTE_MAX_DAYS:
            old_new.append(entry)
        elif entry.get('outcome') == 'decided' and entry.get('decision') == 'card_stage' \
                and not entry.get('milestone_done'):
            stages.append(entry)
    return reads, old_new, stages


def render_queue(state, base, pending_cards=()):
    reads, old_new, stages = queue(state)
    if not (reads or old_new or stages):
        print('Новостей о карточках базы на чтение нет.')
        return
    comps = base.get('companies') or {}
    for entry in reads:
        card, where = find_card(entry['deal_id'], base, pending_cards)
        news = entry.get('news') or {}
        print('id=%s  (%s)' % (entry['id'], entry.get('reason')))
        print('  новость: %s' % _short(news.get('title'), 200))
        print('  адрес:   %s | дата: %s' % (news.get('url') or '—', news.get('date') or '—'))
        if news.get('summary'):
            print('  текст:   %s' % _short(news['summary'], 400))
        if card is not None:
            print('  карточка %s (%s): %s' % (card['id'], where, _short(card.get('title'), 160)))
            print('    стороны: %s | сумма: %s | статус: %s' % (
                ', '.join(card_names(card, comps)[:4]) or '—', card.get('sum') or '—', card.get('status') or '—'))
            print('    консультанты: %s' % ('; '.join(card_advisers(card)) or '—'))
            print('    источники: %s' % ', '.join(sorted(card_urls(card)))[:300])
        print()
    for entry in old_new:
        news = entry.get('news') or {}
        print('id=%s  ДАВНЯЯ НОВОСТЬ, ПРИВЯЗАННАЯ НЕ К ТОЙ КАРТОЧКЕ (%s)' % (entry['id'], entry.get('reason')))
        print('  новость: %s | %s | %s' % (_short(news.get('title'), 160), news.get('url'), news.get('date')))
        print('  сделка в базе есть — ответ same/offer с ее номером в deal_id; нет — собрать карточку '
              'обычным путем (как по кнопке «в работу») и ответить separate')
        print()
    for entry in stages:
        kind = ((stage_fact(entry) or {}).get('value') or {}).get('kind')
        print('ЭТАП ПО РЕШЕНИЮ ВЛАДЕЛЬЦА: %s %s — пост об этапе: review.py --milestone %s %s "<заголовок>" '
              '--write, затем send_milestone_drafts.py --write; потом ответ {"id": "%s", "outcome": "milestone_done"}'
              % (entry['deal_id'], kind, entry['deal_id'], kind, entry['id']))


ANSWER_OUTCOMES = ('same', 'apply', 'offer', 'separate', 'milestone_done')


def check_answer(answer, state, base, pending_cards=(), texts=None):
    """Причины отказа по каждому ответу агента: {номер: [причины]}. Пусто — можно
    применять. Цитата обязана лежать дословно в тексте новости или статьи."""
    import review
    problems = {}
    for item in answer:
        bad = []
        entry = book(state).get(str(item.get('id')))
        if entry is None:
            problems[str(item.get('id'))] = ['такой новости в очереди нет']
            continue
        outcome = item.get('outcome')
        if outcome not in ANSWER_OUTCOMES:
            bad.append('исход вне списка %s' % ', '.join(ANSWER_OUTCOMES))
        if outcome in ('same', 'separate', 'offer', 'apply') and not str(item.get('reason') or '').strip():
            bad.append('нужна причина (reason) — она уйдет в память и, для offer, владельцу')
        if outcome == 'offer' and not str(item.get('doubt') or '').strip():
            bad.append('offer без сомнения (doubt): та же сделка и факт в статье — ответ apply, '
                       'вносится сам; offer — только когда есть в чем сомневаться')
        deal_id = item.get('deal_id') or entry['deal_id']
        card, _where = find_card(deal_id, base, pending_cards)
        if outcome in ('same', 'offer', 'apply') and card is None:
            bad.append('карточки %s нет ни в базе, ни в очереди' % deal_id)
        if outcome in ('offer', 'apply'):
            facts = item.get('facts') or []
            if not facts:
                bad.append('%s без фактов' % outcome)
            if outcome == 'apply':
                for f in facts:
                    if f.get('field') not in AGENT_AUTO_FIELDS:
                        bad.append('apply: поле %r само не вносится (%s) — это offer'
                                   % (f.get('field'), ', '.join(AGENT_AUTO_FIELDS)))
            pool = (texts if texts is not None else review.source_texts()) + [news_text(entry.get('news') or {})]
            for f in facts:
                field = f.get('field')
                if field not in FACT_FIELDS or field == 'src':
                    bad.append('поле %r не из списка %s' % (field, ', '.join(FACT_FIELDS[1:])))
                    continue
                if not review.quote_is_real(f.get('quote') or '', pool):
                    bad.append('%s: цитаты нет в тексте новости или статьи' % field)
                if field == 'law.adv':
                    if not ADV_ROLE.match(str(f.get('role') or '')):
                        bad.append('law.adv: роль начинается с «Юридический консультант» или «Финансовый консультант»')
                    if flat(f.get('value')) not in flat(f.get('quote')):
                        bad.append('law.adv: имени фирмы нет в цитате')
                if field == 'sum':
                    problem = review.sum_is_supported(f.get('value'), f.get('quote') or '')
                    if problem:
                        bad.append('sum: %s' % problem)
                if field == 'stage' and f.get('value') not in enrich.STAGE_TITLE:
                    bad.append('stage: вид этапа из %s' % ', '.join(enrich.STAGE_TITLE))
        if bad:
            problems[entry['id']] = bad
    return problems


def _answer_fact(item_fact, news):
    field = item_fact['field']
    if field == 'law.adv':
        return fact('law.adv', [item_fact['role'], item_fact['value']],
                    '%s: %s' % (item_fact['role'], item_fact['value']), item_fact['quote'])
    if field == 'stage':
        kind = item_fact['value']
        status = {v: k for k, v in enrich.STAGE_KIND.items()}[kind]
        return fact('stage', {'kind': kind, 'status': status, 'date': item_fact.get('date') or news.get('date')},
                    'Новый этап: %s' % enrich.STAGE_TITLE[kind].lower(), item_fact['quote'])
    value = float(item_fact['value']) if field == 'stake_acquired' else item_fact['value']
    return fact(field, value, FACT_LABEL[field], item_fact['quote'])


def apply_answer(answer, state, now=None):
    """Ответ агента — в память (moderation_state.json). `apply` вносит в базу
    потом `apply_ready` (тот же прогон `--apply --write`), `offer` — кнопка
    владельца (approve.py)."""
    for item in answer:
        entry = book(state)[str(item['id'])]
        outcome = item['outcome']
        if outcome == 'milestone_done':
            entry['milestone_done'] = now_iso(now)
            continue
        if item.get('deal_id'):
            entry['deal_id'] = item['deal_id']
        entry['reason'] = item.get('reason')
        entry['read_by'] = 'agent'
        entry['read_at'] = now_iso(now)
        entry['reread'] = True
        if outcome == 'same':
            entry['outcome'] = 'same'
            mark_raw(state, entry, 'enrich:%s' % entry['deal_id'])
        elif outcome == 'separate':
            entry['outcome'] = 'new_deal'
            entry['reason'] = 'чтение: другая сделка — %s' % item.get('reason')
        else:
            src = [f for f in entry.get('facts') or [] if f['field'] == 'src']
            entry['facts'] = [_answer_fact(f, entry.get('news') or {}) for f in item['facts']] + src
            entry['outcome'] = outcome
            if outcome == 'offer':
                entry['doubt'] = item.get('doubt')
            else:
                entry.pop('doubt', None)
            entry.pop('sent_at', None)


# --- старые hold/*-enrich.json --------------------------------------------------
def backlog_items(hold_dir=None):
    """Записи всех hold/*-enrich.json, без повторов по адресу (последняя — свежая)."""
    hold_dir = hold_dir or HOLD_DIR
    seen = {}
    if not os.path.isdir(hold_dir):
        return []
    for name in sorted(os.listdir(hold_dir)):
        if not name.endswith('-enrich.json'):
            continue
        day = name[:10]
        try:
            doc = json.load(open(os.path.join(hold_dir, name), encoding='utf-8'))
        except (OSError, ValueError):
            continue
        for item in doc.get('items') or []:
            if not str(item.get('verdict') or '').startswith('enrich:'):
                continue
            key = item.get('news') or item.get('title')
            seen[key] = {'title': item.get('title'), 'url': item.get('news'), 'date': item.get('date') or day,
                         'summary': item.get('summary'), 'source_id': item.get('source_id'),
                         'verdict': item['verdict'], 'why': item.get('why')}
    return list(seen.values())


def sort_backlog(state, base, pending_cards=(), hold_dir=None, now=None):
    firms = firm_dictionary(base)
    out = []
    for item in backlog_items(hold_dir):
        if news_id(item) in book(state):
            continue
        deal_id = item['verdict'].split(':', 1)[1]
        out.append(sort_news(item, deal_id, item.get('why'), base, pending_cards, 'enrich', now=now, firms=firms))
    return out


def summary(state):
    from collections import Counter
    c = Counter(e.get('outcome') for e in book(state).values())
    sent = sum(1 for e in book(state).values() if e.get('sent_at'))
    print('Новости о карточках базы: %s; предложений показано владельцу: %d'
          % (', '.join('%s — %d' % kv for kv in sorted(c.items())) or 'нет', sent))


def main(argv):
    write = '--write' in argv
    state = promote.load_state()
    base = json.load(open(DATA, encoding='utf-8'))
    pending_cards = promote.load_pending().get('cards') or []
    if '--queue' in argv:
        render_queue(state, base, pending_cards)
        return 0
    if '--check' in argv or '--apply' in argv:
        path = argv[argv.index('--check' if '--check' in argv else '--apply') + 1]
        answer = json.load(open(path, encoding='utf-8'))
        problems = check_answer(answer, state, base, pending_cards)
        for nid, bad in problems.items():
            print('ОТКАЗ %s: %s' % (nid, '; '.join(bad)))
        if problems:
            print('Есть отказы — не пишу ничего.')
            return 1
        print('Ответ проверен: %d записей.' % len(answer))
        if '--apply' not in argv or not write:
            if '--apply' in argv:
                print('Сухой прогон. Запись — с ключом --write.')
            return 0
        state = promote.load_state()
        apply_answer(answer, state)
        promote.save_state(state)
        print('Записано. Предложения уйдут в консоль следующим send_drafts.py --write.')
        if any(where for _e, where in apply_ready()):
            print('Уверенные новости внесены в карточки — база изменилась: facts_derive, pytest, diff, коммит.')
        return 0
    if '--auto' in argv:
        ready = [e for e in book(state).values() if e.get('outcome') == 'apply']
        if not write:
            for e in ready:
                print('  ВНЕСТИ %s -> %s: %s' % (e['id'], e['deal_id'], ', '.join(
                    f['label'] for f in e.get('facts') or [] if f['field'] != 'src') or 'источник'))
            print('Уверенных новостей: %d. Сухой прогон. Запись — с ключом --write.' % len(ready))
            return 0
        apply_ready()
        return 0
    if '--backlog' in argv:
        entries = sort_backlog(state, base, pending_cards)
        from collections import Counter
        print('Старых записей hold/*-enrich.json к разбору: %d — %s' % (
            len(entries), ', '.join('%s — %d' % kv for kv in sorted(Counter(e['outcome'] for e in entries).items()))))
        for e in entries:
            if e['outcome'] != 'same':
                print('  %-8s %s -> %s | %s' % (e['outcome'], e['id'], e['deal_id'], _short(e['news']['title'], 80)))
                print('           %s' % e.get('reason'))
                for f in e.get('facts') or []:
                    print('           + %s = %s | «%s»' % (f['field'], f['value'], _short(f['quote'], 120)))
        if not write:
            print('Сухой прогон. Запись — с ключом --write.')
            return 0
        save_entries(entries)
        print('Записано: %d.' % len(entries))
        return 0
    summary(state)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
