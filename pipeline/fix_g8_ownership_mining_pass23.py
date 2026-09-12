# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — двадцать третья партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, двадцатый час подряд).

Тот же расширенный триггер, что и в партиях 9-22. С учётом уже занятых
126 профилей (пассы 1-22) замер дал 174 уникальные компании-кандидата.

- `g772792a6` (Ledvakh Trade, buyer сделки `g81163284` — покупка двух
  российских заводов 3M): казахстанской компанией владеет научно-
  производственный холдинг ВМП из Екатеринбурга.
- `g7814a42a` (My.Games, seller_id сделки `gc6322659` — продажа
  платформы Boosty): до сентября 2022 года принадлежала VK, затем
  холдинг продал её за $642 млн управляющему LETA Capital Александру
  Чачаве.
- `g519f8484` (Деметра-Холдинг, target сделки `g38ce6e22` — выход
  Marathon Group из капитала): Marathon Group Сергея Захарова и
  Александра Винокурова владела 10,57% холдинга через ООО «СПН» с
  2020 года до выхода в 2023-м.
- `g4912c119` (ОАО «Хлебпром», target сделки `g1f43265d` — выход ЕБРР
  из капитала): ЕБРР владел 29,43% головной структуры через МКООО
  «Рейкрофт Лимитед» с 2011 года.
- `g51747db2` (ООО «Гетмобит», target сделки `g4c62c047` — F+ tech
  купил 49%): после сделки (февраль 2023) 49% — у F+ tech, 41% — у
  Петра Ефимова (основателя «Информзащиты»), 10% — у Рукавишниковой.
- `g78add6eb` (ЛайфСтрим / Смотрешка, target сделки `g1125c0ec` — Wink
  купил 100%): до сделки (январь 2026) 89% принадлежало гендиректору
  Александру Киселевичу, 7,25% — Тимуру Родионову, 3,75% — Георгию Юфа.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass23.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass23.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g772792a6': [{
        'name': 'Холдинг ВМП (Екатеринбург)',
        'id': None,
        'as_of': '2023-06',
        'source': ['Vademecum', 'https://vademec.ru/news/2023/06/07/blizkaya-k-vmp-struktura-kupila-rossiyskiy-zavod-zm/'],
    }],
    'g7814a42a': [
        {
            'name': 'VK',
            'id': None,
            'as_of': 'до 2022-09',
            'source': ['Интерфакс', 'https://www.interfax.ru/business/917057'],
        },
        {
            'name': 'Александр Чачава (LETA Capital)',
            'id': None,
            'as_of': '2022-09',
            'source': ['Интерфакс', 'https://www.interfax.ru/business/917057'],
        },
    ],
    'g519f8484': [{
        'name': 'Marathon Group (Сергей Захаров, Александр Винокуров) через ООО «СПН»',
        'id': None,
        'share': '10,57%',
        'as_of': '2020-2023',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6149973'],
    }],
    'g4912c119': [{
        'name': 'ЕБРР через МКООО «Рейкрофт Лимитед»',
        'id': None,
        'share': '29,43%',
        'as_of': '2011-2023',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5772275'],
    }],
    'g51747db2': [
        {
            'name': 'F+ tech',
            'id': 'gdd8d0439',
            'share': '49%',
            'as_of': '2023-02',
            'source': ['CNews', 'https://www.cnews.ru/news/top/2023-02-07_marvel_vykupil_49_proizvoditelya'],
        },
        {
            'name': 'Пётр Ефимов (основатель «Информзащиты»)',
            'id': None,
            'share': '41%',
            'as_of': '2023-02',
            'source': ['CNews', 'https://www.cnews.ru/news/top/2023-02-07_marvel_vykupil_49_proizvoditelya'],
        },
        {
            'name': 'Рукавишникова',
            'id': None,
            'share': '10%',
            'as_of': '2023-02',
            'source': ['CNews', 'https://www.cnews.ru/news/top/2023-02-07_marvel_vykupil_49_proizvoditelya'],
        },
    ],
    'g78add6eb': [
        {
            'name': 'Александр Киселевич (гендиректор)',
            'id': None,
            'share': '89%',
            'as_of': 'до 2026-01',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/8362652'],
        },
        {
            'name': 'Тимур Родионов',
            'id': None,
            'share': '7,25%',
            'as_of': 'до 2026-01',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/8362652'],
        },
        {
            'name': 'Георгий Юфа',
            'id': None,
            'share': '3,75%',
            'as_of': 'до 2026-01',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/8362652'],
        },
    ],
}


def main(write=False):
    """Идемпотентен, как pass1-22."""
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
