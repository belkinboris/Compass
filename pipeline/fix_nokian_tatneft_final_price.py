# -*- coding: utf-8 -*-
"""У карточки `g2d525daa` («Продажа российского шинного бизнеса Nokian Tyres
компании «Татнефть»») `sum`/`eco.sum` несли «€400 млн» — это ПЕРВОНАЧАЛЬНАЯ
ориентировочная цена на момент подписания соглашения (28 октября 2022 года),
а не фактически уплаченная сумма. Собственное поле `extra` этой же карточки
уже честно рассказывает, что случилось дальше: правительственная комиссия
14 марта 2023 года ограничила допустимую цену 23,05 млрд рублей, и 16–17
марта 2023 года Nokian Tyres получила оплату именно в размере 285 млн евро —
на 115–125 млн евро меньше изначально заявленной суммы. Источник (TAdviser)
называет это число прямо: «Nokian Tyres получила от "Татнефти" 285 млн евро
за шинный бизнес в РФ». Родня уже записанного класса уроков про суммы,
которые относятся не к тому событию/не к той величине (ВТБ/Holiday Inn,
Арнест/Reckitt, Нордлайн/TotalEnergies) — только здесь обе цифры относятся к
ОДНОЙ И ТОЙ ЖЕ сделке, просто одна из них — цена на момент ПОДПИСАНИЯ, а
другая — фактически уплаченная после государственного ограничения; для
заголовочного поля `sum` (то, что сделка «закрыта» и оплачена) верна вторая.

Почему не через review.py: `sum_is_supported()` в `pipeline/ingest/review.py`
проверяет формат только для рублёвых сумм («N[–M] млн|млрд ₽») — валютные
суммы в других значках (€/$) через таблицу FIXES провести нельзя (тот же
формат-барьер, что уже встречался с «до N млн ₽»), хотя дом-стиль CLAUDE.md
прямо разрешает € перед числом. Резать это ограничение ради одной карточки
не стали — правится отдельным скриптом с дословной цитатой в комментарии и
`assert` на исходное значение, тем же путём, что и другие точечные правки
суммы (`fix_nordline_arctic_sum_misattribution.py`).

Запуск: python3 pipeline/fix_nokian_tatneft_final_price.py
        python3 pipeline/fix_nokian_tatneft_final_price.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g2d525daa'
OLD_SUM = '€400 млн'
NEW_SUM = '€285 млн'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['sum'] == NEW_SUM and card['eco']['sum'] == NEW_SUM:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['sum'] == OLD_SUM, '%s: sum уже другой' % CARD_ID
    assert card['eco']['sum'] == OLD_SUM, '%s: eco.sum уже другой' % CARD_ID
    print('ПРАВИМ  %s sum и eco.sum: «%s» -> «%s» (фактически уплачено, а не '
          'цена на момент подписания)' % (CARD_ID, OLD_SUM, NEW_SUM))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['sum'] = NEW_SUM
    card['eco']['sum'] = NEW_SUM
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
