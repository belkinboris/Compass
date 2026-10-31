# -*- coding: utf-8 -*-
"""Приток, 12 сентября 2026: у карточки «Полекс» (gbf6f6432) в `law.adv`
был только консультант ПОКУПАТЕЛЯ (ЛКП). Telegram-канал ALUMNI Partners
(alumnimna, пост от июля 2026, найден притоком 12.09.2026) прямо называет
себя консультантом ПРОДАВЦА: «ALUMNI Partners консультировала продавца в
связи с продажей группы компаний «Полекс Урал»» — фраза дословно взята из
заголовка поста (он же — единственный источник, других предложений в
черновике нет). Источник дописан в `src`.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gbf6f6432'

OLD_ADV = [
    ["Юридический консультант покупателя", "Лемчик, Крупский и Партнеры (ЛКП)",
     "Комплексное сопровождение покупателя — due diligence, структурирование, "
     "подготовка документации, переговоры и закрытие сделки. Источник: lkpconsult.ru"],
]

NEW_ADV_ENTRY = [
    "Консультант продавца",
    "ALUMNI Partners",
    "«ALUMNI Partners консультировала продавца в связи с продажей группы компаний "
    "«Полекс Урал»». Источник: t.me/alumnimna/287",
]

NEW_SOURCE = ["ALUMNI Partners (Telegram)", "https://t.me/alumnimna/287"]


def main(write):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    assert card['law']['adv'] == OLD_ADV, 'law.adv уже другое'
    assert NEW_SOURCE not in card['src'], 'источник уже есть'

    card['law']['adv'] = OLD_ADV + [NEW_ADV_ENTRY]
    card['src'] = card['src'] + [NEW_SOURCE]

    print('Обновлено:', CARD_ID)
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('Сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    import sys
    main('--write' in sys.argv)
