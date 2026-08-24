# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g5880d206 (Игорь Ким/«Фольксваген банк
Рус»): дельта-поиск нашёл, что `eco.val` несёт факт СОВСЕМ ДРУГОЙ
сделки. Третий источник карточки, kommersant.ru/doc/8400478, — статья
про торговый центр «Метрополис» в Москве (переход управления к «ТПС
Недвижимости», оценка 60-65 млрд ₽ — Морган Стэнли выкупает объект за
$1,2 млрд) и не содержит ни слова о банке, Volkswagen или Игоре Киме.
Проверено дважды напрямую (WebFetch): первое предложение статьи —
«На рынке торговой недвижимости... юридически закрылась крупная
сделка», прямой вопрос подтвердил отсутствие упоминаний банка/
Volkswagen/Кима. Похоже на копипаст поля из другой карточки при вводе.

Снимаем `eco.val` (был заглушкой чужого факта, честная пустота лучше)
и убираем сам источник из `src` — он не подтверждает ни одного факта
этой карточки.

Запуск: python3 pipeline/fix_kim_volkswagen_bank_metropolis_misattribution.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g5880d206'

OLD_VAL = 'Оценивает «Метрополис» в 60–65 млрд руб.'
BAD_SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/8400478']


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['val'] == OLD_VAL, \
        f"eco.val: неожиданное значение {deal['eco']['val']!r}"
    assert BAD_SRC in deal['src'], \
        f"src: {BAD_SRC!r} не найден в {deal['src']!r}"

    print(f'{CARD_ID} eco.val: снимаем факт чужой сделки '
          f'(«Метрополис») — правильное значение «—»')
    print(f'{CARD_ID} src: убираем {BAD_SRC!r} — не подтверждает эту '
          f'сделку')

    if write:
        deal['eco']['val'] = '—'
        deal['src'].remove(BAD_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
