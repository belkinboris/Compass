# -*- coding: utf-8 -*-
"""Карточка rosatom-mali («Росатом купил малийскую компанию...»): второе
чтение нашло две находки.

1. law.struct несла фразу о лицензии Moketi Mining SARL (с июля 2024,
дочка Uranium One Group / структуры Росатома) — тот же факт уже в
eco.context, и в law.struct он создает нестыковку (неясно, купленная
компания — это Moketi Mining или другая, местная): убрана дублирующая и
путающая фраза, факт остается только в eco.context.
2. src ставил Интерфакс первым источником в посте, хотя статья Интерфакса
(29.05.2026, про геологоразведку) ничего не говорит о покупке компании;
единственный источник, подтверждающий сам факт покупки, — ПРАЙМ
(30.10.2026, цитата Лихачева). Переставлен первым, Интерфакс и Нефтегаз —
фон.

Запуск:
    python3 pipeline/fix_rosatom_mali_second_reading_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_rosatom_mali_second_reading_2026_11_24.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
CARD_ID = 'rosatom-mali'
OLD_STRUCT = ('Название купленной компании, ее прежних владельцев и долю Росатом не раскрыл. '
              'Разрешение на добычу на Бугуле с июля 2024 года принадлежит Moketi Mining SARL — '
              'дочерней компании Uranium One Group, структуры Росатома.')
NEW_STRUCT = 'Название купленной компании, ее прежних владельцев и долю Росатом не раскрыл.'
NEW_SRC = [
    ['ПРАЙМ', 'https://1prime.ru/20261030/rosatom-874832259.html'],
    ['Интерфакс', 'https://www.interfax.ru/business/1092728'],
    ['Neftegaz.ru', 'https://neftegaz.ru/news/Geological-exploration/857026-mali-zhdet-geologov-iz-rossii-dlya-razvedki-mestorozhdeniy-litiya-nefti-i-gaza/'],
]


def apply(data):
    card = next(c for c in data['deals'] if c['id'] == CARD_ID)
    assert card['law']['struct'] == OLD_STRUCT, 'law.struct уже изменен кем-то другим'
    card['law']['struct'] = NEW_STRUCT
    assert len(card['src']) == 3, 'состав src уже изменен кем-то другим'
    card['src'] = NEW_SRC


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    print('law.struct и src обновлены')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv[1:]))
