# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gece30945` («ТМХ и Rail Vikas Nigam создали СП для поставки поездов
Vande Bharat в Индию», закрыта, 2023) — дочитывание нашло точную
структуру владения СП, разбивку суммы контракта и первую веху после
его создания.

Проверено (по докладу саб-агента, дословные цитаты):
- interfax.ru/business/896323: «Членами консорциума являются структуры
  ТМХ — «Метровагонмаш» и «Локомотивные электронные системы» — c долями
  70% и 5% соответственно, оставшиеся 25% принадлежат Rail Vikas Nigam
  Limited»; «Сумма контракта составит порядка $1,8 млрд за поставку
  поездов и $2,5 млрд за их сервисное обслуживание в течение 35 лет».
- russiaspivottoasia.com/russia-india-joint-venture-wins-us6-5-billion-
  contract-to-build-electric-trains/: консорциум ТМХ/RVNL обошёл в
  тендере Siemens, Alstom Transport и Stadler Rail.
- urbantransportnews.com/news/tmh-rvnl-consortium-propels-the-35000-
  crore-vande-bharat-sleeper-train-project: «TMH submitted a performance
  bank guarantee of Rs 200 crore on August 28, 2023, enabling the
  Manufacturing and Maintenance Agreement with Indian Railways» —
  первая веха после подписания соглашения о СП.
- interfax.ru/business/956649 и /945115: выручка ТМХ по итогам 2023
  года превысила 400 млрд ₽ (рост ~30%), EBITDA по МСФО выросла в 1,7
  раза, до 47 млрд ₽ — масштаб покупателя на момент сделки.

НЕ ВНЕСЕНО: (1) юридический/финансовый консультант — ноль по ~13
проверенным источникам (Интерфакс ×3, Swarajyamag ×2, The Wire, Urban
Transport News, TheMachineMaker, theprint.in и др.); (2) прямое
объяснение, зачем именно индийский рынок понадобился ТМХ, — не найдено,
только общий факт присутствия в 30 странах; (3) расхождение о
конфигурации составов после начала производства (120 поездов по 16
вагонов по первоначальному контракту против сообщений о пересмотре на
80 составов по 24 вагона) — не разрешено дословным чтением обеих версий
целиком (несколько источников недоступны, 403), прямая цитата министра
Вайшнава в парламенте (theprint.in) подтверждает первоначальные условия
— оставлено на будущее чтение, если источники станут доступны; (4)
переход консорциума к операционному контролю над заводом Marathwada
Rail Coach Factory в Латуре (конец июня 2024 года) — источник
(railwaygazette.com) вернул 403, дословная цитата не получена.

Запуск: python3 pipeline/fix_tmh_rvnl_kinet_structure_and_context.py
        python3 pipeline/fix_tmh_rvnl_kinet_structure_and_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gece30945'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Долю ТМХ в 75% в СП «Кинет» держат две его структуры: «Метровагонмаш» '
    '(70%) и «Локомотивные электронные системы» (5%); оставшиеся 25% — у '
    'Rail Vikas Nigam Limited.'
)

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Сумма контракта складывается из двух частей: около $1,8 млрд за '
    'поставку поездов и ещё $2,5 млрд за их сервисное обслуживание в '
    'течение 35 лет. В тендере консорциум ТМХ/RVNL обошёл Siemens, '
    'Alstom Transport и Stadler Rail. 28 августа 2023 года ТМХ внёс '
    'банковскую гарантию, необходимую для вступления в силу соглашения '
    'о производстве и обслуживании поездов с индийскими железными '
    'дорогами. По итогам 2023 года выручка самого ТМХ превысила 400 '
    'млрд ₽ (рост около 30%), а EBITDA по МСФО выросла в 1,7 раза, до 47 '
    'млрд ₽.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['eco']['context'] = NEW_ECO_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
