# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — «Собственники компании на её странице». Все три
уровня очереди дочитывания (дневная/недельная/месячная) впервые пусты
одновременно (11 сентября 2026, ~19:00 МСК) — переход на G-бэклог.

Вместо новых чтений: замер по УЖЕ СОБРАННОМУ тексту карточек (`eco`, `law`,
`extra`) на слова «бенефициар»/«подконтрольный»/«принадлежит», у которых
профиль стороны сделки (target/buyer/seller_id) ещё не несёт поле
`ownership`. Замер (11 сентября): 978 совпадений по мягкому шаблону,
из них по строгому шаблону («бенефициар»/«подконтрольн»/«конечный
владелец» — самые однозначные слова, без риска спутать факт О ЭТОЙ сделке
с фактом о структуре ВЛАДЕНИЯ компанией) — два бесспорных, не пересекающихся
с уже заполненными 47 профилями кандидата, у обоих факт уже мельком назван
и в прозе `desc` профиля (не новый факт — перенос в структуру):

- `g5d22aa06` (ООО «Группа Русская энергия», target сделки `g40d9cd2e`):
  «До сделки 100% «Русской энергии» принадлежало АО «Антрацит» (бенефициар
  — Лариса Пустовалова)» — источники РБК/Коммерсантъ, дата сделки
  18 марта 2026. АО «Антрацит» уже профиль в базе (`g337092b8`).
- `g81045bed` (Фонд «Бумеранг капитал», buyer сделки `g56989e44`):
  «Покупатель — инвестиционный фонд «Бумеранг капитал», подконтрольный
  экс-руководителю «Сбербанк Капитала» Вагану Гаспаряну» — Коммерсантъ,
  дата сделки 31 марта 2026. Гаспарян — не отдельный профиль (лишний
  профиль ради одной сделки не заводится), поле `id` пусто (тот же приём,
  что у «Марины Улахановой» в существующем пилоте).
- `gf15f54d1` (ООО «Юнирест» (Rostic's), target сделки `g1f2895c0`):
  личный WebFetch (Sostav.ru, 07.05.2026, https://www.sostav.ru/
  publication/franchajzi-rostic-s-poluchil-20-v-strukture-vladeltsa-
  seti-83666.html) подтвердил дословно: «франчайзи... IRB... получил 20%
  в капитале головной компании сети»; «Доля ООО «Смарт сервис ЛТД»
  Константина Котова и Андрея Осколкова сократилась с 97% до 77%»;
  «доля гендиректора «Юниреста» Татьяны Шаманской сохранилась на уровне
  3%» (данные ЕГРЮЛ). Три собственника после сделки: IRB — 20% (уже
  профиль базы, `g68204914`, сам покупатель сделки), «Смарт сервис ЛТД»
  — 77% (профиль `g3104e805`), Татьяна Шаманская — 3% (без профиля,
  как физлицо, не сторона сделки).

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass1.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass1.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g5d22aa06': [{
        'name': 'АО «Антрацит» (бенефициар — Лариса Пустовалова)',
        'id': 'g337092b8',
        'share': '100%',
        'as_of': '2026-03',
        'source': ['РБК', 'https://www.rbc.ru/business/25/03/2026/69c3e8ea9a79477845d9411d'],
    }],
    'g81045bed': [{
        'name': 'Ваган Гаспарян',
        'id': None,
        'as_of': '2026-03',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/8571846'],
    }],
    'gf15f54d1': [
        {
            'name': 'ООО «Смарт сервис ЛТД» (Константин Котов и Андрей Осколков)',
            'id': 'g3104e805',
            'share': '77%',
            'as_of': '2026-05',
            'source': ['Sostav.ru', 'https://www.sostav.ru/publication/franchajzi-rostic-s-poluchil-20-v-strukture-vladeltsa-seti-83666.html'],
        },
        {
            'name': 'International Restaurant Brands (IRB)',
            'id': 'g68204914',
            'share': '20%',
            'as_of': '2026-05',
            'source': ['Sostav.ru', 'https://www.sostav.ru/publication/franchajzi-rostic-s-poluchil-20-v-strukture-vladeltsa-seti-83666.html'],
        },
        {
            'name': 'Татьяна Шаманская (гендиректор)',
            'id': None,
            'share': '3%',
            'as_of': '2026-05',
            'source': ['Sostav.ru', 'https://www.sostav.ru/publication/franchajzi-rostic-s-poluchil-20-v-strukture-vladeltsa-seti-83666.html'],
        },
    ],
}


def main(write=False):
    """Идемпотентен: каждый ключ применяется независимо, повторный запуск
    после частичной записи не падает на уже заполненных профилях."""
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    companies = data['companies']

    pending = {}
    for cid, entries in NEW_OWNERSHIP.items():
        assert cid in companies, 'нет такого профиля: %s' % cid
        current = companies[cid].get('ownership')
        if current:
            assert current == entries, 'ownership уже занят другим значением у %s: %r' % (cid, current)
            continue
        pending[cid] = entries

    if not pending:
        print('Все профили уже заполнены — нечего применять.')
        return

    print('Заполняю ownership: %s' % ', '.join('%s (%s)' % (cid, companies[cid]['name']) for cid in pending))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    for cid, entries in pending.items():
        companies[cid]['ownership'] = entries

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
