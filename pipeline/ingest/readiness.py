"""Готовность карточки к консоли и каналу — одно место (H3 аудита кода, 31 октября 2026).

До этого дня «карточка готова» было записано в восьми местах с разными
условиями: send_drafts.build_plan и его «ТУПИК», approve.plan_actions и его
«ТУПИК», accept_card.queue, second_reading.needs_second_reading, своя копия в
ops_status и две в main.py. Они расходились: approve не знал о втором чтении
(принятая после 9 октября без второго чтения печаталась «ТУПИК» и «ждем
решения», хотя ждала приток), три копии needs_second_reading по-разному
читали нестроковую `accepted`, send_drafts не смотрел `held`/`hold_reason`.

    from readiness import state, needs_second_reading, hours_pending, is_shown

`state(card)` отвечает, ЧЕГО карточка ждет, — одно слово по приоритету:

    held            — владелец придержал: ждет его решения
    doubted         — приемка не пропустила (`hold_reason` без `held`): ждет
                      решения человека, по молчанию не выходит никогда
    unreviewed      — не прочитана против источника (review.py)
    accepted_unread — принята, но не прочитана: тупик, а не очередь (OTP Bank,
                      4 октября 2026) — review.py --mark-read
    unaccepted      — прочитана, приемки нет (accept_card.py)
    unread2         — принята с SECOND_READING_SINCE, второго чтения нет и в
                      консоли не показана (second_reading.py)
    stale           — принята, но после приемки содержимое изменилось, а в
                      консоли ее еще не показали: переприемка (accept_card.py)
    ready_unsent    — все есть, в консоли не показана: send_drafts.py --write
    reshow          — показана, потом поправлена и заново принята и прочитана:
                      send_drafts.py --write покажет новую версию с пометкой
                      «поправили» (бэклог D7, 7 ноября 2026)
    shown           — показана в консоли (draft_sent): ждет решения (молчание
                      не публикует с 12.11.2026; через сутки — напоминание в личку)

Правка ПОКАЗАННОЙ, но не опубликованной карточки (D7, 7 ноября 2026; 6 ноября
«Островной», «Циан», Омск, «Хогвартс», «Сезон» проводили руками): текст,
который видел владелец, — `shown_hash` (ставит send_drafts при показе; у
показанных раньше — `accepted_hash`, его `stamp_hash` переносит в
`shown_hash` перед переприемкой). Разошелся — карточка снова `stale` →
`unread2` → `reshow`, молчание ее не публикует. У опубликованной отметок
показа нет (approve их снимает) — ее ведет вычитка (`changed_after_check`).

Штамп привязан к содержимому, пока карточку не показали (H4, 31 октября
2026). Решение владельца (docs/card_acceptance.md; устройство — docs/card_readiness.md): правка качества штамп не
снимает — поэтому отпечаток важен только ДО первого показа или публикации.
`fingerprint(card, comps)` — sha1 над нормализованным текстом полей, которые
читал принимающий (заголовок, тип, статус, даты, сумма, стороны, предмет,
консультанты, все строки eco.* и law.*, extra, события, имена профилей
сторон); НЕ входят источники, штампы, заметки приемки, вычитка, снимок поста
и отметки консоли. `accept_card.apply_answer` пишет `accepted_hash`,
`second_reading.apply` — `second_read_hash`. Разошелся `accepted_hash` на
непоказанной карточке — `stale`, ее берут заново приемка и консоль не
показывает; разошелся `second_read_hash` — снова `unread2`. Без хеша (старые
штампы) карточка свежей не считается несвежей — хеши ставит
pipeline/backfill_stamp_hashes_2026_10_31.py. Отпечаток двухчастный:
«поля.имена» — без справочника компаний сравнивается только часть полей
(ops_status и консоль читают один pending.json).

Показанность (`is_shown`) — отдельный признак: карточка, показанная до того,
как гейты стали обязательными, все равно числится `unreviewed`, потому что
ждет именно чтения; молчание ее не публикует (approve), а консоль не шлет
заново только то, что уже отправлено.

Кто зовет: send_drafts.build_plan (не показывает ничего, кроме ready_unsent;
его «ТУПИК» — accepted_unread), approve.plan_actions (молчание публикует только
shown; текст ожидания — по состоянию; его «ТУПИК» — ready_unsent),
accept_card.queue (unaccepted, unreviewed), second_reading.queue (unread2),
ops_status.queue_counts (Counter по состояниям), main._send_queue_batch.
Модуль без зависимостей: его импортирует и main.py.
"""
import hashlib
import json
import re
from datetime import datetime, timezone

SECOND_READING_SINCE = '2026-10-09'      # принятые с этого дня без второго чтения в консоль не идут
ACCEPTED, SECOND_READ = 'accepted', 'second_read'

