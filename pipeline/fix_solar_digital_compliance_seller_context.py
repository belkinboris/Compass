# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gdbb7d921 (ГК «Солар»
приобрела 100% долей ООО «Диджитал Комплаенс» и ООО «Кибер Сервис»,
октябрь 2024): дельта-поиск нашёл продавца — но ТОЛЬКО для одного из двух
юрлиц предмета сделки. Коммерсантъ прямо называет: ООО «Диджитал
Комплаенс» (юрлицо Digital Security) «с ноября 2022 года по 11 октября
2024 года на 100% принадлежало Елене Медведовской». Про второе юрлицо,
ООО «Кибер Сервис», источник ничего не говорит — учредитель по данным
поисковой выдачи (не проверено WebFetch) может быть другим человеком
(Ольга, не Елена, Медведовская), поэтому факт записан ТОЛЬКО про
«Диджитал Комплаенс», без обобщения на всю сделку и без записи в
структурное поле `seller` (которое относилось бы к сделке целиком).
Также уточнена методика оценки суммы (уже есть диапазон 100-400 млн ₽ —
источник называет расчёт: балансовая стоимость 170 млн руб., мультипликатор
1,8-2,5 капитала). Дословные цитаты подтверждены лично прямым WebFetch.

Запуск: python3 pipeline/fix_solar_digital_compliance_seller_context.py
        python3 pipeline/fix_solar_digital_compliance_seller_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gdbb7d921'

OLD_CONTEXT = (
    'Digital Security – российская консалтинговая компания в области ИБ, '
    'основанная в 2003 г. Команда, включающая более 60 исследователей и '
    'пентестеров, специализируется на комплексном анализе защищенности '
    'корпоративных сетей и ИТ-инфраструктуры, тестировании на '
    'проникновение, анализе защищенности приложений и других связанных с '
    'этим услугах.'
)
CONTEXT_ADDITION = (
    ' Продавец одного из двух юрлиц предмета сделки, ООО «Диджитал '
    'Комплаенс» (юрлицо Digital Security), назван в Коммерсанте: «с ноября '
    '2022 года по 11 октября 2024 года на 100% принадлежало Елене '
    'Медведовской» (про второе юрлицо, ООО «Кибер Сервис», источник не '
    'говорит ничего). Там же — методика оценки: «оценивает сумму сделки '
    'на основе балансовой стоимости в 170 млн руб.», а с учётом команды '
    'специалистов «стоимость Digital Security может быть повышена до '
    'мультипликатора 1,8–2,5 капитала».'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/7230546'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
