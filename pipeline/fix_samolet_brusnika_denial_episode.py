# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g003e4867 (ГК «Самолет»/
«Рублевские кварталы» → «Брусника»): найден предшествующий эпизод, не
попавший в карточку. За полтора месяца до подтверждённой сделки (16
сентября 2025) «Брусника» публично ОПРОВЕРГАЛА переговоры об этом же
активе (Движение.ру, 31.07.2025) — обычная динамика M&A-переговоров, но
факт, который не был известен читателю карточки.

Не через review.py: существующий текст `eco.context` (о падении прибыли
«Самолета») взят из Коммерсанта, а новый факт — из независимого источника
(dvizhenie.ru); объединение фактов из РАЗНЫХ источников в одном поле
review.py не проверяет (правка сравнивает два источника, а не дословную
цитату одного).

Проверено отдельно: RIA Novosti (realty.ria.ru), которое выглядело как
второй независимый источник, на деле — прямой пересказ ТОГО ЖЕ
Коммерсанта («сообщила газета "Коммерсант"») и содержит собственную
опечатку (300 тыс. кв. м → «около 30 тысяч квадратных метров») — не
использовано ни как источник, ни как повод усомниться в цифре 300 тыс.
кв. м, которая дословно стоит в первоисточнике (Коммерсанте).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g003e4867'
OLD_CONTEXT = ('Продажа объясняется падением финансовых показателей '
               '«Самолета»: в первом полугодии 2025 года чистая прибыль '
               'компании снизилась в 2,6 раза год к году, до 1,8 млрд '
               'руб.')
NEW_CONTEXT = (OLD_CONTEXT + ' За полтора месяца до объявления сделки '
               '«Брусника» публично опровергала переговоры об этом '
               'активе: «Информация о покупке не соответствует '
               'действительности. Мы рассматриваем эту землю в '
               'качестве актива, но никакой сделки с «Самолетом» мы не '
               'заключили».')


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += эпизод опровержения переговоров "
          "(31.07.2025, dvizhenie.ru)")
    deal['eco']['context'] = NEW_CONTEXT

    src_urls = [s[1] for s in deal.get('src', [])]
    new_src = ['Движение.ру', 'https://dvizhenie.ru/media/4089/v-brusnike-'
               'oprovergli-pokupku-chasti-proekta-rublevskie-kvartaly-u-'
               'samoleta']
    if new_src[1] not in src_urls:
        deal['src'].append(new_src)
        print(f"{CARD_ID} src: += Движение.ру")

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
