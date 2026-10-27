# -*- coding: utf-8 -*-
"""`triage.py` каждый день заново сопоставляет сегодняшнее сырье с базой —
и каждый раз снова связывает статью про аукцион «Дом.РФ» на право КРТ в
Петра Дубраве с ЧУЖОЙ карточкой (особняк Штиглица, `g49431b3c`: общее
только организатор торгов «Дом.РФ» в кавычках и два общих слова) —
`enrich.py --write` в прогоне 13:20 МСК уже один раз дописал туда этот
источник по ошибке (откат — `revert_g49431b3c_false_enrich_2026_10_14.py`,
KNOWN_ISSUES.md). Сюжет уже собран своей карточкой `g420352ff`, которая
этот же источник уже несет.

Правит ТОЛЬКО сегодняшний файл разбора (`data/inbox/triage/<дата>.json`,
не код матчера и не базу): вердикт на эту статью меняется с
`enrich:g49431b3c` на `enrich:g420352ff` — у второй карточки этот URL уже
есть в `src`, так что `enrich.py` увидит «источник уже известен» и просто
ничего не допишет, вместо того чтобы повторно уйти в чужую карточку на
каждом следующем прогоне сегодняшнего дня.

Запуск:
    python3 pipeline/fix_triage_samara_krt_verdict_2026_10_14.py            # сухой прогон
    python3 pipeline/fix_triage_samara_krt_verdict_2026_10_14.py --write    # применить
"""
import json
import sys

PATH = '/home/user/Compass/data/inbox/triage/2026-10-14.json'
URL = 'https://realty.ria.ru/20261014/samara-2124434687.html'
OLD_VERDICT = 'enrich:g49431b3c'
NEW_VERDICT = 'enrich:g420352ff'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    item = next((x for x in data['items'] if x.get('url') == URL), None)
    assert item, 'записи про эту статью в сегодняшнем разборе нет'
    assert item.get('verdict') == OLD_VERDICT, item.get('verdict')

    print('ПРАВКА вердикта: %r -> %r' % (OLD_VERDICT, NEW_VERDICT))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PATH, encoding='utf-8'))
    fresh_item = next(x for x in fresh['items'] if x.get('url') == URL)
    if fresh_item.get('verdict') != OLD_VERDICT:
        print('кто-то уже поправил — перечитайте')
        return 1
    fresh_item['verdict'] = NEW_VERDICT
    json.dump(fresh, open(PATH, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
