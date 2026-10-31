# -*- coding: utf-8 -*-
"""Приток 24 сентября 2026 (14:20 МСК), карточка g2daf32fe («Ашан» в России
передан во временное управление по указу Президента РФ, ожидает публикации
в pending.json): дополнение из RB.ru — источники «Известий» связывают
передачу Auchan и «Лемана ПРО» под временное управление в том числе с их
развитой складской логистикой (масштаб инфраструктуры — возможный мотив
интереса государства к этим активам), плюс отдельная цитата о том, что
режим временного управления не исключает будущей продажи бизнеса.

Прямым скриптом, не через review.py FIXES: law.struct уже содержит текст,
а дописывание к уже стоящему полю не проходит генерик-проверку check()
(та же причина, что и для gb7ea4703/g17fc21d6/gmru-nspk-privatization,
см. KNOWN_ISSUES.md).

Источник: https://rb.ru/news/auchan-pytalsya-prodat-rossijskij-biznes-sdelka-sorvalas-posle-vvedeniya-vremennogo-upravleniya/,
прочитан целиком, кэш в data/inbox/raw/2026-09-24-articles.jsonl.

Запуск: python3 pipeline/fix_auchan_lemana_logistics_2026_09_24.py --write
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g2daf32fe'
RB_RU = ['RB.ru', 'https://rb.ru/news/auchan-pytalsya-prodat-rossijskij-biznes-sdelka-sorvalas-posle-vvedeniya-vremennogo-upravleniya/']

OLD_STRUCT = (
    'Президент России Владимир Путин передал во временное управление АО '
    '«Л.Е.В. Менеджмент» российские активы Nestlé, логистической компании '
    'FM Logistic, сети строительных гипермаркетов «Лемана ПРО» и «Ашана». '
    'Это следует из указа главы государства от 17 сентября. Он вступает в '
    'силу со дня официального опубликования.'
)
QUOTE_ADD = (
    'Источники «Известий» связывают передачу Auchan и «Лемана ПРО» под '
    'временное управление в том числе с их развитой складской '
    'инфраструктурой. По данным Auchan, на которые ссылается издание, '
    'ритейлер управлял восемью логистическими центрами общей площадью '
    'около 250 тыс. кв. м. У «Лемана ПРО» — 17 складских комплексов '
    'площадью 900 тыс. кв. м. Режим временного управления не исключает '
    'продажу бизнеса в будущем: он ограничивает владельца в распоряжении '
    'активом (ранее поданное заявление на согласование сделки больше не '
    'действует), но, по словам экспертов «Известий», собственник может '
    'обсуждать условия будущей сделки, хотя его возможности распоряжаться '
    'бизнесом на период действия режима существенно ограничены.'
)


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)

    assert card['law']['struct'] == OLD_STRUCT
    card['law']['struct'] = OLD_STRUCT + ' ' + QUOTE_ADD

    if RB_RU[1] not in {s[1] for s in card['src'] if len(s) > 1}:
        card['src'].append(RB_RU)

    if write:
        json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано: law.struct дополнен, источник добавлен.')
    else:
        print('Сухой прогон (--write, чтобы записать).')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
