# -*- coding: utf-8 -*-
"""Качество, 3 октября 2026 (ежедневный прогон 21:37 МСК) — месячная
очередь дочитывания (третий уровень), карточка `gd9ccfdd2` («Леста»,
Минфин продаёт издателя «Мира танков»). В карточке уже есть событие от
1 октября про «Дхамму», но пропущен более ранний и на тот момент более
значимый этап: 15 сентября Forbes сообщил, что сделка с Никитой Мазепиным
была «на финишной прямой» (документы готовы, осталась цена) — это раньше
и конкретнее уже отражённого в `eco.rationale` общего упоминания его
интереса «в сентябре». Без этого события хронология выглядит так, будто
Мазепин появился только 1 октября одним из претендентов среди прочих, а
на деле к середине сентября он был главным кандидатом.

Финансовые показатели «Лесты» за 2025 год, которые саб-агент тоже
приводил (выручка 29,05 млрд ₽, прибыль 10,5 млрд ₽), в указанном
источнике (expert.ru) дословно НЕ НАШЛИСЬ при проверке — текст статьи
говорит про другие цифры (2024 год, 35 млрд ₽ прибыли, рост выручки 40%,
$1,6 млрд оценка в рейтинге Рунета). Эти цифры в карточку НЕ добавлены —
саб-агент либо спутал источник, либо процитировал не ту статью; честнее
оставить поле как есть, чем внести непроверенную цифру.

Запуск:
    python3 pipeline/fix_lesta_mazepin_finish_line_2026_10_03.py            # сухой прогон
    python3 pipeline/fix_lesta_mazepin_finish_line_2026_10_03.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

NEW_EVENT = {
    'kind': 'negotiations',
    'date': '2026-09-15',
    'title': 'Мазепин — на финишной прямой',
    'note': ('По данным Forbes, сделка о продаже «Лесты» Никите Мазепину '
             'находится на финишной прямой — документы уже подготовлены, '
             'осталось согласовать цену. Источник Forbes оценил справедливую '
             'стоимость компании в 30–35 млрд ₽ — ниже первоначальной оценки '
             'в 50 млрд ₽.'),
    'source': ['Forbes (через 3DNews)',
               'https://3dnews.ru/1148534/vot-eto-povorot-na-pokupku-izdatelya-mira-tankov-i-mira-korabley-natselilsya-bivshiy-rossiyskiy-gonshchik-formuli1'],
}


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'gd9ccfdd2']
    assert len(target) == 1, target
    card = target[0]
    assert len(card['events']) == 2, card['events']
    assert not any(e.get('source', [None, None])[1] == NEW_EVENT['source'][1]
                   for e in card['events'])
    card['events'].insert(1, NEW_EVENT)

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Событие 15.09.2026 (Мазепин на финишной прямой) добавлено в gd9ccfdd2. ЗАПИСАНО.')
    else:
        print('Сухой прогон: добавил бы новое событие в events[] карточки gd9ccfdd2. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
