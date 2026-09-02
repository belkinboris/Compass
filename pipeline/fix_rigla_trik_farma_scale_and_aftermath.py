# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gb84f2b2f
(«Ригла купила краснодарскую Трик Фарму», закрыта 22 июня 2023) —
предмет сделки (число аптек) не был назван, динамика выручки цели
известна только одной цифрой, а дальнейшая судьба юрлица (поглощение
«Риглой») не отражена.

Проверено лично прямым WebFetch (Ведомости,
https://www.vedomosti.ru/business/articles/2023/06/26/982377-rigla-priobrela-krasnodarskuyu-aptechnuyu-set):
«Под этим брендом в Краснодаре работают пять аптек»; «в 2020 г. она
составила 381,1 млн, в 2021 г. – 270,1 млн, в 2022 г. – 245 млн руб.»
(выручка снижалась три года подряд — контекст к уже стоявшей в
`eco.target_fin` цифре 244,9 млн ₽ по СПАРК за тот же год).

Проверено лично прямым WebFetch (audit-it.ru,
https://www.audit-it.ru/contragent/1102312002099_ooo-trik-farma):
«прекращение деятельности юридического лица путем реорганизации в
форме присоединения»; «Дата начала реорганизации: 19 сентября 2023
года»; «Дата ликвидации: 05 сентября 2024 года»; «Правопреемник: ООО
"РИГЛА"» — юрлицо-цель окончательно поглощено «Риглой» немногим более
года спустя закрытия сделки, отдельной структурой больше не
существует.

НЕ ВКЛЮЧЕНО: консультанты сделки и согласование ФАС — ни один из
проверенных источников (Vademecum, Ведомости, Фармвестник, прямой
поиск по fas.gov.ru) их не называет; отсутствие упоминания ФАС не
равно подтверждению, что согласование не требовалось, — оставлено
честной заглушкой. Точное соответствие пяти прежних адресов «Трик
Фармы» нынешним точкам «Здравсити Аптека» в Краснодаре (сеть выросла
до 32+ точек за счёт других сделок «Риглы» в регионе) источниками не
устанавливается — не додумывается.

Запуск: python3 pipeline/fix_rigla_trik_farma_scale_and_aftermath.py
        python3 pipeline/fix_rigla_trik_farma_scale_and_aftermath.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gb84f2b2f'

OLD_ECO_SHARE = '—'
NEW_ECO_SHARE = (
    'Пять аптек в Краснодаре под брендом «Трик Фарма»; после сделки '
    'переименованы в «Здравсити Аптека».'
)

OLD_ECO_TARGET_FIN = 'Выручка «Трик Фармы» в 2022 году составила 244,9 млн рублей'
NEW_ECO_TARGET_FIN = (
    'Выручка «Трик Фармы» снижалась три года подряд: 381,1 млн ₽ (2020) '
    '→ 270,1 млн ₽ (2021) → 245 млн ₽ (2022, по данным Ведомостей; '
    'СПАРК называл близкую цифру — 244,9 млн ₽).'
)

OLD_ECO_CONTEXT = (
    'До этого компания принадлежала Александру (50,3%) и Ольге (16,53%) '
    'Казакевич, а также Олегу Покладу (33,17%)'
)
NEW_ECO_CONTEXT = (
    'До этого компания принадлежала Александру (50,3%) и Ольге (16,53%) '
    'Казакевич, а также Олегу Покладу (33,17%). ООО «Трик Фарма» '
    'реорганизовано присоединением к «Ригле» и прекратило существование '
    '5 сентября 2024 года — отдельным юрлицом сеть больше не значится.'
)

NEW_SRC = [
    ['Ведомости', 'https://www.vedomosti.ru/business/articles/2023/06/26/982377-rigla-priobrela-krasnodarskuyu-aptechnuyu-set'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['share'] == OLD_ECO_SHARE
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    new_src = deal['src'] + NEW_SRC

    print('=== eco.share: станет ===')
    print(NEW_ECO_SHARE)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['share'] = NEW_ECO_SHARE
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
