# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gad2aea9d
(Raiffeisen Bank International отказался от покупки доли в Strabag SE) —
сделка сорвалась в мае 2024, но карточка не знала, что случилось с
исками и с самой долей за прошедшие почти два года. Проверено лично
прямым WebFetch пяти источников: RBI (два пресс-релиза), pravo.ru,
Strabag Newsroom, The Moscow Times.

`eco.context` (дополнено):

1) Первый иск «Распериа» (195 млрд ₽) — суд разрешил в пользу истца, RBI
обжалует. Дословно (RBI, вердикт апелляции от 24.04.2025): «EUR 2.044
billion plus interest» с АО Raiffeisenbank; «AO Raiffeisenbank will
appeal this verdict in the next instance in Russia».
https://www.rbinternational.com/en/raiffeisen/media-hub/press-releases/2025/rasperia-second-instance-verdict.html

2) Второй, ОТДЕЛЬНЫЙ иск «Распериа» (€339 млн, 18.12.2025) — основание:
«non-receipt by Rasperia of monetary compensation related to the
reduction of STRABAG's authorized capital in 2024, unpaid dividends from
STRABAG for 2024». RBI снова обжалует: «AO Raiffeisenbank will appeal
this verdict with suspensive effect».
https://www.rbinternational.com/en/investors/news/ir-releases/rasperia-2-verdict.html

3) Доля НЕ осталась у «Илиадиса» — вернулась к прежнему владельцу.
Дословно (pravo.ru): «Весной 2024 года стало известно о переходе
компании в собственность «Илиадиса». Сумма составила 7 млрд руб.» —
затем «Илиадис» потребовал «отменить сделку в связи с изменением
стоимости актива после введения санкций», и «стороны решили спор во
внесудебном порядке, и «Распериа» вернули «Валтура холдингз лимитед»»
(январь 2025). https://pravo.ru/news/257041/

4) Австрийские акционеры Strabag отозвали параллельный арбитражный иск
в Амстердаме из-за угрозы штрафа российскому подразделению RBI.
Дословно: «A breach of this injunction would be fined with a lump-sum
penalty of €1.09 billion... against RBI's Russian subsidiary»; «the
STRABAG shares held by Rasperia remain frozen».
https://newsroom.strabag.com/en/press-releases/group/2025-09/core-shareholders-withdraw-arbitration-claim-in-amsterdam

5) RBI второй раз не смогла выйти из России. Дословно (The Moscow
Times/Reuters, 01.10.2025): «transferring ownership to local investors
could trigger Western sanctions against RBI, a crucial financial channel
for Moscow»; банк «found a local buyer for its stake», но власти сделку
заблокировали.
https://www.themoscowtimes.com/2025/10/01/austrias-raiffeisen-bank-fails-again-to-exit-russia-as-authorities-block-sale-reuters-a90683

НЕ ВКЛЮЧЕНО: судьба обеспечительных мер на акции Райффайзенбанка (снят
арест или нет) — не нашлась в открытых источниках; цифры сокращения
депозитов/кредитов RBI с 2022 года — встретились только в резюме
поисковика без дословной цитаты первоисточника, не подтверждены;
консультанты — не найдены ни в одном источнике.

Запуск: python3 pipeline/fix_raiffeisen_strabag_lawsuit_saga.py
        python3 pipeline/fix_raiffeisen_strabag_lawsuit_saga.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gad2aea9d'

OLD_CONTEXT = (
    'При этом строительная компания Strabag отмечала, что «Расперия» '
    'больше не контролируется Олегом Дерипаской, а пакет акций, '
    'принадлежащих «Распериа» (24,1%), остается замороженным в '
    'соответствии с положением о санкциях ЕС. 14 мая МКАО «Распериа '
    'Трейдинг Лимитед» и АО «Илиадис» были включены в санкционный список '
    'США, а затем и ЕС.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Судьба доли и исков за 2025 год: доля НЕ осталась у «Илиадиса» — '
    'после того как «Илиадис» потребовал отменить покупку из-за санкций, '
    '«стороны решили спор во внесудебном порядке, и «Распериа» вернули '
    '«Валтура холдингз лимитед»» (январь 2025, pravo.ru). Первый иск '
    '«Распериа» к Strabag/Райффайзенбанку суд разрешил в пользу истца: '
    'апелляция 24 апреля 2025 подтвердила взыскание «EUR 2.044 billion '
    'plus interest», RBI обжалует далее (RBI, пресс-релиз). 18 декабря '
    '2025 суд удовлетворил ВТОРОЙ, отдельный иск «Распериа» на €339 млн '
    '— «non-receipt by Rasperia of monetary compensation related to the '
    'reduction of STRABAG\'s authorized capital in 2024, unpaid dividends '
    'from STRABAG for 2024» — RBI снова обжалует (RBI, пресс-релиз). В '
    'сентябре 2025 австрийские акционеры Strabag отозвали параллельный '
    'иск в Амстердамском арбитраже из-за угрозы штрафа в €1,09 млрд '
    'российскому подразделению RBI; акции Strabag, принадлежащие '
    '«Распериа», остаются заморожеными (Strabag Newsroom). В октябре '
    '2025 RBI второй раз не смогла выйти из России: власти заблокировали '
    'продажу найденному местному покупателю, «опасаясь, что передача '
    'местным инвесторам вызовет санкции против RBI» (The Moscow '
    'Times/Reuters).'
)

NEW_SRC = [
    ['RBI', 'https://www.rbinternational.com/en/raiffeisen/media-hub/press-releases/2025/rasperia-second-instance-verdict.html'],
    ['RBI', 'https://www.rbinternational.com/en/investors/news/ir-releases/rasperia-2-verdict.html'],
    ['pravo.ru', 'https://pravo.ru/news/257041/'],
    ['Strabag Newsroom', 'https://newsroom.strabag.com/en/press-releases/group/2025-09/core-shareholders-withdraw-arbitration-claim-in-amsterdam'],
    ['The Moscow Times', 'https://www.themoscowtimes.com/2025/10/01/austrias-raiffeisen-bank-fails-again-to-exit-russia-as-authorities-block-sale-reuters-a90683'],
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
    print('\n=== src добавится ===')
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
