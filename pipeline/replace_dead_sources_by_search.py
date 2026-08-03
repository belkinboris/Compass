# -*- coding: utf-8 -*-
"""Мёртвые ссылки, найденные живым поиском: замена на статью того же события.

ЗАЧЕМ. После починки разбором адреса осталось десять карточек с мёртвой
единственной ссылкой. По шести нашлась публикация деловых СМИ о ТОЙ ЖЕ
сделке — она и ставится источником.

КАК ПРОВЕРЯЛОСЬ СОВПАДЕНИЕ. Не по совпадению слов в адресе (урок про «слаг,
не называющий стороны, — не доказательство»), а по содержанию найденной
статьи: стороны, предмет и дата должны совпадать с карточкой. Например у
«36,6» карточка говорит о закрытии сделки по «ЛекОптТорг» и «Родник
здоровья» 1 октября 2023 года — статья «Ведомостей» от 17 октября 2023 года
описывает ровно эту сделку и тех же продавцов. Каждый новый адрес перед
записью запрашивается: в базу идёт только ответивший 200.

ПОЧЕМУ У «36,6» НЕ VADEMECUM. Поиск возвращает статью Vademecum с тем же
адресом, что уже стоит в карточке, — а он отвечает 404. Живой поисковый
индекс помнит страницу, которой на сайте больше нет; проверка кодом ответа
это ловит, а доверие выдаче — нет.

ЧТО ОСТАЁТСЯ БЕЗ ИСТОЧНИКА. Четыре карточки. Две из них («Ред Софт»)
собраны по ЕГРЮЛ, а не по публикации: пресса об этих изменениях долей не
писала, и подставлять статью «про ту же компанию» нельзя — это ровно тот
случай, когда рабочая ссылка на чужую страницу хуже видимого 404. Ещё две
(«Степь» в Ростовской области, раунд DentalPro) освещались только
региональными и отраслевыми изданиями, чьи страницы удалены. Ссылки у них не
стёрты: пустой список источников — не более честное решение, а другое
нарушение (`test_every_deal_has_a_source_link`).

Запуск:
    python3 pipeline/replace_dead_sources_by_search.py            # сухой прогон
    python3 pipeline/replace_dead_sources_by_search.py --write    # записать
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; KompasBot/1.0)'}

# id карточки -> (подпись издания, адрес статьи о ТОЙ ЖЕ сделке).
FOUND = {
    # У РБК тоже есть статья об этой сделке, но rbc.ru отвечает роботу 401,
    # и проверить её кодом ответа нельзя. Берём «Коммерсантъ» о той же сделке:
    # источник, который мы можем подтвердить, лучше источника, про который
    # приходится верить поисковой выдаче на слово.
    'g1f098415': ('Коммерсантъ', 'https://www.kommersant.ru/doc/6098761'),
    'gc9e8bb60': ('Коммерсантъ', 'https://www.kommersant.ru/doc/5951579'),
    'g334b5760': ('Коммерсантъ', 'https://www.kommersant.ru/doc/7432590'),
    'gf8b3e66e': ('Ведомости',
                  'https://www.vedomosti.ru/business/articles/2023/10/17/1001064-366-priobrela-aptechnuyu-set'),
    'gb6b5625e': ('Коммерсантъ', 'https://www.kommersant.ru/doc/5873898'),
    'g51fbc8c8': ('Интерфакс', 'https://www.interfax.ru/business/1000914'),
}


def alive(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read(512)
            return resp.status
    except urllib.error.HTTPError as err:
        return err.code
    except Exception as err:
        return type(err).__name__


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    plan = []
    for deal_id, (label, url) in FOUND.items():
        deal = by_id.get(deal_id)
        assert deal is not None, 'карточки %s нет в базе' % deal_id
        assert len(deal.get('src') or []) == 1, \
            '%s: источников уже не один — решение принимать заново' % deal_id
        known = {str(s[1]) for s in deal['src'] if len(s) > 1}
        assert url not in known, '%s: ссылка уже стоит' % deal_id
        code = alive(url)
        print('%-13s %-52s %s' % (deal_id, str(deal.get('title'))[:52], code))
        if code == 200:
            plan.append((deal, label, url))
        else:
            print('    НЕ ЗАПИСЫВАЕМ: ответ %s' % code)

    print('\nзаменяем источник у %d карточек из %d' % (len(plan), len(FOUND)))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for deal, label, url in plan:
        # Старая ссылка не удаляется молча: она заменяется целиком, потому что
        # это единственный источник и он мёртв. Новая — о той же сделке.
        deal['src'] = [[label, url]]
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
