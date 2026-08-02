# -*- coding: utf-8 -*-
"""Точечные правки, найденные живым обходом 50 карточек (1 августа, 5 персон).

ЧТО ЧИНИМ — каждый случай прочитан вручную и сверен с текстом самой карточки
до правки (см. `PRODUCT_ROADMAP.md`, прогон с разбором отчёта):

1. **`g075e9738` (VK / АО «Р7»).** `buyer` пуст, хотя заголовок и `eco.share`
   («сумма ... раскрыта в годовой отчётности VK») однозначно называют VK
   покупателем. Профиль VK уже есть в базе (`g4e694234`) — связываем.
2. **`gbada7ff0` (РНКБ / ВТБ).** `buyer` пуст, хотя `eco.share` прямо пишет
   «Росимущество внесло 100% акций РНКБ в уставный капитал ВТБ». Профиль ВТБ
   уже есть (`gcafc31dc`) — связываем. `seller` («Росимущество») уже верен,
   не трогаем.
3. **`g552abe79` (Русатом ИР / «Квадра»).** Самая запутанная карточка:
   `target` ссылался на профиль ПОКУПАТЕЛЯ («Русатом Инфраструктурные
   решения»), а не на предмет сделки («Квадра») — сторона и предмет
   перепутаны местами. Плюс `eco.finadv` и `law.adv` относятся к ДРУГОЙ,
   более ранней сделке (покупка 82,47% у «Онэксима» в январе 2022 — той
   карточки в базе нет) — оценщика и консультанта той сделки показывали как
   консультантов ЭТОЙ (выкуп 12,55% у миноритариев в июне 2022), а
   `law.adv` третьим элементом нёс не описание работы консультанта, а
   служебную метку пайплайна «Источник: обогащение/веб-поиск» — то, что
   пользователь видеть не должен. Правим: `target`→«Квадра», `buyer`→«Русатом
   ИР», `seller` — текстом «Миноритарные акционеры «Квадры»» (сторона
   реальна, но это не одна компания — профиля для группы нет и быть не
   может), `eco.finadv`/`eco.val` — на честное «—» (не досочиняем
   консультанта и оценку для сделки, где их не было), `law.adv` — пусто.
   Текст `extra` про январскую сделку — законный фон (объясняет, откуда у
   РИР взялись первые 82,47%), не трогаем.
4. **`g089e507d` (Займер / БЭСТ).** `asset` хранит обрывок заголовка в
   родительном падеже («платежной системы БЭСТ») — та же ошибка, что уже
   чинили для доли в имени компании, только здесь испорчен падеж, а не
   вырезана доля. Приводим к именительному.
5. **`g8b2e2afd` (завод «Карат»).** `seller_id` пуст, хотя и заголовок, и
   `eco.rationale` называют продавца — Александра Клячина (через Gleden
   Invest). Профиль уже есть (`gb9c8945c`, использован продавцом и в другой
   карточке, `gf3c5069f`) — связываем.

Профили компаний (два случая «имя в родительном падеже», тот же класс, что
уже чинили для долей в имени):
6. `g0773a305`: «Новой охотской рудной компании» → «Новая Охотская Рудная
   Компания» (НОРК).
7. `g6d8a19ee`: «Квадры» → «Квадра».

ЧЕГО НЕ ДЕЛАЕМ. Не создаём отдельную карточку под январскую сделку
«Русатом/Онэксим» — для неё нет собственного текста и источников с разбором
роли консультантов, только упоминание внутри карточки о выкупе миноритариев;
досочинять её означало бы нарушить принцип «переносить факт можно, сочинять
нельзя».

Запуск:
    python3 pipeline/fix_persona_review_findings.py            # сухой прогон
    python3 pipeline/fix_persona_review_findings.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

DEAL_FIXES = {
    'g075e9738': {'buyer': 'g4e694234'},
    'gbada7ff0': {'buyer': 'gcafc31dc'},
    'g552abe79': {
        'target': 'g6d8a19ee',
        'buyer': 'gb7a1b8d6',
        'seller': 'Миноритарные акционеры «Квадры»',
    },
    'g089e507d': {'asset': 'Платёжная система БЭСТ'},
    'g8b2e2afd': {'seller_id': 'gb9c8945c'},
}
# Проверка исходного состояния — если поле уже не такое, как мы ожидали
# (кто-то поправил раньше нас), скрипт останавливается, а не переписывает
# поверх чужой правки.
DEAL_FIXES_EXPECTED_OLD = {
    'g075e9738': {'buyer': None},
    'gbada7ff0': {'buyer': None},
    'g552abe79': {'target': 'gb7a1b8d6', 'buyer': None, 'seller': None},
    'g089e507d': {'asset': 'платежной системы БЭСТ'},
    'g8b2e2afd': {'seller_id': None},
}
ECO_FIXES = {
    'g552abe79': {'finadv': '—', 'val': '—'},
}
ECO_FIXES_EXPECTED_OLD = {
    'g552abe79': {
        'finadv': 'PwC — оценка 100% акций «Квадры» в сентябре 2021 года в рамках подготовки к первичной сделке (по заказу «Онэксима»)',
        'val': '3 млрд ₽ (за 12,55% акций в рамках обязательной оферты; сделка по приобретению контрольного пакета 82,47% у группы «Онэксим» — ~26 млрд ₽ по данным источников Интерфакса)',
    },
}
LAW_ADV_CLEAR = {'g552abe79'}

COMPANY_NAME_FIXES = {
    'g0773a305': ('Новой охотской рудной компании', 'Новая Охотская Рудная Компания'),
    'g6d8a19ee': ('Квадры', 'Квадра'),
}


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    by_id = {d['id']: d for d in data['deals']}
    changes = []

    for did, fields in DEAL_FIXES.items():
        d = by_id[did]
        for key, new in fields.items():
            old_expected = DEAL_FIXES_EXPECTED_OLD[did][key]
            old_actual = d.get(key)
            assert old_actual == old_expected, \
                f'{did}.{key}: ожидали {old_expected!r}, нашли {old_actual!r}'
            changes.append((did, key, old_actual, new))
            if write:
                d[key] = new

    for did, fields in ECO_FIXES.items():
        eco = by_id[did].setdefault('eco', {})
        for key, new in fields.items():
            old_expected = ECO_FIXES_EXPECTED_OLD[did][key]
            old_actual = eco.get(key)
            assert old_actual == old_expected, \
                f'{did}.eco.{key}: ожидали {old_expected!r}, нашли {old_actual!r}'
            changes.append((did, 'eco.' + key, old_actual, new))
            if write:
                eco[key] = new

    for did in LAW_ADV_CLEAR:
        law = by_id[did].setdefault('law', {})
        old = law.get('adv')
        assert old == [['Консультант онэксим (продавец)', 'Никольская Консалтинг', 'Источник: обогащение/веб-поиск']], \
            f'{did}.law.adv изменился с прошлого замера: {old!r}'
        changes.append((did, 'law.adv', old, []))
        if write:
            law['adv'] = []

    for cid, (old_expected, new) in COMPANY_NAME_FIXES.items():
        c = data['companies'][cid]
        old_actual = c.get('name')
        assert old_actual == old_expected, \
            f'{cid}.name: ожидали {old_expected!r}, нашли {old_actual!r}'
        changes.append((cid, 'company.name', old_actual, new))
        if write:
            c['name'] = new

    print(f'правок: {len(changes)}')
    for obj_id, field, old, new in changes:
        print(f'  {obj_id} [{field}]: {old!r} -> {new!r}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
