# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gfa1163ce (Леонид Федун
продал 10% акций «Лукойла» компании): дельта-поиск разрешил кажущееся
противоречие дат (сделка реально прошла «в начале 2025 года», публично
известна стала только 25 ноября 2025 через Reuters — это совпадающая
формулировка всех независимых источников, а не ошибка карточки) и нашёл
официальное решение совета директоров «Лукойла» о погашении акций (29
августа 2025) — первичный источник вместо только вторичных пересказов.
Не через review.py: цитаты из ТРЁХ новых источников (lukoil.ru,
themoscowtimes.com, kommersant.ru) в разных полях.

Запуск: python3 pipeline/fix_fedun_lukoil_context_extend.py
        python3 pipeline/fix_fedun_lukoil_context_extend.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gfa1163ce'

OLD_VAL = '—'
NEW_VAL = (
    'Оценка ≈$7 млрд принадлежит Reuters и рассчитана по рыночной цене '
    'пакета — неясно, была ли эта сумма реально выплачена. Ни «Лукойл», '
    'ни сам Федун сделку официально не подтвердили: «Лукойл» дважды '
    'отказался от комментариев.'
)

OLD_CONTEXT = (
    'Леонид Федун в течение 26 лет занимал пост вице-президента '
    '«Лукойла», с 1996 по 2022 год. Он ушел из компании в связи с '
    '«достижением пенсионного возраста и семейными обстоятельствами», '
    'сообщал «Лукойл» в июне 2022-го. Вскоре после этого нефтяная '
    'компания купила футбольный клуб «Спартак», основным акционером '
    'которого был Федун.'
)
CONTEXT_ADDITION = (
    ' 29 августа 2025 года совет директоров «Лукойла» принял решение о '
    'погашении квазиказначейских акций в количестве не более 76 млн '
    'штук, приобретённых организациями группы в 2024-2025 годах. По '
    'данным Reuters, Вагит Алекперов сохраняет неформальное влияние на '
    '«Лукойл», тогда как Федун полностью вышел из операционной '
    'деятельности компании.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['lukoil.ru', 'https://lukoil.ru/PressCenter/Pressreleases/Pressrelease/sovet-direktorov-pao-lukoil-prinial-reshenie-po'],
    ['themoscowtimes.com', 'https://www.themoscowtimes.com/2025/11/26/lukoil-co-founder-leonid-fedun-sells-back-his-stake-in-company-a91243'],
    ['kommersant.ru', 'https://www.kommersant.ru/doc/8230610'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['val'] == OLD_VAL
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.val: станет ===')
    print(NEW_VAL)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['val'] = NEW_VAL
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
