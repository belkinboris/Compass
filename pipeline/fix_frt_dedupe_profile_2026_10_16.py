# -*- coding: utf-8 -*-
"""Второй прогон accept_card.py --apply для gba764f10 (та же сессия, та же
находка «родовое описание») создал ВТОРОЙ профиль для того же юрлица
(g54e5778a, ИНН 7704446429 — тот же, что у уже исправленного g6921da17),
потому что ответ в acceptance-файле ещё просил завести профиль, а не
привязать существующий. Снимает дубль: убирает g54e5778a из companies и
fns_registry, возвращает seller_id карточки на g6921da17, ставит штамп
accepted вручную (пост с правильным профилем уже чист — проверено
accept_card.py --queue перед записью этого скрипта).

ДОПОЛНЕНИЕ (после первого --write): test_data.py::
test_match_keys_point_to_existing_profiles поймал осиротевший ключ
match_keys['g54e5778a'] — accept_card.py пишет match_keys при создании
профиля, и этот скрипт изначально его не трогал. Удалён тем же прогоном
ниже (идемпотентно — если ключа уже нет, просто пропускается).

Запуск:
    python3 pipeline/fix_frt_dedupe_profile_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_frt_dedupe_profile_2026_10_16.py --write    # применить
"""
import json
import sys
from datetime import date

DATA = '/home/user/Compass/static/data/deals_promoted.json'
PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'gba764f10'
KEEP_ID = 'g6921da17'
DROP_ID = 'g54e5778a'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    assert DROP_ID in data['companies'], '%s уже не в companies — перечитайте' % DROP_ID
    assert KEEP_ID in data['companies'], '%s пропал из companies' % KEEP_ID
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = {c['id']: c for c in pending['cards']}[CARD_ID]
    assert card.get('seller_id') == DROP_ID, 'seller_id уже не %r: %r' % (DROP_ID, card.get('seller_id'))
    print('companies: удаляю дубль %s (оставляю %s)' % (DROP_ID, KEEP_ID))
    if DROP_ID in data.get('match_keys', {}):
        print('match_keys: удаляю осиротевший ключ %s' % DROP_ID)
    print('fns_registry.py: удаляю запись %s' % DROP_ID)
    print('%s: seller_id %r -> %r' % (CARD_ID, DROP_ID, KEEP_ID))
    print('%s: accepted <- %s' % (CARD_ID, date.today().isoformat()))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(DATA, encoding='utf-8'))
    assert DROP_ID in fresh['companies'], '%s поменяли параллельно — перечитайте' % DROP_ID
    del fresh['companies'][DROP_ID]
    fresh.get('match_keys', {}).pop(DROP_ID, None)
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    fresh_pending = json.load(open(PENDING, encoding='utf-8'))
    fc = {c['id']: c for c in fresh_pending['cards']}[CARD_ID]
    assert fc.get('seller_id') == DROP_ID, 'seller_id поменяли параллельно — перечитайте'
    fc['seller_id'] = KEEP_ID
    fc['accepted'] = date.today().isoformat()
    json.dump(fresh_pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    registry_path = '/home/user/Compass/pipeline/fns_registry.py'
    text = open(registry_path, encoding='utf-8').read()
    block = ("\n# Приёмка карточки gba764f10 — 2026-10-16 (pipeline/ingest/accept_card.py).\n"
             "REGISTRY += [\n"
             "    {\"company_id\": '%s', \"decision\": \"confirmed\", \"inn\": '7704446429',\n"
             "     \"reason\": 'Приёмка карточки gba764f10 (2026-10-16): юрлицо Публично-правовая "
             "компания «Фонд развития территорий» названо читателем, ИНН подтверждён точным "
             "совпадением имени в ЕГРЮЛ (единственное действующее юрлицо).',\n"
             "     \"date\": '2026-10-16'},\n"
             "]\n") % DROP_ID
    assert block in text, 'блок реестра ИНН для %s не найден в ожидаемом виде — правьте вручную' % DROP_ID
    text = text.replace(block, '\n', 1)
    open(registry_path, 'w', encoding='utf-8').write(text)

    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
