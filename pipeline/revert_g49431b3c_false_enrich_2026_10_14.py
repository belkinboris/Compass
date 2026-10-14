# -*- coding: utf-8 -*-
"""`enrich.py --write` (шаг 13, прогон 14 октября 2026, ~13:20 МСК) дописал
в `src` карточки `g49431b3c` («Дом.РФ» выставит на торги особняк барона
Штиглица в Петербурге) ссылку на статью РИА Недвижимость про СОВСЕМ ДРУГОЙ
лот «Дом.РФ» — аукцион права на КРТ участка в Петра Дубраве (Самарская
область), под который уже собрана отдельная карточка `g420352ff`. Совпали
только «Дом.РФ» (организатор торгов у обоих) и общие слова «выставил на
торги» — тот же класс дефекта матчера, что уже чинился для Азимут/Ярославль
(три раза, 13–14 октября), только здесь сработал сигнал «имя в кавычках»
(обычно надёжный, 0,7% ошибок по замеру в докстроке `enrich.py`) —
именно этот случай и есть одна из тех ошибок.

Откатывает ссылку из `src` и чистит пустую запись в `data/inbox/updates/
2026-10-14.json` (notify был false, изменений в посте не было — откатывать
больше нечего).

Запуск:
    python3 pipeline/revert_g49431b3c_false_enrich_2026_10_14.py            # сухой прогон
    python3 pipeline/revert_g49431b3c_false_enrich_2026_10_14.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
UPDATES = '/home/user/Compass/data/inbox/updates/2026-10-14.json'
CARD_ID = 'g49431b3c'
BAD_URL = 'https://realty.ria.ru/20261014/samara-2124434687.html'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    src = card.get('src') or []
    match = [s for s in src if len(s) > 1 and s[1] == BAD_URL]
    assert match, 'ссылки нет в src — уже откатано?'

    print('УБИРАЕМ из %s src: %r' % (CARD_ID, match))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_card = next(d for d in fresh['deals'] if d['id'] == CARD_ID)
    fresh_src = fresh_card.get('src') or []
    if not any(len(s) > 1 and s[1] == BAD_URL for s in fresh_src):
        print('кто-то уже откатил — перечитайте')
        return 1
    fresh_card['src'] = [s for s in fresh_src if not (len(s) > 1 and s[1] == BAD_URL)]
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    upd = json.load(open(UPDATES, encoding='utf-8'))
    upd['updates'] = [u for u in upd.get('updates', []) if u.get('deal_id') != CARD_ID]
    json.dump(upd, open(UPDATES, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
