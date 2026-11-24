# -*- coding: utf-8 -*-
"""Карточка rosatom-mali: eco.context несла перепутанную по смыслу фразу
«...разрешило передать Moketi Mining SARL из Uranium One Group» — по
источнику (Министерство горнодобывающей промышленности Мали «одобрило
передачу разрешения на добычу лития ... компании Moketi Mining SARL,
дочке структуры Росатома Uranium One Group») разрешение передали Moketi
Mining SARL (дочерней структуре Uranium One Group), а не «из» нее —
второе чтение верно поймало обратный смысл.

Запуск:
    python3 pipeline/fix_rosatom_mali_eco_context_direction_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_rosatom_mali_eco_context_direction_2026_11_24.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
CARD_ID = 'rosatom-mali'
OLD = ('Литиевый проект в малийском регионе Сикасо Россия и Мали ведут с марта 2023 года. Летом '
       '2023 года Владимир Путин говорил, что дочерней компании Росатома принадлежат 75% активов '
       'проекта. Права на Бугулу горное министерство Мали в июле 2024 года разрешило передать '
       'Moketi Mining SARL из Uranium One Group.\n\nПо отчету АО «Атомэнергопром» за 2025 год, '
       'геологоразведка предварительно подтвердила потенциал участка. По словам Алексея Лихачева, '
       'первый этап изысканий удвоил запасы месторождения — до более чем 400 тыс. т литиевого '
       'концентрата. Строительство горно-обогатительного комбината в Мали Росатом намерен начать '
       'в 2028 году.')
NEW = ('Литиевый проект в малийском регионе Сикасо Россия и Мали ведут с марта 2023 года. Летом '
       '2023 года Владимир Путин говорил, что дочерней компании Росатома принадлежат 75% активов '
       'проекта. Права на добычу на Бугуле горное министерство Мали в июле 2024 года разрешило '
       'передать компании Moketi Mining SARL — дочерней структуре Uranium One Group.\n\nПо отчету '
       'АО «Атомэнергопром» за 2025 год, геологоразведка предварительно подтвердила потенциал '
       'участка. По словам Алексея Лихачева, первый этап изысканий удвоил запасы месторождения — '
       'до более чем 400 тыс. т литиевого концентрата. Строительство горно-обогатительного '
       'комбината в Мали Росатом намерен начать в 2028 году.')


def apply(data):
    card = next(c for c in data['deals'] if c['id'] == CARD_ID)
    assert card['eco']['context'] == OLD, 'eco.context уже изменен кем-то другим'
    card['eco']['context'] = NEW


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    print('eco.context обновлен')
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
