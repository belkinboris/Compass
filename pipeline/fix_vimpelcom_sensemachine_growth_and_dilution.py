# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g3d0699a8 (ВымпелКом инвестировал в Candy Flip Robots / Sense Machine,
закрыта 7 ноября 2023) — «Хайв» нарастил долю, затем размылся под новый
раунд другого инвестора, финансы компании ухудшились.

Проверено лично прямым WebFetch (AKM.RU,
https://www.akm.ru/news/vympelkom_uvelichil_svoyu_dolyu_uchastiya_v_razrabotchike_programmnoy_sistemy_sense_machine/,
23.09.2024): «ООО «Хайв» — стала владельцем 25.46% ООО «Кенди Флип
Роботс», увеличив свой пакет с 19.3% до блокирующего», «Пакеты были
приобретены у Алексея Овчарова, который продал свою долю в компании»,
«Выручка компании за 2023 год составила 121.2 млн руб., год был
закончен с убытком 12.9 млн руб.».

Проверено лично прямым WebFetch (Mergers.ru,
https://mergers.ru/news/Venchurnyj-fond-Voshod-investiroval-v-razrabotchika-datatech-platformy-SenseMachine-85447,
27.06.2025): «Datatech-платформа SenseMachine... привлекла 100 млн
рублей в ходе нового раунда инвестиций», лид-инвестор — венчурный фонд
«Восход» (связан с холдингом «Интеррос» Владимира Потанина), «Владельцами
ООО «Кенди Флип Роботс»... выступают Владимир Марголин (36,1%) и Сергей
Коренков (27,1%), а также ООО «Хайв» (23,9%) и «Восход» (12,9%)» — доля
«Хайва» снизилась не продажей, а размытием при новом раунде.

По данным саб-агента (не дозаверено отдельным WebFetch, агрегаторы
СПАРК/Контур.Фокус недоступны прямым WebFetch — 403): выручка за 2024
год почти не выросла (~122 млн ₽), убыток вырос почти вчетверо (49,6
млн ₽ против 12,9 млн ₽ в 2023-м) — цифра согласуется арифметически
(12,9×4≈51,6) и повторяется в нескольких независимых сводках, но без
прямой цитаты с открытым URL, поэтому в `extra` идёт с осторожной
формулировкой, без точного числа убытка.

НЕ ВКЛЮЧЕНО: смена гендиректора на Сергея Коренкова (саб-агент нашёл
это только в непроверенной агрегированной сводке, другой источник
называет директором Овчарова — противоречиво, не вносится); интеграция
технологии в продукты самого «Вымпелкома»/beeline (ни один источник не
подтверждает, что это реализовано — только гипотеза экспертов на
момент сделки, уже отражённая в исходном тексте карточки).

Запуск: python3 pipeline/fix_vimpelcom_sensemachine_growth_and_dilution.py
        python3 pipeline/fix_vimpelcom_sensemachine_growth_and_dilution.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g3d0699a8'

OLD_EXTRA = (
    'Вымпелком через свою венчурную компанию ООО Хайв приобрел 13,3% '
    'долей в ООО Кенди Флип Роботс, разработчика ПО Sense Machine для '
    'анализа эмоций по видеоизображениям. Сделка закрыта 7 ноября 2023.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' 23 сентября 2024 «Хайв» нарастил долю до блокирующих 25,46%, '
    'выкупив пакет у вышедшего из капитала Алексея Овчарова. 27 июня '
    '2025 компания привлекла новый раунд 100 млн ₽ с лид-инвестором — '
    'венчурным фондом «Восход» (связан с холдингом «Интеррос»): доля '
    '«Хайва» размылась до 23,9% без продажи. Финансы компании при этом '
    'ухудшились: выручка почти не выросла, а убыток заметно увеличился '
    'по сравнению с 2023 годом.'
)

NEW_SRC = [
    ['AKM.RU', 'https://www.akm.ru/news/vympelkom_uvelichil_svoyu_dolyu_uchastiya_v_razrabotchike_programmnoy_sistemy_sense_machine/'],
    ['Mergers.ru', 'https://mergers.ru/news/Venchurnyj-fond-Voshod-investiroval-v-razrabotchika-datatech-platformy-SenseMachine-85447'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
