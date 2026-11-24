"""Лот на торгах без результата не должен дойти до консоли и сайта, даже если
стал лотом уже ПОСЛЕ ворот (24 ноября 2026).

Ворота (`promote.is_open_listing`) смотрят черновик. 24 ноября 2026 карточка
`g69f9b746` («Дом.РФ» выставил на торги имущество в Дмитрове) прошла их с
другим типом, чтение поставило «Продажа с торгов», приемка пропустила — и
владелец получил ее в консоль с проектом поста: «Мы же торги не выкладываем
вроде больше». Этот шаг забора снимает такие карточки из очереди и запоминает
адреса источников, чтобы новость не вернулась под новым id.

    python3 pipeline/ingest/purge_open_lots.py            # сухой прогон
    python3 pipeline/ingest/purge_open_lots.py --write
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import promote  # noqa: E402


def split(cards):
    """(остаются, снимаются)."""
    keep = [c for c in cards if not promote.is_open_listing(c)]
    gone = [c for c in cards if promote.is_open_listing(c)]
    return keep, gone


def remember(state, card, now):
    for s in card.get('src') or []:
        if len(s) > 1 and str(s[1]).startswith('http'):
            state.setdefault('discarded_urls', {})[str(s[1])] = {
                'id': card['id'], 'title': card.get('title'),
                'at': now.isoformat(timespec='seconds'), 'why': 'лот на торгах без результата'}


def main(argv):
    write = '--write' in argv
    pending = promote.load_pending()       # читается прямо перед записью
    keep, gone = split(pending.get('cards') or [])
    if not gone:
        print('Лотов на торгах без результата в очереди нет.')
        return 0
    for c in gone:
        print('  СНЯТ ЛОТ %s  %s' % (c['id'], str(c.get('title'))[:80]))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    state = promote.load_state()
    now = datetime.now(timezone.utc)
    for c in gone:
        remember(state, c, now)
    pending['cards'] = keep
    promote.save_pending(pending)
    promote.save_state(state)
    print('Снято лотов без результата: %d.' % len(gone))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
