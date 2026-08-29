# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g6e4d91c3
(Фонд 3 STREAMS вложил 60 млн рублей в Shinsale через конвертируемый
займ, август 2024). Дельта-поиск нашёл ВТОРОЙ раунд инвестиций того же
фонда в тот же актив — событие произошло в марте 2025, до всех трёх
уровней обыска карточки, и было упущено.

RB.ru, 19.03.2025 (проверено лично прямым WebFetch,
https://rb.ru/news/shinsale-vkusvill-investments/): «Российский
инвестиционный фонд 3 Streams вложил еще 50 млн рублей в сервис подбора
б/у шин и дисков Shinsale» — «Общая сумма инвестиций 3 Streams в Shinsale
достигла 110 млн рублей.» Деньги пойдут «на развитие логистической
инфраструктуры и оптимизацию процесса обработки шин с применением
различных технологий, включая искусственный интеллект».

Это отдельное, более позднее событие (второй раунд), а не уточнение уже
описанного займа 60 млн ₽ — не заменяет `sum`/`eco.sum` (они остаются
про первый транш), добавлено в `eco.context` как продолжение истории.
Конвертация первого займа (60 млн ₽) в долю 16,67% нигде прямо не
упоминается и не датирована — не утверждается.

НЕ включены: подтверждение конвертации займа в долю, финансовые
показатели Shinsale за 2024-2025 год (везде повторяется только цифра
2023 года), консультанты сделки, судьба фонда 3 STREAMS в целом — не
нашлось ни в одном источнике.

Запуск: python3 pipeline/fix_3streams_shinsale_second_round.py
        python3 pipeline/fix_3streams_shinsale_second_round.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g6e4d91c3'

OLD_CONTEXT = (
    '3 STREAMS — частный инвестиционный фонд, ориентирован на развитие '
    'быстрорастущих российских брендов на рынке потребительских товаров. С '
    '2018 по 2023 год команда развивала венчурный фонд и акселератор для '
    'стартапов Startup Lab. Было совершено более 30 инвестиций в России, '
    'США и Европе.'
)
CONTEXT_ADDITION = (
    ' В марте 2025 года фонд вложил ещё 50 млн рублей: «Общая сумма '
    'инвестиций 3 Streams в Shinsale достигла 110 млн рублей» — средства '
    'направят «на развитие логистической инфраструктуры и оптимизацию '
    'процесса обработки шин с применением различных технологий, включая '
    'искусственный интеллект» (RB.ru).'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION

NEW_SRC = [
    ['RB.ru', 'https://rb.ru/news/shinsale-vkusvill-investments/'],
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
