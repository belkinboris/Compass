# -*- coding: utf-8 -*-
"""Партия 2 разбора @LawFirms: три карточки, которым пост даёт факт.

ЗАЧЕМ. Продолжение партии 1 (посты 16–30 канала). Из пятнадцати объявлений
восемь сделок уже были в базе, и у пяти из них консультанты стояли полностью
— но у трёх пост давал то, чего в карточке не было.

САМАЯ ВАЖНАЯ ИЗ ТРЁХ — «Рив Гош». У карточки в поле «Финансовый консультант»
стояло «Не привлекался», а объявление ДГП прямо пишет: «Финансовым
консультантом сделки выступила инвестиционно-банковская группа Aspring
Capital». Это не пустое поле, а НЕВЕРНОЕ: база утверждала отсутствие факта,
который был. Отдельный класс находки — обычно приток дополняет пустое и не
трогает заполненное, но «Не привлекался» это не факт, а заглушка того же
рода, что «Не раскрыта», и опровергается она источником.

ВТОРАЯ ЗАГЛУШКА — Ivideon/Sk Capital: «Стороны сделки — Не раскрывались»
против объявления VERBA LEGAL о сопровождении той же сделки. Строка не
дополняется, а заменяется, как и в партии 1.

ТРЕТЬЯ — Selectel: у карточки уже стоит ALUMNI Partners (сторона покупателя),
а White Square вела мажоритарного акционера Selectel, то есть третью сторону
той же сделки. Сумма (16 млрд ₽) в карточке уже есть и совпадает с постом —
не трогается.

Запуск:
    python3 pipeline/enrich_from_lawfirms_batch2.py            # сухой прогон
    python3 pipeline/enrich_from_lawfirms_batch2.py --write    # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_LABEL = 'РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ (@LawFirms)'

ADVISORS = [
    ('gad633118',
     'Юридический консультант мажоритарного акционера Selectel (Servertech Holding Ltd.)',
     'White Square',
     'Сопровождение Servertech Holding Ltd. в сделке по приобретению МКООО «Каталитик Пипл» '
     '25% акций Selectel у инвестиционных структур Геворка Вермишяна и прочих акционеров. '
     'Источник: https://t.me/LawFirms/10140',
     'https://t.me/LawFirms/10140',
     None,
     ['Юридический консультант']),
    ('g25db4ede',
     'Юридический консультант',
     'VERBA LEGAL',
     'Комплексное сопровождение сделки по выходу венчурного фонда Sk Capital из капитала '
     'Ivideon. Источник: https://t.me/LawFirms/9772',
     'https://t.me/LawFirms/9772',
     'Стороны сделки',
     ['Стороны сделки']),
]

# Отдельно от консультантов: поле «Финансовый консультант» — это `eco.finadv`,
# и здесь оно не пустое, а неверное. Проверка исходного состояния поэтому
# сравнивает со СТАРЫМ значением, а не с пустотой.
FINADV = [
    ('g94683ed2', 'Не привлекался',
     'Aspring Capital',
     'https://t.me/LawFirms/9989'),
]


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
            '%s: роли другие (%r), чем при чтении (%r)' % (did, [str(a[0]) for a in adv if a], before)
        assert url not in {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}, \
            '%s: объявление уже стоит в источниках' % did
        print('%s  %s' % (did, (deal.get('title') or '')[:60]))
        if drop:
            print('    убрать заглушку: %s' % drop)
        print('    + %s — %s' % (role, firm))

    for did, was, now, url in FINADV:
        deal = by_id.get(did)
        assert deal is not None, 'карточки %s нет в базе' % did
        current = str((deal.get('eco') or {}).get('finadv') or '').strip()
        assert current == was, \
            '%s: «Финансовый консультант» сейчас %r, а не %r — решение принимать заново' % (
                did, current, was)
        print('%s  %s' % (did, (deal.get('title') or '')[:60]))
        print('    «Финансовый консультант»: %r -> %r' % (was, now))

    print('\nкарточек к правке: %d' % (len(ADVISORS) + len(FINADV)))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for did, role, firm, note, url, drop, before in ADVISORS:
        deal = by_id[did]
        law = deal.setdefault('law', {})
        law['adv'] = [a for a in (law.get('adv') or []) if not (drop and str(a[0]) == drop)]
        law['adv'].append([role, firm, note])
        deal.setdefault('src', []).append([SRC_LABEL, url])
    for did, was, now, url in FINADV:
        deal = by_id[did]
        deal.setdefault('eco', {})['finadv'] = now
        if url not in {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}:
            deal.setdefault('src', []).append([SRC_LABEL, url])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
