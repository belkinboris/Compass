"""Карточка-двойник: новая карточка о сделке, которая уже есть в базе (13 ноября 2026).

13 ноября 2026 приток дважды за день довел до кнопки владельца карточку-дубль:
`g5540db5e` («К+» / «Комфорт» — та же статья «Ведомостей», дата и сумма, что у
`g93df6a58`) и `ga241b1af` («Библио-Глобус» — тот же профиль предмета и продавец,
что у открытой `g4afd35d0`). Ворота (`promote.near_duplicate`) смотрят только
черновик из разбора заголовка; карточку, собранную руками из отложенного
черновика или из сырья по кнопке «Это сделка», с базой не сверял никто, а
`test_data.py::test_no_duplicate_deal_cards` видит дубль, только когда он уже в
базе. Здесь — сверка готовой карточки с базой и очередью по ее полям; зовут
приемка (`accept_card.findings`, код `duplicate_card`) и показ в консоль
(`send_drafts.build_plan`).

Признаки пары и замер на базе (1773 сделки, все пары, 13 ноября 2026):
  U — общий адрес источника (src, discovery_src, источники этапов);
  T — тот же предмет: один профиль `target` или общее название в кавычках в
      предмете (с падежом: «Библио-Глобус» / «Библио-Глобуса»);
  B, S — тот же покупатель, продавец (id профиля или имя);
  $ — та же сумма (до 5%); D — даты не дальше 45 дней; OO — обе не закрыты.

  одиночные и слабые сочетания — не блокируют:
    U           469 пар — одна статья о нескольких сделках, указ о пяти активах;
    U+T          65 — статья о новой сделке пересказывает прошлую (Softline и
                      Polymatica 2022 и 2026), ни одного дубля;
    T+(B|S)      36 — серийный продавец или покупатель, пакеты по частям;
    T+B+S         3 — «Русагро» 25% и 77,5% «Агро-Белогорья», «Роснефть» часть и
                      остаток пакета «Башнефти», ТЦ «Аура» в Ярославле и в
                      Сургуте: все законные;
    U+T+D         3 — законные (Rockwool: управление и покупка);
  блокируют (RULES):
    U+$+D         1 пара — и это настоящий дубль (две карточки «Дом.РФ» о
                  семинарии в Краснодаре, g134d5b0e / g8ad8ce9d);
    T+(B|S)+$     0 пар;
    T+(B|S)+OO    1 пара («Росгосстрах» выставлен на продажу / WB может купить
                  долю у ВТБ — один процесс в двух карточках).
Оба случая 13 ноября ловятся: «К+» — первым и вторым, «Библио-Глобус» — вторым
и третьим. Сделка правда другая (второй пакет, новый покупатель) — находку
закрывает причина в `accepted_notes.checked.duplicate_card`.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import match as matcher  # noqa: E402

CODE = 'duplicate_card'
NEAR_DAYS = 45
SUM_TOLERANCE = 0.05


def url_key(url):
    """Адрес без схемы, www, меток перехода и хвостового слеша."""
    u = re.sub(r'^https?://(?:www\.)?', '', str(url or '').strip().lower()).split('#', 1)[0]
    if '?' in u:
        path, query = u.split('?', 1)
        keep = [q for q in query.split('&') if q and not re.match(r'(utm_\w+|from|%20tg|tg|ref)(=|$)', q)]
        u = path + ('?' + '&'.join(keep) if keep else '')
    return u.rstrip('/')


def _pairs(value):
    for s in value or []:
        if isinstance(s, (list, tuple)) and len(s) > 1 and s[1]:
            yield s[1]


def card_urls(card):
    out = set()
    for field in ('src', 'discovery_src'):
        out.update(url_key(u) for u in _pairs(card.get(field)))
    for ev in card.get('events') or []:
        if not isinstance(ev, dict):
            continue
        out.update(url_key(u) for u in _pairs([ev.get('source')]))
        out.update(url_key(u) for u in _pairs(ev.get('sources')))
    out.discard('')
    return out


def _keys(card, id_field, name_field, comps, match_keys):
    keys = set(matcher._profile_keys(card.get(id_field), comps, match_keys))
    key = matcher.entity_key(card.get(name_field))
    if key:
        keys.add(key)
    return keys


def features(card, comps=None, match_keys=None):
    """Признаки карточки. Ключи сторон считаются по требованию (`_party_keys`):
    они нужны только паре с общим адресом или предметом, а таких единицы."""
    comps = comps or {}
    target = card.get('target') or card.get('asset_id')
    target_name = (comps.get(target) or {}).get('name') if target else ''
    names = matcher.quoted(str(card.get('asset') or ''))
    if target_name:
        names |= matcher.quoted(str(target_name)) | matcher.quoted('«%s»' % target_name)
    return {
        'id': card.get('id'), 'title': card.get('title'), 'status': card.get('status'),
        'date': card.get('date'), 'urls': card_urls(card), 'target': target, 'names': names,
        'buyer': card.get('buyer'), 'seller': card.get('seller_id'),
        'amount': matcher.amount(card.get('sum')) or matcher.amount(card.get('title')),
        '_card': card, '_comps': comps, '_match_keys': match_keys,
    }


def _party_keys(row, role):
    key = role + '_keys'
    if key not in row:
        id_field, name_field = {'buyer': ('buyer', 'buyer_name'), 'seller': ('seller_id', 'seller')}[role]
        row[key] = _keys(row['_card'], id_field, name_field, row['_comps'], row['_match_keys'])
    return row[key]


def _agree(a, b):
    return any(matcher.entity_agree(x, y) for x in a for y in b)


def signs(a, b):
    """Множество признаков пары (буквы — в шапке модуля)."""
    out = set()
    if a['urls'] & b['urls']:
        out.add('U')
    if (a['target'] and a['target'] == b['target']) or matcher.quoted_common(a['names'], b['names']):
        out.add('T')
    if not out:
        return out          # без общего адреса и предмета ни одно правило не сработает
    if (a['buyer'] and a['buyer'] == b['buyer']) or _agree(_party_keys(a, 'buyer'), _party_keys(b, 'buyer')):
        out.add('B')
    if (a['seller'] and a['seller'] == b['seller']) or _agree(_party_keys(a, 'seller'), _party_keys(b, 'seller')):
        out.add('S')
    if a['amount'] and b['amount'] and \
            abs(a['amount'] - b['amount']) / max(a['amount'], b['amount']) < SUM_TOLERANCE:
        out.add('$')
    if matcher.days_between(a['date'], b['date']) <= NEAR_DAYS:
        out.add('D')
    if a['status'] in matcher.OPEN_STATUSES and b['status'] in matcher.OPEN_STATUSES:
        out.add('OO')
    return out


RULES = (
    (lambda s: {'U', '$', 'D'} <= s, 'та же статья в источниках, та же сумма и дата рядом'),
    (lambda s: 'T' in s and s & {'B', 'S'} and '$' in s, 'тот же предмет, та же сторона и та же сумма'),
    (lambda s: 'T' in s and s & {'B', 'S'} and 'OO' in s, 'тот же предмет и та же сторона, обе сделки еще не закрыты'),
)


def why(s):
    for rule, text in RULES:
        if rule(s):
            return text
    return None


_INDEX = {}


def _base_index(base):
    deals = base.get('deals') or []
    key = (id(deals), len(deals))
    if _INDEX.get('key') != key:
        _INDEX.clear()
        _INDEX['key'] = key
        _INDEX['rows'] = [features(d, base.get('companies'), base.get('match_keys')) for d in deals]
    return _INDEX['rows']


def twins(card, base, queue=()):
    """[(id, заголовок, где, почему)] — карточки базы и очереди о той же сделке.

    Опубликованная карточка (уже в базе) с собой и соседями не сверяется: это
    проверка НОВОЙ карточки перед показом; дубли внутри базы — docs/base_duplicates.md.
    """
    cid = card.get('id')
    if cid and any(d.get('id') == cid for d in base.get('deals') or []):
        return []
    rows = _base_index(base)
    me = features(card, base.get('companies'), base.get('match_keys'))
    out = []
    for where, others in (('в базе', rows),
                          ('в очереди', [features(c, base.get('companies'), base.get('match_keys'))
                                         for c in queue or () if c.get('id') != cid])):
        for row in others:
            reason = why(signs(me, row))
            if reason:
                out.append((row['id'], row['title'], where, reason))
    return out


def finding_text(found):
    """Одна находка приемки: кто двойник и что делать."""
    names = '; '.join('%s «%s» (%s: %s)' % (i, str(t or '')[:80], where, reason)
                      for i, t, where, reason in found[:3])
    first = found[0][0]
    return ('похоже, эта сделка уже есть: %s. Это та же сделка — новое дописать этапом или фактом в %s '
            '(docs/intake_run.md, raw_screen.py --enrich; docs/duplicates.md), а эту карточку снять '
            'drop_pending.py, новую не заводить; если сделка другая (другой пакет, другой покупатель) — '
            'закрыть находку причиной в checked.%s' % (names, first, CODE))


def blocked(card, base, queue=()):
    """Двойники, не закрытые причиной читателя (`accepted_notes.checked.duplicate_card`)."""
    if CODE in ((card.get('accepted_notes') or {}).get('checked') or {}):
        return []
    return twins(card, base, queue)
