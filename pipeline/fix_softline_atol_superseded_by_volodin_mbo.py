# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`ged4a85ae` («Softline приобретает Атол», статус «Обсуждается» с
2023 года) — находка: переговоры с Softline, похоже, ничем не
закончились, актив в итоге купил другой покупатель.

Проверено лично прямым WebFetch (CNews, https://www.cnews.ru/news/top/2024-12-23_osnovateli_krupnogo_proizvoditelya,
23.12.2024): покупатель — Роман Володин, бывший гендиректор «Атола»
(выкуп менеджментом); продавцы — те же Алексей и Ирина Макаровы (по
50%); «Софтлайн» вышла из переговоров «из-за текущей ключевой ставки»
(аналитик Геннадий Тарантасов); выручка «Атола» за 2023 год — 5,3
млрд ₽, чистая прибыль — 227 млн ₽ (рост с 3,9 млрд ₽/26 млн ₽ за 2022
год, которые уже стоят в карточке).

По докладу саб-агента (не перепроверено мной лично прямым WebFetch):
среди других не завершивших сделку претендентов также назывались
Сбербанк и Т-Банк; юридическое сопровождение выкупа осуществляла
фирма LEVEL Legal Services; точная сумма сделки Володина не раскрыта
(экспертная оценка 1,5–2 млрд ₽, у Ленты — «несколько миллиардов
рублей»); упоминание «2,1 млрд ₽» на странице TAdviser относится к
ДРУГОЙ сделке (Сбербанк/Эвотор) и не должно использоваться здесь.

НЕ ВНЕСЕНО в структурные поля (`buyer`/`title`/`status`) — см.
отдельную запись в CLAUDE.md, «Известные проблемы»: решение о том, как
переформулировать карточку, оставлено человеку.

Запуск: python3 pipeline/fix_softline_atol_superseded_by_volodin_mbo.py
        python3 pipeline/fix_softline_atol_superseded_by_volodin_mbo.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ged4a85ae'

OLD_ECO_CONTEXT = (
    'Таким образом, «Софтлайн» продолжает стратегию поглощения '
    'активов в разных сегментах. Эксперты предполагают, что новая '
    'сделка позволит компании расширить клиентскую базу в розничной '
    'торговле, а также усилить позиции в продажах не только ПО, но и '
    'аппаратного обеспечения.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' По независимым данным, переговоры с Softline'
    ' закрытием не завершились: 23 декабря 2024 года «Атол» купил'
    ' Роман Володин, бывший гендиректор компании (выкуп менеджментом'
    ' у тех же продавцов, Алексея и Ирины Макаровых) — Softline вышла'
    ' из переговоров «из-за текущей ключевой ставки». Выручка «Атола»'
    ' за 2023 год выросла до 5,3 млрд ₽, чистая прибыль — до 227 млн ₽.'
)

NEW_SRC = [
    ['CNews', 'https://www.cnews.ru/news/top/2024-12-23_osnovateli_krupnogo_proizvoditelya'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
