# -*- coding: utf-8 -*-
"""Дневная очередь (REVISION_BRIEF, первый уровень), g3dcf441e («Минфин
продаст на бирже до 23,76% госпакета акций «Аэрофлота»», добавлена
2 сентября 2026) — НАЙДЕНА ОШИБКА ПРИТОКА того же класса, что уже не
раз описан в CLAUDE.md («Стороной сделки может быть записан профиль
совсем другой сущности» / путаница «предмет вместо стороны»):
`seller_id` карточки указывал на профиль ПАО «Аэрофлот» — то есть
предмет сделки был ошибочно записан продавцом САМОГО СЕБЯ. `target`
при этом стоял пустым.

Проверено лично прямым WebFetch (Коммерсантъ,
https://www.kommersant.ru/doc/8779715): цитата первого замгендиректора
«Аэрофлота» по коммерции и финансам Андрея Чиханчина на годовом
собрании акционеров 29 июня 2026 года — «Первое, что надо отметить,
продает государство, а не "Аэрофлот". Не будет дополнительной эмиссии
акций, будет их прямая продажа» — прямое опровержение самой компанией
той роли, которую ей ошибочно приписала карточка.

Проверено лично прямым WebFetch (Интерфакс,
https://www.interfax.ru/business/1091297, 22 мая 2026 — настоящий
первоисточник майского объявления, взамен вторичных Sostav.ru/
Mail.ru): «Государство выставит на продажу 23,76% акций ПАО "Аэрофлот
- российские авиалинии"»; «Государство контролирует 73,8% акций
компании»; «Рыночная цена 23,76%-ной доли, исходя из текущих
котировок на "Московской бирже" (чуть выше 47 рублей за акцию),
составляет порядка 44,5 млрд рублей».

Правка: `target` = профиль «Аэрофлот» (gf3ed02a1, тот же id, что
раньше ошибочно стоял в `seller_id`); `seller_id` = профиль
«Росимущество» (g9fd82fee — уже верно используется в карточках-сёстрах
о Шереметьево и НМТП того же дня); источники дополнены авторитетным
Интерфаксом и Коммерсантом (Sostav/Mail.ru оставлены в списке —
дублировать факт другим изданием не значит удалять уже стоявшую
ссылку).

НЕ ВКЛЮЧЕНО: дисконт к рыночной цене (5-10%) — это оценка аналитика
Freedom Finance Global, а не факт сделки, и относится к КОСВЕННО другой
метрике (ожидаемая цена размещения, а не оценка пакета) — не путать с
`eco.val`, куда идёт именно оценка стоимости пакета; общая сумма
ожидаемых бюджетных поступлений от ВСЕЙ программы приватизации 2026
года — не нашлась ни в одном источнике целиком, только по отдельным
активам.

Запуск: python3 pipeline/fix_aeroflot_spo_seller_target_swap.py
        python3 pipeline/fix_aeroflot_spo_seller_target_swap.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g3dcf441e'

OLD_TARGET = None
NEW_TARGET = 'gf3ed02a1'

OLD_SELLER_ID = 'gf3ed02a1'
NEW_SELLER_ID = 'g9fd82fee'

OLD_ECO_VAL = '—'
NEW_ECO_VAL = (
    'Рыночная оценка на дату майского объявления (по котировкам '
    'Московской биржи, чуть выше 47 ₽ за акцию) — около 44,5 млрд ₽ за '
    'весь пакет.'
)

OLD_ECO_FINADV = 'Публично не сообщалось'
NEW_ECO_FINADV = 'АО «Сбербанк КИБ» — организатор размещения (выбран Росимуществом по итогам отбора, заявки принимались 22 мая — 8 июня 2026).'

NEW_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/1091297'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8779715'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('target') == OLD_TARGET
    assert deal.get('seller_id') == OLD_SELLER_ID
    assert deal['eco']['val'] == OLD_ECO_VAL
    assert deal['eco']['finadv'] == OLD_ECO_FINADV

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== target: станет ===')
    print(NEW_TARGET, '(Аэрофлот)')
    print('\n=== seller_id: станет ===')
    print(NEW_SELLER_ID, '(Росимущество)')
    print('\n=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    print('\n=== eco.finadv: станет ===')
    print(NEW_ECO_FINADV)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['target'] = NEW_TARGET
        deal['seller_id'] = NEW_SELLER_ID
        deal['eco']['val'] = NEW_ECO_VAL
        deal['eco']['finadv'] = NEW_ECO_FINADV
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