STATES = ('held', 'doubted', 'unreviewed', 'accepted_unread', 'unaccepted',
          'stale', 'unread2', 'ready_unsent', 'reshow', 'shown')
# Карточка ждет приток (чтение, приемку, второе чтение), а не человека.
WAITING_INTAKE = frozenset({'unreviewed', 'accepted_unread', 'unaccepted', 'stale', 'unread2'})
# Чего ждет непоказанная карточка (молчание не публикует ничего с 12.11.2026).
WAIT_TEXT = {
    'unreviewed': 'не прочитана против источника',
    'accepted_unread': 'принята, но не прочитана против источника (review.py --mark-read)',
    'unaccepted': 'не прошла приемку (accept_card.py)',
    'stale': 'переприемка после правок (accept_card.py)',
    'unread2': 'ждет второго чтения (second_reading.py)',
    'ready_unsent': 'в консоли не показана (send_drafts.py --write)',
    'reshow': 'поправлена после показа, новая версия в консоли еще не показана (send_drafts.py --write)',
    'doubted': 'приемка не пропустила — ждет вашего решения',
    'held': 'придержана ранее — ждет ручного решения',
}


def is_shown(card):
    """Показана в консоли: карточка (🗂) или проект поста (📣) ушли владельцу."""
    return bool(card.get('draft_sent') or card.get('post_draft_sent'))


def _accepted_day(card):
    """Дата приемки строкой или None: у старых фикстур `accepted: True`/'d' —
    не дата, они идут по-старому, без второго чтения."""
    acc = card.get(ACCEPTED)
    return acc if isinstance(acc, str) and acc[:4].isdigit() else None


def needs_second_reading(card, comps=None):
    """Принята с SECOND_READING_SINCE и еще не прочитана второй раз — или
    прочитана, но с тех пор содержимое изменилось (`second_read_hash`
    разошелся). Одно определение на всех (раньше — три с разной трактовкой
    нестроковой `accepted`). Показанность здесь не учитывается — ее решает
    `state`."""
    acc = _accepted_day(card)
    if not (acc and acc >= SECOND_READING_SINCE):
        return False
    if not card.get(SECOND_READ):
        return True
    return not hash_matches(card.get(SECOND_READ + '_hash'), fingerprint(card, comps))


def state(card, comps=None):
    if card.get('held'):
        return 'held'
    if card.get('hold_reason'):
        return 'doubted'
    if not card.get('reviewed'):
        return 'accepted_unread' if card.get(ACCEPTED) else 'unreviewed'
    if not card.get(ACCEPTED):
        return 'unaccepted'
    if is_shown(card):
        if not edited_after_shown(card, comps):
            return 'shown'
        # Поправлена после показа (D7): та же дорога, что у новой карточки —
        # приемка, второе чтение, потом показ новой версии.
        if not card.get(ACCEPTED + '_hash') or \
                not hash_matches(card.get(ACCEPTED + '_hash'), fingerprint(card, comps)):
            return 'stale'
        if needs_second_reading(card, comps):
            return 'unread2'
        return 'reshow'
    if is_stale(card, comps):
        return 'stale'
    if needs_second_reading(card, comps):
        return 'unread2'
    return 'ready_unsent'


# ---------------------------------------------------------------------------
# Отпечаток содержимого: штамп держится, пока карточку не показали

FINGERPRINT_FIELDS = ('title', 'type', 'status', 'date', 'date_basis', 'sum', 'sum_basis',
                      'asset', 'buyer', 'buyer_name', 'seller', 'seller_id', 'target', 'asset_id',
                      'advisers', 'extra')
PARTY_ID_FIELDS = ('buyer', 'seller_id', 'target', 'asset_id')


def _norm(v):
    """Текст с точностью до типографики: кавычки, тире, пробелы и регистр не
    в счет (сплошной типографский прогон не должен снимать штамп — та же
    мысль, что `review.typo_flat`)."""
    if v is None:
        return None
    if isinstance(v, dict):
        return {str(k): _norm(x) for k, x in sorted(v.items())}
    if isinstance(v, (list, tuple)):
        return [_norm(x) for x in v]
    return re.sub(r'[^\wа-яё]+', '', str(v), flags=re.I).lower()


