# -*- coding: utf-8 -*-
"""Качество, 25 сентября 2026 (ежедневный прогон 21:37 МСК) — ИСПРАВЛЕНИЕ
СВОЕЙ ЖЕ ОШИБКИ ТЕМ ЖЕ ПРОГОНОМ. `pipeline/fix_tdmtekh_sum_unsupported.py`
(этот же прогон, раньше) снял сумму «5,95 млрд ₽» с карточки `g7fac547e`,
потому что оба независимых читателя фактов прочитали ЕДИНСТВЕННЫЙ указанный
в `src` источник (АК&М, 22.09.2023) и не нашли в нём суммы — это было верно
дословно, но вывод из этого был поспешным.

Сумма СУЩЕСТВОВАЛА и была верна — только раскрыта ПОЗЖЕ и ДРУГИМ
источником, никогда не попадавшим в `src` карточки: ComNews, 07.03.2024
(со ссылкой на «материалы „Т2 Мобайл“», перепечатано «Интерфаксом» тем же
днём). В таблице `FIXES` (`pipeline/ingest/fixes/batch_agents100_r7.py`,
партия агентов, 15 августа 2026) цитата comnews.ru уже стояла и когда-то
была принята — но добавляя сумму, тот прогон не дописал источник в `src`,
и следующее чтение (сегодня) видело только AK&M и решило, что цифра ничем
не подтверждена.

Урок: «единственный источник в `src` ничего не подтверждает» — не то же
самое, что «факт не подтверждён». Прежде чем снимать значение, стоило
искать сам факт в вебе (как это и предписывает первый уровень очереди
дочитывания), а не только проверять src карточки. Восстановлено: сумма,
плюс сам источник — в `src`, которого там не хватало.

Запуск:
    python3 pipeline/fix_tdmtekh_sum_restored.py            # сухой прогон
    python3 pipeline/fix_tdmtekh_sum_restored.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

RIGHT_SUM = '5,95 млрд ₽'
NEW_SRC = ['ComNews', 'https://www.comnews.ru/content/231919/2024-03-07/2024-w10/1009/tele2-zaplatil-595-mlrd-rubley-za-85-tdm-tekh-razrabotchika-pak-dlya-operatorov-svyazi']


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'g7fac547e']
    assert len(target) == 1, target
    card = target[0]
    assert card['sum'] is None, repr(card['sum'])
    assert RIGHT_SUM in card.get('retracted', {}).get('sum', [])

    card['sum'] = RIGHT_SUM
    card['eco']['sum'] = RIGHT_SUM
    card['retracted']['sum'].remove(RIGHT_SUM)
    if not card['retracted']['sum']:
        del card['retracted']['sum']
    if not card['retracted']:
        del card['retracted']
    if NEW_SRC not in card['src']:
        card['src'].append(NEW_SRC)

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Сумма g7fac547e восстановлена, ComNews добавлен в src. ЗАПИСАНО.')
    else:
        print('Сухой прогон: восстановил бы сумму и добавил источник. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
