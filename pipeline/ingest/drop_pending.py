"""Выкинуть из очереди карточку, которая не сделка, — без вопроса владельцу.

Владелец 24 октября 2026, про 42 вопроса в консоли («Аукцион вещей Брижит
Бардо», «Единороссы получили 86% кресел», «Райан Рейнольдс купил паб»):
«Что за бред нам в консоль пришел? … раньше же все такое удалялось просто».

Раньше мусор отсеивался на шаге сырья (`raw_screen.py --drop`, рутина решает
сама). Эти 42 в 21 сентября — 14 октября проскочили сырье уже карточками
(`pending.json`), а у приемки (`accept_card.py`) есть только «принять» и
«придержать» — месяц они висели в «придержанных», а вечером 24 октября рутина
публикации, не имея права их выкинуть, отправила владельцу 42 вопроса.

Этот скрипт — то же «выкинуть», что кнопка владельца (`approve.py`, вердикт
`discard`): карточка уходит из очереди насовсем, адреса ее источников
запоминаются в `discarded_urls`, чтобы та же новость не вернулась под новым id.
Отметка `by: routine` отличает решение рутины от решения человека.

КОГДА МОЖНО: не сделка уверенно — знаменитости и личные покупки, сувениры и
аукционы вещей, выборы и политика, макростатистика, операции ЦБ с валютой,
закупки оборудования, иностранная сделка без российской стороны. Сомнение —
не выкидывать: один вопрос владельцу со СПИСКОМ, а не по сообщению на карточку
(`routines/publication.md`, приемка).

    python3 pipeline/ingest/drop_pending.py g1 g2 --reason "не сделка: …"          # сухой прогон
    python3 pipeline/ingest/drop_pending.py g1 g2 --reason "не сделка: …" --write
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')


def drop(pending, state, ids, reason, now):
    cards = {c['id']: c for c in pending['cards']}
    missing = [i for i in ids if i not in cards]
    assert not missing, 'нет в очереди: %s' % missing
    for i in ids:
        card = cards[i]
        for s in card.get('src') or []:
            if len(s) > 1 and str(s[1]).startswith('http'):
                state.setdefault('discarded_urls', {})[str(s[1])] = {
                    'id': i, 'title': card.get('title'), 'by': 'routine', 'reason': reason,
                    'at': now.isoformat(timespec='seconds')}
    pending['cards'] = [c for c in pending['cards'] if c['id'] not in set(ids)]
    return [cards[i] for i in ids]


def main(argv):
    write = '--write' in argv
    reason = argv[argv.index('--reason') + 1] if '--reason' in argv else ''
    assert reason.strip(), 'нужна причина: --reason "не сделка: …"'
    ids = [a for a in argv if a.startswith(('g', 'c')) and a not in (reason,) and not a.startswith('--')]
    pending = json.load(open(PENDING, encoding='utf-8'))
    state = promote.load_state()
    gone = drop(pending, state, ids, reason, datetime.now(timezone.utc))
    for c in gone:
        print('  ВЫКИНУТА  %-11s %s' % (c['id'], str(c.get('title'))[:70]))
    print('Выкинуто из очереди: %d, осталось в очереди: %d.' % (len(gone), len(pending['cards'])))
    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0
    pending_fresh = json.load(open(PENDING, encoding='utf-8'))   # перечитать прямо перед записью
    state = promote.load_state()
    drop(pending_fresh, state, ids, reason, datetime.now(timezone.utc))
    json.dump(pending_fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    promote.save_state(state)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
