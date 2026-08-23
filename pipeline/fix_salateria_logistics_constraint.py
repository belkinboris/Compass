# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gecec7266 (Фонд «Бумеранг
капитал» выкупил группу «Салатерия»): дельта-поиск нашёл независимый
скептический взгляд отраслевого издания на стратегию консолидации —
короткий срок годности и холодовая цепь физически ограничивают
масштабирование fresh-cut продукта до «федерального игрока». Остальные
факты статьи (оценки сделки, финансы 2024 года) — дословное повторение
уже записанного в eco.val/eco.target_fin, не новость. Не через review.py:
поле уже занято текстом из другого источника.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
logistics.ru.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gecec7266'
OLD_RATIONALE = (
    'Стратегия фонда предполагает создание крупного игрока на рынке '
    'салатных смесей для поставок в ритейл, гостиницы и заведения '
    'общепита (HoReCa). «Сделка по приобретению «Салатерии» позволит нам '
    'развиваться в европейской части России»,— заявил он «Ъ», добавив, '
    'что активы «Прованса» и «Салатерии» планируется консолидировать.'
)
ADDITION = (
    'Отраслевое издание для логистики оценивает эту стратегию скептично: '
    'рынок fresh-cut (нарезанные салаты/овощи) растёт не столько за счёт '
    'маркетинга, сколько за счёт способности обеспечить стабильное '
    'качество на коротком сроке годности и удержать себестоимость в '
    'холодовой цепи, и «именно здесь попытка построить «федерального '
    'игрока» сталкивается с физическими ограничениями продукта».'
)
NEW_RATIONALE = OLD_RATIONALE + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['rationale'] == OLD_RATIONALE, \
        f"eco.rationale: неожиданное значение {deal['eco']['rationale']!r}"

    print(f"{CARD_ID} eco.rationale: += скепсис логистического издания о масштабировании")
    deal['eco']['rationale'] = NEW_RATIONALE

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
