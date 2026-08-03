# -*- coding: utf-8 -*-
"""Партия 3 разбора @LawFirms: пять карточек получают факт из объявления.

ЗАЧЕМ. Посты 28–40 канала. Здесь особенно хорошо видно то, ради чего канал и
разбирается: у четырёх карточек из пяти консультант либо не назван вовсе,
либо назван только с ОДНОЙ стороны, а объявление называет другую.

ЧТО ЗАПИСЫВАЕТСЯ ПО СУММЕ. Ровно одно значение: SPO «Озон Фармацевтика»
привлекло 2,8 млрд ₽ — это сказано об этой сделке и ни о чём другом.
У Outlet Village сумма НЕ трогается: в карточке стоит «8–9 млрд ₽ (по
оценке)», а SEAMLESS Legal пишет «совокупная рыночная стоимость объектов
около 20 млрд рублей» — это расхождение, а расхождение показывают человеку,
а не правят догадкой (правило `enrich.py`: заменить выверенное значение
догадкой хуже, чем не дописать).

ЗАГЛУШКИ, КОТОРЫЕ ОПРОВЕРГНУТЫ ИСТОЧНИКОМ. У «МЦ Эксперт» и у завода
«Масленица» стояло «Стороны сделки — Не раскрывались», и обе строки
заменяются именем фирмы, а не дополняются им.

Запуск:
    python3 pipeline/enrich_from_lawfirms_batch3.py            # сухой прогон
    python3 pipeline/enrich_from_lawfirms_batch3.py --write    # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_LABEL = 'РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ (@LawFirms)'

ADVISORS = [
    ('g833a29f6',
     'Юридический консультант продавца (ГК «Эксперт»)',
     'Nextons',
     'Сопровождение продажи ГК «Эксперт» 100% доли в ООО «МЦ Эксперт» — сети медцентров '
     'в 13 городах России. Источник: https://t.me/LawFirms/9031',
     'https://t.me/LawFirms/9031',
     'Стороны сделки',
     ['Стороны сделки']),
    ('g7596ae81',
     'Юридический консультант продавца (фонды группы Hines)',
     'Nextons',
     'Консультирование международных инвестиционных фондов группы Hines по всем аспектам '
     'продажи долей в обществах, владеющих Outlet Village Белая Дача и Outlet Village '
     'Пулково. Источник: https://t.me/LawFirms/8944',
     'https://t.me/LawFirms/8944',
     None,
     ['Юридический консультант покупателя (Кама Капитал)']),
    ('g1a475dee',
     'Юридический консультант инвестора (ПАО «Группа Аренадата»)',
     'NSP',
     'Сопровождение инвестиционной сделки ПАО «Группа Аренадата». '
     'Источник: https://t.me/LawFirms/8827',
     'https://t.me/LawFirms/8827',
     None,
     ['Юридический консультант ООО «Решения Гармония» (получателя инвестиций)']),
    ('g549ddd5a',
     'Антимонопольное сопровождение покупателя (ГК «ЭФКО»)',
     'BIRCH',
     'Сопровождение ГК «ЭФКО» в согласовании сделки с ФАС России: сбор документов, '
     'подготовка и подача ходатайства. Источник: https://t.me/LawFirms/9248',
     'https://t.me/LawFirms/9248',
     'Стороны сделки',
     ['Стороны сделки']),
]

# Поле, ссылка и ожидаемое текущее значение. Сумма правится только там, где
# объявление называет её ОБ ЭТОЙ сделке, а не о соседнем упоминании.
VALUES = [
    ('g09f78960', 'sum', 'Не раскрыта', '2,8 млрд ₽', 'https://t.me/LawFirms/9157'),
    ('g09f78960', 'eco.sum', 'Не раскрыта', '2,8 млрд ₽', 'https://t.me/LawFirms/9157'),
]


def read(deal, path):
    node = deal
    for part in path.split('.'):
        node = (node or {}).get(part)
    return node


def write_field(deal, path, value):
    parts = path.split('.')
    node = deal
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for did, role, firm, note, url, drop, before in ADVISORS:
        deal = by_id.get(did)
        assert deal is not None, 'карточки %s нет в базе' % did
        adv = (deal.get('law') or {}).get('adv') or []
        names = ' | '.join(str(a[1]) for a in adv if len(a) > 1).lower()
        assert firm.lower() not in names, '%s: %s уже записан' % (did, firm)
        assert [str(a[0]) for a in adv if a] == before, \
            '%s: роли другие (%r), чем при чтении' % (did, [str(a[0]) for a in adv if a])
        assert url not in {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}, \
            '%s: объявление уже стоит в источниках' % did
        print('%s  %s' % (did, (deal.get('title') or '')[:60]))
        if drop:
            print('    убрать заглушку: %s' % drop)
        print('    + %s — %s' % (role, firm))

    for did, path, was, now, url in VALUES:
        deal = by_id.get(did)
        assert deal is not None, 'карточки %s нет в базе' % did
        current = str(read(deal, path) or '').strip()
        assert current == was, '%s.%s сейчас %r, а не %r' % (did, path, current, was)
        print('%s  %s -> %r' % (did, path, now))

    print('\nправок: %d' % (len(ADVISORS) + len(VALUES)))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for did, role, firm, note, url, drop, before in ADVISORS:
        deal = by_id[did]
        law = deal.setdefault('law', {})
        law['adv'] = [a for a in (law.get('adv') or []) if not (drop and str(a[0]) == drop)]
        law['adv'].append([role, firm, note])
        deal.setdefault('src', []).append([SRC_LABEL, url])
    for did, path, was, now, url in VALUES:
        deal = by_id[did]
        write_field(deal, path, now)
        if url not in {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}:
            deal.setdefault('src', []).append([SRC_LABEL, url])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
