# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка `gc82185e7`
(«Русагро купила элеватор «БиоТехнологии» в Тамбовской области», закрыта,
2023-10-06) — дочитывание подтвердило уже известное (продавец, финансы
цели) вторым чтением и добавило три новых факта: мощность элеватора,
уставный капитал и год регистрации.

Проверено (по докладу саб-агента, дословные цитаты, abireg.ru/newsitem/99610
если не указано иное):
- «элеватор может вмещать в себя 240 тыс. тонн зерновых единовременного
  хранения пшеницы, ячменя, подсолнечника, кукурузы, сои, ржи и других
  культур» — мощность предмета, ранее на карточке не стояла.
- «Уставный капитал – 1 млрд рублей.» — показатель цели, не был перенесён.
- «АО «БиоТехнологии» зарегистрировано в Тамбовской области в 2007 году.»
  — год регистрации, не был перенесён.
- Продавец (50% АО «Российская холдинговая компания» + 50% Whispering
  Lakes Limited) уже стоит в `eco.context` дословно — тем же чтением
  подтверждён вторым источником не был (только abireg), но факт уже верно
  внесён; переносится в структурное поле `seller` (было пустым).

НЕ ВНЕСЕНО: (1) юридический/финансовый консультант сделки — ноль по
проверенным источникам; (2) согласование ФАС — не упоминается ни в одном
источнике; (3) независимая экспертная оценка суммы сделки по мощности
элеватора — не найдена, сумма остаётся «Не раскрыта»; (4) реестровая
история смены учредителей ДО сделки (для подтверждения продавца вторым
источником) — технически недоступна (капча/403/429/платный доступ у
основных агрегаторов).

Запуск: python3 pipeline/fix_rusagro_biotehnologii_seller_and_details.py
        python3 pipeline/fix_rusagro_biotehnologii_seller_and_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc82185e7'

OLD_SELLER = None
NEW_SELLER = 'АО «Российская холдинговая компания» и Whispering Lakes Limited (по 50%)'

OLD_ECO_SHARE = '100% акций'
NEW_ECO_SHARE = (
    OLD_ECO_SHARE + '. Элеватор рассчитан на 240 тыс. тонн единовременного '
    'хранения зерновых и масличных культур (пшеница, ячмень, подсолнечник, '
    'кукуруза, соя, рожь и другие).'
)

OLD_ECO_TARGET_FIN = (
    'В 2022 году выручка «БиоТехнологий» составила 190,5 млн ₽, чистая '
    'прибыль — 4,1 млн ₽.'
)
NEW_ECO_TARGET_FIN = (
    OLD_ECO_TARGET_FIN + ' Уставный капитал АО «БиоТехнологии» — 1 млрд '
    'рублей.'
)

OLD_ECO_CONTEXT = (
    '50% компании принадлежит АО «Российская холдинговая компания»; раньше '
    'эта доля была у бывшего топ-менеджера «Газпрома» Александра Рязанова. '
    'Ещё 50% — у кипрской Whispering Lakes Limited.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' АО «БиоТехнологии» зарегистрировано в Тамбовской '
    'области в 2007 году.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('seller') == OLD_SELLER
    assert deal['eco']['share'] == OLD_ECO_SHARE
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    print('=== seller: станет ===')
    print(NEW_SELLER)
    print('\n=== eco.share: станет ===')
    print(NEW_ECO_SHARE)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)

    if write:
        deal['seller'] = NEW_SELLER
        deal['eco']['share'] = NEW_ECO_SHARE
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['eco']['context'] = NEW_ECO_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
