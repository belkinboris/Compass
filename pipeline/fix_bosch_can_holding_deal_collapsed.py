# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g23592800» («Покупка турецким Can Holding российских заводов Bosch по
производству бытовой техники», статус «Обсуждается» с 19.12.2023) —
СДЕЛКА С CAN HOLDING НЕ СОСТОЯЛАСЬ.

Предыдущий ревизионный проход (`batch_c_2023.py`, комментарий «g23592800
rev05») уже нашёл, что в апреле 2024 года завод передан указом
президента во временное управление «Газпром бытовым системам», но
СОЗНАТЕЛЬНО не менял статус: «"под угрозой срыва" — не то же самое, что
"не состоялась" механически..., судьба сделки формально открыта» —
явной цитаты о срыве ИМЕННО сделки с Can Holding на тот момент не было.

Такая цитата с тех пор появилась. Проверено лично прямым WebFetch:
- Lenta.ru, https://lenta.ru/news/2025/05/09/bosch-soobschila-o-sryve-sdelki-po-prodazhe-zavodov-v-peterburge/,
  09.05.2025: «Bosch не смог продать свое предприятие в Петербурге,
  которым владеет его дочерняя компания ООО «БСХ бытовые приборы»»;
  «сделка оказалась невозможной из-за передачи предприятия во
  временное управление АО «Газпром бытовые системы»».
- Фонтанка, https://www.fontanka.ru/2026/03/16/76313667/, 16.03.2026:
  завод выпускает холодильники «под собственной торговой маркой Darina
  и в рамках контрактного производства под брендами Weissgauff,
  Kuppersberg и рядом других»; «ведется работа по организации
  производства стиральных машин»; Bosch официально заявил, что «не
  планирует возвращаться в Россию».

Статус меняется на «Не состоялась» — это ИМЕННО про несостоявшуюся
покупку Can Holding, не про судьбу завода в целом (завод работает,
просто не был продан туда, куда планировалось). `buyer`/`title`/`type`
НЕ трогаю: возможная переработка карточки под класс «временное
управление» (как уже есть для похожих сюжетов) — решение для человека,
не для одного скрипта; сохраняю то, ЧТО ИМЕННО обсуждалось и не
случилось.

НЕ ВКЛЮЧЕНО: судьба самой Can Holding и её брендов (Awox, Seikon) после
апреля 2024 года — ни один источник её не отражает; номер указа
президента — источники (Meduza, Интерфакс) называют дату (26 апреля
2024), но не дословную цитату самого текста указа, вносить номер без
дословного подтверждения не стал; `eco.target_fin` — уже занято правкой
другого потока (`batch_c_2023.py`), не трогаю во избежание конфликта
редактирования одного поля из двух мест.

Запуск: python3 pipeline/fix_bosch_can_holding_deal_collapsed.py
        python3 pipeline/fix_bosch_can_holding_deal_collapsed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g23592800'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Не состоялась'

OLD_EXTRA = ''
NEW_EXTRA = (
    'Сделка с Can Holding не состоялась: в апреле 2024 года президент '
    'подписал указ о передаче ООО «БСХ бытовые приборы» во временное '
    'управление «Газпром бытовым системам» — переговоры с турецким '
    'инвестором оказались невозможны. Bosch формально остаётся '
    'собственником завода, но заявил, что не планирует возвращаться в '
    'Россию. С мая 2025 года завод под управлением «Газпрома» '
    'возобновил выпуск холодильников под собственной маркой Darina и '
    'по контракту — под брендами Weissgauff и Kuppersberg.'
)

OLD_ECO_CONTEXT = (
    'ООО «БСХ Бытовые приборы» работало в стране с 1994 года, выпуская '
    'более 1 млн холодильников и стиральных машин в год и организуя '
    'сервис для марок Bosch, Siemens, Gaggenau и Neff.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Судьба Can Holding и его планов на завод '
    '(бренды Awox, Seikon) после апреля 2024 года в открытых '
    'источниках не отражена.'
)

NEW_SRC = [
    ['Lenta.ru', 'https://lenta.ru/news/2025/05/09/bosch-soobschila-o-sryve-sdelki-po-prodazhe-zavodov-v-peterburge/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['extra'] == OLD_EXTRA
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['status'] = NEW_STATUS
        deal['extra'] = NEW_EXTRA
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
