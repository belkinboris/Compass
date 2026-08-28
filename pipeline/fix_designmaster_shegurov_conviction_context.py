# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gffed92e4 (WB-Russ приобретает
оператора наружной рекламы «Дизайнмастер», ноябрь 2024): дельта-поиск нашёл,
что бывший совладелец «Дизайнмастера» Роман Шегуров (тот же человек, чья
цитата уже стоит в `eco.rationale` карточки — «Нам были предложены хорошие
условия по продаже бизнеса») осуждён в феврале 2026 года — уже ПОСЛЕ
продажи компании. Источник NGS.ru уже привязан к карточке (был среди трёх
исходных ссылок), но сам факт приговора не был перенесён в поля. Дело не
касается сделки с WB-Russ и самой компании «Дизайнмастер» напрямую — только
личной ответственности бывшего владельца. Дословная цитата подтверждена
лично прямым WebFetch.

Запуск: python3 pipeline/fix_designmaster_shegurov_conviction_context.py
        python3 pipeline/fix_designmaster_shegurov_conviction_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gffed92e4'

OLD_CONTEXT = (
    'Владельцами бизнеса являются новосибирские предприниматели, создавшие '
    'известные бренды: торговый дом «Септима», интернет-провайдер '
    '«Электронный город», компанию «Сибирский грузовой терминал», торгово-'
    'офисный центр «Ситицентр», ресторан LaMaison и другие. Бывшие '
    'собственники «Дизайнмастера» планируют развиваться в сфере '
    'строительного рынка и сейчас получили разрешение на возведение нового '
    'объекта в городе.'
)
CONTEXT_ADDITION = (
    ' Уже после продажи бизнеса бывший совладелец «Дизайнмастера» Роман '
    'Шегуров осуждён: в феврале 2026 года суд признал его виновным «по '
    'ч.2 ст.165 УК РФ — причинение крупного ущерба путем обмана или '
    'злоупотребления доверием» и назначил «2 лет условно с испытательным '
    'сроком 2 года» плюс штраф 50 тыс. руб. (дело возбуждено ещё в ноябре '
    '2022 года, до сделки с WB-Russ, и её самой не касается).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