def _sha(obj, n):
    return hashlib.sha1(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()[:n]


def fingerprint(card, comps=None):
    """«поля[.имена]»: 12 знаков над полями карточки и, если дан справочник
    компаний, еще 6 над именами профилей сторон (переименование профиля —
    тоже правка того, что читал принимающий)."""
    body = {f: _norm(card.get(f)) for f in FINGERPRINT_FIELDS}
    body['eco'] = _norm(card.get('eco') or {})
    body['law'] = _norm(card.get('law') or {})
    body['events'] = [(_norm(e.get('kind')), _norm(e.get('date')), _norm(e.get('title')))
                      for e in card.get('events') or [] if isinstance(e, dict)]
    h = _sha(body, 12)
    if comps is not None:
        names = [_norm((comps.get(card.get(k)) or {}).get('name')) if card.get(k) else None
                 for k in PARTY_ID_FIELDS]
        h += '.' + _sha(names, 6)
    return h


def hash_matches(stored, current):
    """Нет сохраненного хеша (старый штамп) — совпадает; часть имен
    сравнивается, только когда она есть у обоих."""
    if not stored:
        return True
    s_fields, _, s_names = str(stored).partition('.')
    c_fields, _, c_names = str(current).partition('.')
    return s_fields == c_fields and (not s_names or not c_names or s_names == c_names)


def edited_after_shown(card, comps=None):
    """Показана в консоли, и текст с тех пор изменился: сверка с `shown_hash`
    (что видел владелец), без него — с `accepted_hash` (показывают только
    принятую, и до D7 правка штамп не снимала). Ни того, ни другого — старый
    штамп, правку не отличить: False."""
    if not is_shown(card) or not card.get(ACCEPTED):
        return False
    ref = card.get('shown_hash') or card.get(ACCEPTED + '_hash')
    return bool(ref) and not hash_matches(ref, fingerprint(card, comps))


def stamp_hash(card, stamp, comps=None):
    """Отпечаток к штампу `stamp` (accepted / second_read). У показанной
    карточки без `shown_hash` прежний `accepted_hash` сначала переезжает в
    `shown_hash`: иначе после переприемки не узнать, что владелец видел
    другой текст, и новая версия в консоль не попадет."""
    if stamp == ACCEPTED and is_shown(card) and not card.get('shown_hash') and card.get(ACCEPTED + '_hash'):
        card['shown_hash'] = card[ACCEPTED + '_hash']
    card[stamp + '_hash'] = fingerprint(card, comps)


def is_stale(card, comps=None):
    """Принята, но содержимое с тех пор изменилось, а карточку еще не
    показали. Показанную ведет своя ветка `state` (`edited_after_shown`, D7);
    опубликованную — вычитка (`changed_after_check`)."""
    if is_shown(card) or not card.get(ACCEPTED):
        return False
    return not hash_matches(card.get(ACCEPTED + '_hash'), fingerprint(card, comps))


# ---------------------------------------------------------------------------
# Правка опубликованной карточки возвращает ее на проверку (2 ноября 2026)
#
# До этого дня отпечаток у показанной карточки был только информационным:
# правка качества штамп не снимала, и правки опубликованных карточек не
# проходили ни приемку, ни второе чтение. Так прошел октябрьский пересказ
# (76% базы) и ВТБ/«Деметра», где прогноз стал фактом. Решение владельца
# 2 ноября 2026: «Проверки должны быть всеобъемлющие, как когда карта
# создается». Карточка с сайта не снимается — она встает первой в очередь
# вычитки (pipeline/reread_queue.py, routines/reread.md), и вычитка ставит
# `reread_hash`. Совпадение с ЛЮБЫМ из сохраненных отпечатков значит: текст
# ровно тот, который кто-то проверил (или взят за точку отсчета
# `gate_baseline_hash` при включении правила).

CHECKED_HASHES = ('reread_hash', 'second_read_hash', 'accepted_hash', 'gate_baseline_hash')


def changed_after_check(card, comps=None):
    """Текст карточки не совпадает ни с одним проверенным. Без единого
    сохраненного отпечатка — False (точку отсчета ставит
    pipeline/gate_baseline_2026_11_02.py для всей базы)."""
    stored = [card.get(k) for k in CHECKED_HASHES if card.get(k)]
    if not stored:
        return False
    cur = fingerprint(card, comps)
    return not any(hash_matches(h, cur) for h in stored)


def hours_pending(card, now=None):
    """Сколько часов карточка ждет решения. Без `pending_since` отсчет идет от
    приемки или чтения (раньше без отметки часы стояли на нуле навсегда —
    Мадрид, Nestlé, «Ашан», три недели в «выйдут сами»)."""
    now = now or datetime.now(timezone.utc)
    stamp = card.get('pending_since') or card.get(ACCEPTED) or card.get('reviewed')
    try:
        since = datetime.fromisoformat(str(stamp))
    except ValueError:
        return 0.0
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    return (now - since).total_seconds() / 3600.0


def _self_check():
    assert state({}) == 'unreviewed'
    assert state({'accepted': '2026-10-01'}) == 'accepted_unread'
    assert state({'reviewed': 'd'}) == 'unaccepted'
    assert state({'reviewed': 'd', 'accepted': 'd'}) == 'ready_unsent'
    assert state({'reviewed': 'd', 'accepted': '2026-10-09'}) == 'unread2'
    assert state({'reviewed': 'd', 'accepted': '2026-10-08'}) == 'ready_unsent'
    assert state({'reviewed': 'd', 'accepted': '2026-10-09', 'second_read': '2026-10-09'}) == 'ready_unsent'
    assert state({'reviewed': 'd', 'accepted': '2026-10-09', 'draft_sent': True}) == 'shown'
    assert state({'reviewed': 'd', 'accepted': 'd', 'hold_reason': 'не сделка'}) == 'doubted'
    assert state({'held': True, 'hold_reason': 'x'}) == 'held'
    assert state({'draft_sent': True}) == 'unreviewed'
    assert set(WAIT_TEXT) == set(STATES) - {'shown'}
    comps = {'b1': {'name': 'ООО «Ромашка»'}}
    card = {'reviewed': 'd', 'accepted': '2026-10-20', 'second_read': '2026-10-20', 'buyer': 'b1',
            'eco': {'context': 'Актив продан — из-за долгов.'}}
    card['accepted_hash'] = card['second_read_hash'] = fingerprint(card, comps)
    assert state(card, comps) == 'ready_unsent' and state(card) == 'ready_unsent'
    typo = dict(card, eco={'context': 'Актив продан - из за долгов'})
    assert state(typo, comps) == 'ready_unsent', 'типографика штамп не снимает'
    edited = dict(card, eco={'context': 'Актив продан из-за санкций.'})
    assert state(edited, comps) == 'stale' and state(edited) == 'stale'
    assert state(dict(card, draft_sent=True), comps) == 'shown'
    shown_edited = dict(edited, draft_sent=True)
    assert state(shown_edited, comps) == 'stale', 'правка показанной — переприемка (D7)'
    stamp_hash(shown_edited, ACCEPTED, comps)
    assert shown_edited['shown_hash'] == card['accepted_hash']
    assert state(shown_edited, comps) == 'unread2'
    stamp_hash(shown_edited, SECOND_READ, comps)
    assert state(shown_edited, comps) == 'reshow' and state(shown_edited) == 'reshow'
    assert state(dict(shown_edited, shown_hash=fingerprint(shown_edited, comps)), comps) == 'shown'
    assert state({'reviewed': 'd', 'accepted': 'd', 'draft_sent': True, 'title': 'x'}) == 'shown', \
        'старый штамп без отпечатка — правку не отличить'
    renamed = dict(card)
    assert state(renamed, {'b1': {'name': 'ООО «Лютик»'}}) == 'stale' and state(renamed) == 'ready_unsent'
    reaccepted = dict(edited, accepted_hash=fingerprint(edited, comps))
    assert state(reaccepted, comps) == 'unread2', 'после переприемки — снова второе чтение'
    shown = dict(card, draft_sent=True)
    assert not changed_after_check(shown, comps)
    assert changed_after_check(dict(edited, draft_sent=True), comps), 'правка показанной — на проверку'
    assert not changed_after_check(dict(typo, draft_sent=True), comps)
    reread = dict(edited, reread_hash=fingerprint(edited, comps))
    assert not changed_after_check(reread, comps), 'вычитка снимает с очереди'
    assert not changed_after_check({'eco': {'context': 'x'}}), 'без отпечатков — не очередь'


_self_check()


def raw_key(title):
    """Ключ памяти о сырье — нормализованный заголовок (дословно как
    `promote.raw_key`; совпадение держит test_ingest)."""
    return re.sub(r'[^\wа-яё]+', '', str(title or ''), flags=re.I).lower()


def undecided_raw(drafts, state):
    """Сырье, которое действительно ждет человека: не решено ни по draft_id,
    ни по заголовку, не дубль внутри партии. ОДНО определение для отчета
    публикации (`ops_status.doubted_count`), кнопки «Сомнительные» и сводки
    очереди в консоли (`app/console.py`) и `raw_screen.undecided`.
    8 ноября 2026: отчет писал «Сомнительных: 33», а ждали решения 0 —
    счетчик и кнопка смотрели только `decided_raw` и не видели повторов
    одной новости, уже решенных по заголовку (`raw_titles`)."""
    state = state or {}
    decided_ids = set(state.get('decided_raw') or {})
    decided_titles = set(state.get('raw_titles') or {})
    return [d for d in drafts or []
            if str(d.get('draft_id')) not in decided_ids
            and raw_key(d.get('title')) not in decided_titles
            and not d.get('dup_in_batch')]

