# -*- coding: utf-8 -*-
"""Месячная очередь, 9 сентября 2026 — дочитывание карточки `geb221705`
(«X5 Group приобрела 100% цифровой площадки MAY24 (ООО "МАЙ24")»,
добавлена в базу 3 августа 2026, полностью обыскана в тот же день).

Дельта-поиск (саб-агент + личная проверка) нашёл два новых факта:

1) Роль компании «Май» после сделки. Личный WebFetch (comnews.ru,
   3 октября 2024) подтвердил дословно: «После завершения сделки Компания
   «Май» будет выполнять роль стратегического партнера для X5 в
   дальнейшем развитии системы цифровой дистрибуции товаров.»

2) Ребрендинг платформы. Личный WebFetch (foodretail.ru, 6 марта 2025)
   подтвердил дословно: «Компания X5 Group объявила о планах по
   изменению бренда своей платформы MAY24, которая теперь будет носить
   название OKOLO.Market»; «В январе 2025 года компания уменьшила размер
   вознаграждения для внешних поставщиков до символического 0,01% от
   товарооборота.»

Саб-агент также нашёл цитату основателя Игоря Лисиненко о дальнейшем
развитии маркетплейса — источник (vedomosti.ru) оказался за платным
доступом, лично процитировать не удалось, поэтому эта деталь НЕ вносится
без прямой проверки. Сумма сделки и финансовый консультант по-прежнему
нигде не названы — карточка права, что оставляет их как есть.

Запуск:
    python3 pipeline/fix_x5_may24_okolo_market_rebrand.py            # сухой прогон
    python3 pipeline/fix_x5_may24_okolo_market_rebrand.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_CONTEXT = (
    'MAY24 — цифровая торговая площадка: она помогает производителям и '
    'дистрибьюторам товаров повседневного спроса продавать их '
    'региональным торговым сетям и независимым магазинам несетевой '
    'розницы. Площадка объединяет более 200 производителей и '
    'дистрибьюторов, которые поставляют товары в 65 российских '
    'регионов.'
)
NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' После сделки компания «Май» стала стратегическим партнёром X5 в '
    'развитии системы цифровой дистрибуции. В марте 2025 года платформа '
    'была переименована в OKOLO.Market; в январе 2025 года вознаграждение '
    'для внешних поставщиков снижено до 0,01% от товарооборота.'
)

NEW_SRC = [
    ['ComNews', 'https://www.comnews.ru/content/235545/2024-10-03/2024-w40/1010/kh5-priobrel-platformu-may24-kompanii-may'],
    ['Foodretail.ru', 'https://foodretail.ru/news/x5-provedet-rebrending-platformi-may24-pereimenovav-ee-v-okolomarket-474541'],
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['geb221705']

    assert d['eco']['context'] == OLD_ECO_CONTEXT, \
        'geb221705 eco.context уже другой: %r' % (d['eco']['context'],)
    urls = {s[1] for s in d['src']}
    for src in NEW_SRC:
        assert src[1] not in urls, 'источник уже добавлен: %s' % src[1]

    print('geb221705: eco.context дополнен (роль «Май», ребрендинг в '
          'OKOLO.Market); добавлены источники comnews.ru, foodretail.ru')

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
