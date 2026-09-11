# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — третья партия майнинга уже собранного текста
карточек. Три уровня очереди дочитывания пусты четвёртый час подряд.

Метод уточнён по итогам замера прошлого часа: искать не просто слово
«бенефициар»/«подконтрольный» ГДЕ-ТО в карточке, а в ТОМ ЖЕ
ПРЕДЛОЖЕНИИ, что и имя профиля стороны сделки, — иначе выборка (232
кандидата по мягкому совпадению поля) переполнена случаями, где слово
относится к другой стороне того же текста. Уточнённый шаблон дал 62
кандидата; отобраны четыре с однозначным, не оспариваемым фактом и
точным источником (остальные либо содержат оговорку «не установлен» /
«не раскрываются», либо ссылаются на неподтверждённую версию СМИ — не
вносятся):

- `g04a9090b` (Arrival, target сделки `g270c77f8`, раунд Hyundai/Kia):
  «До сделки единственным акционером Arrival был фонд Kinetik
  (бенефициар — Денис Свердлов)» — РБК/Forbes/Ведомости, до раунда
  16 января 2020 года.
- `gc9913f2a` (Таймыр Инжиниринг, buyer сделки `g18569a1c`): «бенефициар
  с марта 2025 года — Марат Тякин» (Интерфакс).
- `g493c37b3` (АО «Атерра», buyer сделки `gdfe2f116`): «его бенефициар
  Наталия Хряпова владеет долей 43,75%» (Коммерсантъ).
- `g3a52762e` (ООО «Юнитайл Холдинг», target сделки `gb207417a`):
  «3 июня 2026 года личная доля Файна (94,99% в «Юнитайл Холдинге»)
  перешла подконтрольному ему же АО «СДМ ИНВЕСТ»» — текущая структура
  ПОСЛЕ передачи, Коммерсантъ/audit-it.ru/companies.rbc.ru.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass3.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass3.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g04a9090b': [{
        'name': 'Фонд Kinetik (бенефициар — Денис Свердлов)',
        'id': None,
        'as_of': '2020-01',
        'source': ['РБК', 'https://www.rbc.ru/business/16/01/2020/5e1f84379a794703747061b1'],
    }],
    'gc9913f2a': [{
        'name': 'Марат Тякин',
        'id': None,
        'as_of': '2025-03',
        'source': ['Интерфакс', 'https://www.interfax.ru/business/1063509'],
    }],
    'g493c37b3': [{
        'name': 'Наталия Хряпова',
        'id': None,
        'share': '43,75%',
        'as_of': '2023-08',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6137536'],
    }],
    'g3a52762e': [{
        'name': 'АО «СДМ ИНВЕСТ» (структура Александра Файна)',
        'id': None,
        'share': '94,99%',
        'as_of': '2026-06',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/7432619'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1/pass2."""
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
