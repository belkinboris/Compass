# -*- coding: utf-8 -*-
"""Месячная очередь, 9 сентября 2026 — дочитывание карточки `g37a1b2e2`
(«"МТС-Банк" привлёк около 4 млрд ₽ через дополнительную эмиссию акций»,
добавлена в базу 8 сентября 2026).

Дельта-поиск (саб-агент + личная проверка) нашёл точные параметры
размещения и реакцию котировок. Личный WebFetch подтвердил дословно:

- preqveca.ru: «Итоговая цена размещения — 1 380.50» ₽ за акцию (диапазон
  был «1 300.00»–«1 600.00» ₽), размещено «2 897 574» акций.
- vc.ru: «Цена размещения составила 1380,5 рублей за бумагу», «Объём
  дополнительного размещения (SPO) составил почти 2,9 млн обыкновенных
  акций», «После SPO бумаги «МТС Банка» на Мосбирже выросли на 0,88% по
  сравнению с предыдущей торговой сессией».

Кто выкупил акции допэмиссии, ни один источник не называет — это остаётся
честной пустотой (саб-агент нашёл только предположение аналитиков ДО
размещения, а не факт по его итогам, — записывать его не стал).

Запуск:
    python3 pipeline/fix_mts_bank_spo_price_and_reaction.py            # сухой прогон
    python3 pipeline/fix_mts_bank_spo_price_and_reaction.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_SHARE = (
    'ПАО «МТС-Банк» провело дополнительную эмиссию акций и привлекло в '
    'капитал около 4 млрд ₽.'
)
NEW_ECO_SHARE = OLD_ECO_SHARE + (
    ' Размещено 2 897 574 акции по цене 1380,5 ₽ за штуку (диапазон был '
    '1300–1600 ₽ за акцию).'
)

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'После завершения SPO бумаги «МТС-Банка» на Московской бирже выросли '
    'на 0,88% по сравнению с предыдущей торговой сессией.'
)

NEW_SRC = [
    ['preqveca.ru', 'https://preqveca.ru/placements/651/'],
    ['VC.ru', 'https://vc.ru/invest/2097534-mts-bank-privlek-4-mlrd-rublej'],
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g37a1b2e2']

    assert d['eco']['share'] == OLD_ECO_SHARE, \
        'g37a1b2e2 eco.share уже другой: %r' % (d['eco']['share'],)
    assert d['eco']['context'] == OLD_ECO_CONTEXT, \
        'g37a1b2e2 eco.context уже другой: %r' % (d['eco']['context'],)
    urls = {s[1] for s in d['src']}
    for src in NEW_SRC:
        assert src[1] not in urls, 'источник уже добавлен: %s' % src[1]

    print('g37a1b2e2: eco.share дополнен (цена 1380,5 ₽/акцию, диапазон '
          '1300–1600 ₽, 2 897 574 акции); eco.context заполнен '
          '(котировки +0,88% после SPO); добавлены источники preqveca.ru, '
          'vc.ru')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['share'] = NEW_ECO_SHARE
    d['eco']['context'] = NEW_ECO_CONTEXT
    d['src'].extend(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
