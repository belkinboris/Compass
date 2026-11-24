# -*- coding: utf-8 -*-
"""Карточка g9ba1f9f2 (завод «Кемма», Челябинск): заголовок не по стандарту
для «M&A», статус «Обсуждается» — находка `title_standard` в `accept_card.py`.

Было (действительный залог, завод как подлежащее): «Завод «Кемма» в
Челябинске выставил на продажу два цеха за 387 млн рублей».
Стандарт для продажи без покупателя (`pipeline/title_standard.py`, VERBS
[('M&A', TALKS)]) требует страдательный залог: «Y выставлен(а/о/ы) на
продажу [за N ₽]» — предмет сделки, а не завод, подлежащим.

Стало: «Два цеха завода «Кемма» в Челябинске выставлены на продажу за
387 млн рублей» — тот же набор фактов, своей фразой (не копия заголовка
URA.RU «Челябинский завод «Кемма» продает цеха за 387 миллиарда рублей» —
в заголовке источника к тому же опечатка «миллиарда» вместо «миллионов»,
исправленная в тексте статьи и не унаследованная карточкой).

ИСТОЧНИК: URA.RU, https://ura.news/news/1053146951

Запуск:
    python3 pipeline/fix_g9ba1f9f2_title_standard_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_g9ba1f9f2_title_standard_2026_11_24.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')
CARD_ID = 'g9ba1f9f2'
OLD_TITLE = 'Завод «Кемма» в Челябинске выставил на продажу два цеха за 387 млн рублей'
NEW_TITLE = 'Два цеха завода «Кемма» в Челябинске выставлены на продажу за 387 млн рублей'


def apply(data):
    card = next(c for c in data['cards'] if c['id'] == CARD_ID)
    assert card['title'] == OLD_TITLE, card['title']
    card['title'] = NEW_TITLE


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    print('Карточка %s: заголовок -> %s' % (CARD_ID, NEW_TITLE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv[1:]))
