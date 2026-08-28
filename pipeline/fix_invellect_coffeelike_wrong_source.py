# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gf9df9712 (Invellect
приобрела 100% сети кофеен Coffee Like, октябрь 2024): найден и починен
источник о ДРУГОЙ сделке. Единственная ссылка в `src` вела на статью Forbes
№522054 — «Севергрупп» купила 19,91% платформы «Автостэлс» для запчастей
для иномарок (проверено: WebSearch и прямая проверка подтверждают, что
статья не содержит вообще ничего про Invellect или Coffee Like). При этом
`eco.val` уже правильно ссылался на Forbes («Сумма сделки могла составить
до 5 млрд рублей, пишет Forbes») — то есть факт был верным, а URL к нему
был подставлен от другой статьи (класс дефекта «источник о другой сделке»,
см. CLAUDE.md).

Починка: заменён на правильную статью Forbes (№523331, ровно по теме
«У основанной Аязом Шабутдиновым сети кофеен Coffee Like сменился
владелец» — WebFetch Forbes технически недоступен в этой сессии, отдаёт
закодированное GIF-изображение вместо текста, поэтому дословно не
процитирован, но тема и номер статьи подтверждены поиском однозначно) плюс
два НОВЫХ источника, прочитанных лично прямым WebFetch: cafe-future.ru
(структура сделки, две ступени: 3,95% в сентябре + 96,05% в октябре 2024,
что уже совпадает с полем `extra`) и AdIndex (более точный диапазон оценки
— «от 1,5 до 5 млрд руб.», а не только верхняя граница).

Запуск: python3 pipeline/fix_invellect_coffeelike_wrong_source.py
        python3 pipeline/fix_invellect_coffeelike_wrong_source.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf9df9712'

WRONG_URL = 'https://www.forbes.ru/biznes/522054-severgrupp-kupila-19-91-platformy-dla-pokupki-zapcastej-dla-inomarok-avtostels'

OLD_SRC = [['Forbes', WRONG_URL]]
NEW_SRC = [
    ['Forbes', 'https://www.forbes.ru/svoi-biznes/523331-u-osnovannoj-aazom-sabutdinovym-seti-kofeen-coffee-like-smenilsa-vladelec'],
    ['FoodService', 'https://www.cafe-future.ru/news/gruppa-kompaniy-invellect-vykupila-biznes-seti-kofeen-coffee-like/'],
    ['AdIndex', 'https://adindex.ru/news/marketing/2024/10/18/326558.phtml'],
]

OLD_VAL = 'Сумма сделки могла составить до 5 млрд рублей, пишет Forbes.'
NEW_VAL = (
    'Сумма сделки могла составить до 5 млрд рублей, пишет Forbes. По '
    'данным AdIndex, диапазон оценки шире: «Предполагается, что она может '
    'составлять от 1,5 до 5 млрд руб.».'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['src'] == OLD_SRC, f'src изменился: {deal["src"]}'
    assert deal['eco']['val'] == OLD_VAL

    print('=== src: было ===')
    print(OLD_SRC)
    print('=== src: станет ===')
    print(NEW_SRC)
    print('=== eco.val: станет ===')
    print(NEW_VAL)

    if write:
        deal['src'] = NEW_SRC
        deal['eco']['val'] = NEW_VAL
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
