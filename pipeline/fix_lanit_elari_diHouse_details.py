# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g0be89c20` («ГК «Ланит» купила российские активы израильской Elari»,
февраль 2024, Закрыта) — линза «Экономист» пуста, что за компания
Elari и что стало с бизнесом после покупки не пояснялось.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- comnews.ru/content/231358/...: Elari «создана Йосефом Заксом в 2012
  году», «занимается разработкой приложений, а также продажей носимых
  устройств и другой электронной продукции» (в основном детские умные
  часы); купленное — «команду разработчиков, работавших в Elari; право
  использовать товарный знак в РФ и Белоруссии; права интеллектуальной
  собственности на софт для умной электроники»; сумма — «стоимость
  российского бизнеса Elari могла составлять до 500 млн рублей»
  (оценка знакомого со сторонами источника, официально не раскрыта);
- new-retail.ru/novosti/retail/dihouse_priobrela_rossiyskiy_biznes_elari/:
  «Генеральным директором российской компании назначен Антон Бадаев,
  многие годы руководивший продуктовой разработкой в московском офисе
  ELARI»; «Йосеф Закс, основатель и управляющий директор ELARI
  International, останется в совете директоров ELARI IT и в ранге
  советника компании diHouse»; новая компания продолжит «разработку и
  поддержку продукции и программного обеспечения (ПО) для рынка России
  и Беларуси», diHouse — эксклюзивный дистрибьютор.

НЕ ВНЕСЕНО: (1) точные доли собственников ООО «Элари айти» (99,99%
у ООО «Дихаус», 0,01% у Юрия Родного) — встретились только в
агрегированной выдаче поиска, ни разу не подтверждены прямым чтением
страницы реестра (страница TAdviser о самой компании отдаёт 404,
ferra.ru не отрендерил содержимое) — не переносится без прямой
проверки; (2) утверждение о росте продаж бренда «в 46 раз» в 2024 году
— тоже только агрегированный сниппет поиска, не проверено чтением
конкретной статьи целиком; (3) сумма сделки в `sum`/`eco.sum` уже
стоит «500 млн ₽ (по оценке)» и совпадает с найденной оценкой — не
меняется.

Запуск: python3 pipeline/fix_lanit_elari_diHouse_details.py
        python3 pipeline/fix_lanit_elari_diHouse_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g0be89c20'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Elari — израильский разработчик гаджетов, основанный Йосефом Заксом '
    'в 2012 году; компания делает приложения и носимые устройства, в '
    'первую очередь детские умные часы. У «Ланита» (через дочернюю '
    'diHouse) — команда бывших разработчиков Elari, право на товарный '
    'знак в России и Белоруссии и права на программное обеспечение для '
    'умной электроники; сам бренд Elari и его международный бизнес '
    'остаются за прежними владельцами. Гендиректором российской компании '
    'стал Антон Бадаев, ранее руководивший продуктовой разработкой в '
    'московском офисе Elari; основатель Йосеф Закс вошёл в совет '
    'директоров новой компании как советник diHouse.'
)

OLD_SRC = [
    ['Известия', 'https://iz.ru/1642734/valerii-kodachigov/chasnoe-delo-izrailskii-razrabotchik-gadzhetov-elari-prodal-aktivy-v-rf'],
]
NEW_SRC = OLD_SRC + [
    ['ComNews', 'https://www.comnews.ru/content/231358/2024-02-01/2024-w05/1009/chasnoe-delo-izrailskiy-razrabotchik-gadzhetov-elari-prodal-aktivy-rf'],
    ['New Retail', 'https://new-retail.ru/novosti/retail/dihouse_priobrela_rossiyskiy_biznes_elari/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
