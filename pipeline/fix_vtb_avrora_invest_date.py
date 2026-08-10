# -*- coding: utf-8 -*-
"""Карточка cd9abfbfd («Группа ВТБ продаёт акции АО «Аврора Инвест» —
акционера Первой грузовой компании») несла дату «2025-09-30» вместо
2024-12-16.

ЧТО СЛОМАНО. Карточка — компактная запись из рэнкинга «Ъ — Сделки года»
(`from_compact: mini`), и, видимо, унаследовала дату публикации самого
рэнкинга, а не дату сделки. AK&M прямо датирует сообщение: «ВТБ продал
компанию «Аврора Инвест» AK&M 16 декабря 2024 17:32 ... Банк ВТБ вышел из
капитала АО «Аврора Инвест», владеющей Первой грузовой компанией: 100%
компании ... продано с хорошей прибылью для банка. Сделка закрыта».
Родня уже исправленных карточек этой сессии (cb50ea645, g2369d101,
gf9b54ee7, gd7c2b9ee, g98a85532, g7e470153) — год-заглушка компактного
импорта поставила не тот год, здесь ещё и не тот день/месяц.

ПОЧЕМУ НЕ ЧЕРЕЗ `review.py`. `date_is_supported()` намеренно запрещает
менять год — перенос года обязан быть отдельным, явным решением с
проверяемым источником, а не автоматической правкой в общей таблице.

Карточка этим переносом выходит из среза 2025 года (переходит в 2024).

Запуск:
    python3 pipeline/fix_vtb_avrora_invest_date.py            # сухой прогон
    python3 pipeline/fix_vtb_avrora_invest_date.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
DEAL_ID = 'cd9abfbfd'
OLD_DATE = '2025-09-30'
NEW_DATE = '2024-12-16'
QUOTE = ('AK&M, 16 декабря 2024 17:32: «Банк ВТБ вышел из капитала АО '
         '«Аврора Инвест», владеющей Первой грузовой компанией: 100% '
         'компании ... продано с хорошей прибылью для банка. Сделка '
         'закрыта»')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('date') == OLD_DATE, \
        'дата уже другая: %r, ожидали %r' % (deal.get('date'), OLD_DATE)

    print('%s: date %r -> %r' % (DEAL_ID, OLD_DATE, NEW_DATE))
    print('  цитата: %r' % QUOTE)

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    deal['date'] = NEW_DATE
    assert deal['date'] == NEW_DATE, 'дата не записалась'

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
