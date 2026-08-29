# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g5190658a
(GBM Holding купила 75% BCS Prime Brokerage, британское подразделение
БКС). Карточка не называла продавца вовсе, хотя он уже упомянут текстом в
`extra`. Проверено лично прямым WebFetch (AKM — англоязычный пересказ со
ссылкой на пресс-релиз GBM, не прямая цитата Bloomberg — помечено в
тексте как таковое, а не выдано за дословную цитату первоисточника).

1) `seller` (новое поле, текстом) — AKM, дословно: «Gerald Banks... '
acquired a large stake in BCS Prime, replacing the owner of the Russian '
parent company Oleg Mikhasenko» — Олег Михасенко назван владельцем
российской материнской компании БКС, чью долю в британском подразделении
и купил GBM Holding.

2) `eco.rationale` (новое поле) — причина продажи, тот же источник:
«Western sanctions imposed in 2022... negatively affected Russian
financial companies' UK operations», после чего «FG BCS decided to sell
90.1% of the British subsidiary... to a third-party investor and refocus
on the international business and exit the Russian business of the BCS
group» (доля в намерении конца 2023 года — 90,1%, к закрытию сделки в
июле 2024 могла измениться до заявленных в заголовке 75%; расхождение
зафиксировано честно, не выровнено механически).

3) `eco.context` (новое поле) — судьба актива: дивиденд перед сделкой и
ребрендинг. AKM, дословно: «A few days before the takeover, BCS Prime
Brokerage paid a special dividend of $27.5 million» (это дивиденд, не
цена сделки — не идёт в `sum`); «BCS Prime Brokerage will operate under
the new GBM Securities brand, focused on emerging and frontier markets».
Офисы (gbmsecurities.com): Лондон — «Headquarters and operational
center», Токио — «Home to GBM Asset Management».

НЕ включены: консультанты сделки — не найдены ни в одном источнике;
кадровые назначения GBM Securities 2026 года (Мария Анцупова) — не
относятся к самой сделке, а к текущей операционной жизни компании;
регуляторных проблем/штрафов FCA у GBM Securities не найдено.

Запуск: python3 pipeline/fix_gbm_bcs_prime_seller_and_rebrand.py
        python3 pipeline/fix_gbm_bcs_prime_seller_and_rebrand.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g5190658a'

NEW_SELLER = 'Олег Михасенко (владелец ФГ БКС)'

NEW_RATIONALE = (
    '«Western sanctions imposed in 2022... negatively affected Russian '
    'financial companies\' UK operations», после чего ФГ БКС «decided to '
    'sell 90.1% of the British subsidiary... to a third-party investor '
    'and refocus on the international business and exit the Russian '
    'business of the BCS group» (AKM; доля в намерении конца 2023 года — '
    '90,1%, к закрытию сделки могла измениться до заявленных 75%).'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    '«A few days before the takeover, BCS Prime Brokerage paid a special '
    'dividend of $27.5 million» (дивиденд, не цена сделки). После '
    'закрытия компания «will operate under the new GBM Securities brand, '
    'focused on emerging and frontier markets»: Лондон — головной офис '
    '(«Headquarters and operational center»), Токио — «Home to GBM Asset '
    'Management» (AKM, gbmsecurities.com).'
)

NEW_SRC = [
    ['AKM', 'https://www.akm.ru/eng/news/gbm-holdings-acquired-the-british-business-of-bcs-prime-brokerage/'],
    ['gbmsecurities.com', 'https://www.gbmsecurities.com/about-us'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('seller') is None
    assert not deal['eco'].get('rationale')
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print(f'=== seller (новое поле): станет {NEW_SELLER!r} ===')
    print('=== eco.rationale (новое поле): станет ===')
    print(NEW_RATIONALE)
    print('=== eco.context (новое поле): станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['seller'] = NEW_SELLER
        deal['eco']['rationale'] = NEW_RATIONALE
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
