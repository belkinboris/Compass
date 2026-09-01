# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g99f062be (Verra выкупила автосалон «Обухов» в Перми, закрыта 1 ноября
2023) — здание превратилось в мультибрендовый центр под несколькими
марками Verra, а не осталось моносалоном Geely.

Проверено лично прямым WebFetch (Verra.ru, новость от 10.09.2024,
https://verra.ru/news/zhdem-vas-v-gac-verra-po-novomu-adresu-v-permi):
«С 15 сентября мы рады встрече с Вами по новому адресу: Шоссе
Космонавтов, 332А» — салон марки GAC переехал именно в купленное у
«Обухова» здание. По данным саб-агента (2ГИС, не дозаверено отдельным
WebFetch, но независимый агрегатор): по тому же адресу сейчас также
работают дилерские центры Geely и Belgee под брендом Verra.

НЕ ВКЛЮЧЕНО: судьба прежнего владельца, ГК «Обухов», в Перми —
саб-агент предположил полный уход компании из города (Пермь
отсутствует в списке дилерских центров на obukhov.ru), но при
самостоятельной проверке (прямой WebFetch obukhov.ru) на сайте всё ещё
есть переключатель города «Москва / Пермь» без работающей ссылки, а
редирект с perm.obukhov.ru ведёт на страницу без Перми вовсе —
результат противоречивый, факт не настолько чист, чтобы записывать его
как утверждение; судьба сервисного обслуживания клиентов Volvo в
здании — ни один источник не подтверждает и не опровергает, продолжается
ли оно сейчас; официальная сумма сделки задним числом — по-прежнему не
раскрыта, все источники повторяют ту же оценку 150–250 млн ₽, что уже
была в карточке.

Запуск: python3 pipeline/fix_verra_obukhov_multibrand_expansion.py
        python3 pipeline/fix_verra_obukhov_multibrand_expansion.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g99f062be'

OLD_EXTRA = (
    'Сделка касается выкупа пермского автосалона «Обухов-Урал» '
    'компанией Verra. Закрыта в ноябре 2023 года.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Здание стало мультибрендовым центром: с 15 сентября 2024 года '
    'сюда переехал салон марки GAC, работающий под брендом Verra наряду '
    'с уже открытыми здесь дилерскими центрами других марок.'
)

NEW_SRC = [
    ['Verra.ru', 'https://verra.ru/news/zhdem-vas-v-gac-verra-po-novomu-adresu-v-permi'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
