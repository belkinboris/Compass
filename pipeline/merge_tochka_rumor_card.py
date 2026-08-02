# -*- coding: utf-8 -*-
"""Слух и его исход — две несвязанные карточки об одной сделке (Точка/Траст).

ЧТО СЛОМАНО. `g81670f73` — карточка от 1 января 2023 года, собранная по
единственному источнику (репост в @dealsma со ссылкой на Коммерсантъ):
«Траст продаёт 90% «Точки» банку «Тинькофф» за 20 млрд ₽», статус до сих пор
«Обсуждается». `gcd2b0954` — фактический исход, закрытый 25 августа 2023 года
и подтверждённый девятью источниками (Коммерсантъ, РБК, Forbes, Ведомости):
90,01% «Точки» ушли не «Тинькофф», а консорциуму во главе с «Интерросом»
(позже — VK и «1С»), и не за 20, а за 41,5 млрд ₽ на аукционе. Это не другая
сделка — тот же пакет той же «Точки» от того же «Траста», просто ранний слух
не подтвердился в частностях. Читатель, который найдёт только `g81670f73`
(он всё ещё висит как «обсуждается»), унесёт с собой сегодняшнюю дату, но
позавчерашние и попросту неверные покупателя и сумму.

ЧТО ДЕЛАЕМ.
1. У `gcd2b0954` чиним два самостоятельных дефекта, обнаруженных при чтении
   карточки для слияния (не связаны со слухом сами по себе):
   - `target` был `null`, а `target_was_seller` стоял `true` — по смыслу
     флага это значит «в target раньше лежал продавец, у предмета сделки нет
     профиля компании». Но профиль ЕСТЬ: `g09ccbaca`, «Банк «Точка»» — тот
     самый, на который верно ссылается предмет в карточке-слухе. Линкуем
     `target` и снимаем флаг (иначе на карточке всё равно висела бы сноска
     «отдельной карточки не имеет», хотя теперь имеет).
   - `buyer`/`buyer_name` были пусты, хотя из текста ясно, кто купил —
     консорциум, а не одна компания (профиля для консорциума быть не может).
     Заполняем `buyer_name` текстом из собственного заголовка карточки:
     «Консорциум инвесторов во главе с «Интерросом»» — дословно оттуда, не
     сочиняем.
   - Ранний источник (Коммерсантъ, 1 января) переносим в `src`: то же
     издание уже даёт остальные ссылки карточки, поэтому подписываем его
     тем же именем, а не ярлыком «@dealsma (Telegram)» из карточки-слуха —
     это ярлык ленты-агрегатора, а не издания, и сама ссылка ведёт на
     kommersant.ru напрямую.
2. Сливаем `g81670f73` в `gcd2b0954` тем же механизмом, что и Volkswagen
   (прогон 50, `merge_duplicate_deals.py`): `merged[g81670f73] = gcd2b0954`,
   карточка-слух убирается из `deals`, а её адрес (`#/deal/g81670f73`)
   продолжает открывать браузер — просто теперь ведёт на верную карточку,
   а не показывает общую ленту.

ЧТО ПРОВЕРЯЕТСЯ ПЕРЕД ЗАПИСЬЮ. Обе карточки на месте и в ожидаемом
состоянии; переносимый факт (текст консорциума) лежит в заголовке дословно;
переносимый URL отсутствует среди уже имеющихся источников; после слияния
число карточек уменьшается ровно на одну.

Запуск:
    python3 pipeline/merge_tochka_rumor_card.py            # сухой прогон
    python3 pipeline/merge_tochka_rumor_card.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

KEEP, DROP = 'gcd2b0954', 'g81670f73'

TARGET_CO = 'g09ccbaca'  # «Банк «Точка»»
BUYER_NAME = 'Консорциум инвесторов во главе с «Интерросом»'

EARLY_SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/5720795']


def norm(s):
    return ' '.join(str(s or '').split())


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    deals = data['deals']
    by_id = {d['id']: d for d in deals}

    keep, drop = by_id.get(KEEP), by_id.get(DROP)
    assert keep and drop, 'карточек пары нет в базе — состояние изменилось, скрипт остановлен'

    assert keep.get('target') is None and keep.get('target_was_seller') is True, \
        f'{KEEP}.target уже не в ожидаемом состоянии: target={keep.get("target")!r}, target_was_seller={keep.get("target_was_seller")!r}'
    assert not keep.get('buyer') and not keep.get('buyer_name'), \
        f'{KEEP}: покупатель уже заполнен'
    # В заголовке «консорциуму» стоит в дательном падеже («продажа … консорциуму
    # инвесторов…») — в buyer_name нужен именительный («Консорциум инвесторов…»,
    # так его называют в самой карточке дальше). Проверяем дословно всё, кроме
    # окончания первого слова — та же терпимость к падежу, что и у других правок
    # этой сессии (ФИО, названия компаний), не сочинение нового факта.
    buyer_pattern = re.compile(r'консорциум\w*' + re.escape(BUYER_NAME[len('Консорциум'):]), re.I)
    assert buyer_pattern.search(norm(keep.get('title'))), \
        'текст консорциума не лежит в заголовке дословно (с точностью до падежа) — переносить нечего'

    keep_urls = {norm(s[1]) for s in (keep.get('src') or []) if len(s) > 1}
    assert norm(EARLY_SRC[1]) not in keep_urls, 'ранний источник уже перенесён'

    drop_urls = {norm(s[1]) for s in (drop.get('src') or []) if len(s) > 1}
    assert norm(EARLY_SRC[1]) in drop_urls, 'ранний источник не лежит в карточке-слухе'

    assert drop.get('target') == TARGET_CO, \
        f'{DROP}.target изменился: {drop.get("target")!r}'

    print('ЧИНИМ САМОСТОЯТЕЛЬНЫЕ ДЕФЕКТЫ У', KEEP)
    print(f'  target: None -> {TARGET_CO} ({data["companies"][TARGET_CO]["name"]!r})')
    print(f'  target_was_seller: True -> убран')
    print(f'  buyer_name: None -> {BUYER_NAME!r}')
    print(f'  src: + {EARLY_SRC}')

    print('\nСЛИЯНИЕ СЛУХА И ИСХОДА')
    print('  оставляем %s  %s' % (KEEP, str(keep['title'])[:80]))
    print('  удаляем   %s  %s' % (DROP, str(drop['title'])[:80]))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    keep['target'] = TARGET_CO
    del keep['target_was_seller']
    keep['buyer_name'] = BUYER_NAME
    keep.setdefault('src', []).append(EARLY_SRC)

    was = len(deals)
    data['deals'] = [d for d in deals if d['id'] != DROP]
    assert len(data['deals']) == was - 1, 'удалилась не одна карточка'
    data.setdefault('merged', {})[DROP] = KEEP

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано. Карточек в базе: %d (было %d).' % (len(data['deals']), was))


if __name__ == '__main__':
    main('--write' in sys.argv)
