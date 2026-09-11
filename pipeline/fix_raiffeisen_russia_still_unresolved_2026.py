# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — дочитывание карточки
`c61052e8d` («Raiffeisen Bank International планирует выделение
российского подразделения», 1 марта 2023, weekly_researched 10 августа
2026). Карточка описывала только ПЛАН на март 2023 года — что стало с
ним за три с половиной года, было неизвестно.

Дельта-поиск (саб-агент + личная проверка WebFetch) установил: сделка
ДО СИХ ПОР не состоялась ни в каком виде.

Личный WebFetch подтвердил дословно (The Moscow Times, 1 октября 2025,
https://www.themoscowtimes.com/2025/10/01/austrias-raiffeisen-bank-fails-again-to-exit-russia-as-authorities-block-sale-reuters-a90683):

1) «Russian authorities blocked the deal out of fears that transferring
   ownership to local investors could trigger Western sanctions against
   RBI» — попытка продажи местному покупателю заблокирована российскими
   властями осенью 2025 года.
2) «Moscow wants to preserve remaining economic ties with Europe...
   Raiffeisen processes payments for fuel deliveries through the
   TurkStream pipeline» — причина: банк нужен как канал платежей за
   поставки топлива.
3) «the bank has accumulated around 7 billion euros in profits in
   Russia — funds that remain effectively trapped in the country».

И (Investing.com, 31 июля 2026, отчёт RBI за I полугодие,
https://www.investing.com/news/company-news/raiffeisen-h1-2026-slides-profit-up-25-russia-exit-accelerates-93CH-4828633):

4) «maintaining the run-down as the base case with continued
   ring-fencing, extracting value through legal claims including the
   Rasperia filing on July 30, 2026, and pursuing renewed sale
   efforts» — три направления усилий, включая новый судебный иск.
5) «reduced Russian customer deposits from EUR 29.5 billion to EUR
   10.9 billion and loans from EUR 13.7 billion to EUR 2.5 billion»
   (с 2022 года).

НЕ внесено: конкретный покупатель (не назван ни в одном источнике);
срок сделки (RBI отказывается называть); варианты 2023-2024 годов
(buyback, обмен с УГМК/Сбербанком) — ни один источник не подтверждает
их как состоявшуюся сделку, само предположение о них не проверялось
отдельно и в карточку не вносится.

Запуск:
    python3 pipeline/fix_raiffeisen_russia_still_unresolved_2026.py            # сухой прогон
    python3 pipeline/fix_raiffeisen_russia_still_unresolved_2026.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_CONTEXT = (
    'Raiffeisen находится под давлением США и ЕЦБ после того, как '
    'выяснилось: банк был среди тех, кого обязали участвовать в '
    'российской схеме отсрочки платежей по кредитам для войск, '
    'воюющих в Украине.'
)
NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' По состоянию на середину 2026 года сделка так и не состоялась. '
    'В октябре 2025 года российские власти заблокировали попытку '
    'продажи местному покупателю — опасаясь, что передача '
    'собственности местным инвесторам может спровоцировать новые '
    'западные санкции против RBI, а также желая сохранить банк как '
    'канал платежей за поставки топлива по «Турецкому потоку». У RBI '
    'в России заблокировано около 7 млрд € прибыли, накопленной с '
    '2022 года. В отчёте за первое полугодие 2026 года RBI назвал три '
    'направления: продолжение сворачивания бизнеса, извлечение '
    'стоимости через судебные иски (в том числе иск по Rasperia, '
    'поданный 30 июля 2026 года) и возобновлённые усилия по продаже — '
    'без названного покупателя и срока. Клиентские депозиты банка в '
    'России сократились с 29,5 млрд € до 10,9 млрд €, кредиты — с '
    '13,7 млрд € до 2,5 млрд € (с 2022 года).'
)

NEW_SRC = [
    ['The Moscow Times', 'https://www.themoscowtimes.com/2025/10/01/austrias-raiffeisen-bank-fails-again-to-exit-russia-as-authorities-block-sale-reuters-a90683'],
    ['Investing.com', 'https://www.investing.com/news/company-news/raiffeisen-h1-2026-slides-profit-up-25-russia-exit-accelerates-93CH-4828633'],
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['c61052e8d']

    assert d['eco']['context'] == OLD_ECO_CONTEXT, \
        'c61052e8d eco.context уже другой: %r' % (d['eco']['context'],)
    urls = {s[1] for s in d['src']}
    for src in NEW_SRC:
        assert src[1] not in urls, 'источник уже добавлен: %s' % src[1]

    print('c61052e8d: eco.context дополнен (сделка не состоялась, блок '
          'октября 2025, заблокированная прибыль 7 млрд €, отчёт RBI '
          'за I полугодие 2026); добавлены источники The Moscow Times, '
          'Investing.com')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['context'] = NEW_ECO_CONTEXT
    d['src'].extend(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
