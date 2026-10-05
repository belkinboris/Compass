# -*- coding: utf-8 -*-
"""Качество, 5 октября 2026 (ежедневный прогон 21:37 МСК) — подтверждение
фактов двумя чтениями, карточка `berizaryad» («Яндекс» приобрёл 100%
сервиса «Бери заряд!»). Поле `sum` стояло «4,2 млрд ₽», но два
независимых чтения (`facts_confirm.py`) не нашли эту цифру ни в одном
доступном источнике — «Ведомости» и Коммерсантъ прямо пишут, что сумма
не раскрывается; `facts.price` подтверждён как `undisclosed` (null).
Единственный источник, где могла стоять именно эта цифра (rbc.ru), этой
машине недоступен (401/сброс соединения у обоих читателей) — честнее
написать «Не раскрыта», чем оставить непроверенное число.

`sum` не прошло бы через `review.py` напрямую: его проверка (`check()`,
ветка `field == 'sum'`) разбирает только числовой формат суммы и не
умеет записывать «Не раскрыта» — тот же класс ограничения, что у ранних
one-off правок.

Запуск:
    python3 pipeline/fix_berizaryad_sum_undisclosed_2026_10_05.py            # сухой прогон
    python3 pipeline/fix_berizaryad_sum_undisclosed_2026_10_05.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'berizaryad']
    assert len(target) == 1, target
    card = target[0]
    assert card.get('sum') == '4,2 млрд ₽', card.get('sum')
    assert card['facts']['price'].get('meaning') == 'undisclosed', card['facts']['price']

    card['sum'] = 'Не раскрыта'

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('sum карточки berizaryad заменён на «Не раскрыта». ЗАПИСАНО.')
    else:
        print('Сухой прогон: заменил бы sum на «Не раскрыта». Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
