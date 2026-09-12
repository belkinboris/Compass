# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — девятнадцатая партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, четырнадцатый час подряд).

Тот же расширенный триггер, что и в партиях 9-18. С учётом уже занятых
90 профилей (пассы 1-18) замер дал 204 уникальные компании-кандидата —
метод по-прежнему далёк от исчерпания. Отобраны шесть с однозначным
направлением (проверено по `target`/`buyer`/`seller_id` каждой сделки) и
без оговорок.

- `g0c7636b1` (Smartway, buyer сделки `g8e71c525` — покупка агентства
  делового туризма ATH): по данным «СПАРК-Интерфакса» 44,10% принадлежит
  гендиректору Максиму Яремко, 4,9% — Александру Коляскину.
- `g3738b7b1` (АО «Ямалдорстрой», target сделки `g7ae9bb53` — покупка
  ООО «Энерготехника Северо-Запад»): основал в 2007 году Марс
  Гайнутдинов, ему принадлежало 100% акций до продажи.
- `g130b6d10` (ГК Росспиртпром, buyer сделки `g3ece5143` — покупка 51%
  Тульского винокуренного завода 1911): до 2024 года принадлежал
  Росимуществу, в апреле 2024 года 100% акций продали на торгах.
- `gf15533aa` (ООО «Ланксесс Липецк», target сделки `gfe16916c` —
  продажа Владимиру Якушину): с 31 мая 2023 года 100% принадлежит
  «Нортексу».
- `g00f14033` (Ростелеком, buyer сделки `gf9ceefb9` — покупка 55% Tele2
  у ВТБ и консорциума инвесторов): по итогам сделки ВТБ с партнёрами
  стали владельцами 29,4% обыкновенных акций.
- `g49ed9c48` (ООО «МОЯ СМЕНА», target сделки `ga6924cc4` — инвестиция
  HeadHunter): сервис «Моя смена» принадлежит ГК Verme.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass19.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass19.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g0c7636b1': [
        {
            'name': 'Максим Яремко',
            'id': None,
            'share': '44,10%',
            'as_of': '2023',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/amp/6014872'],
        },
        {
            'name': 'Александр Коляскин',
            'id': None,
            'share': '4,9%',
            'as_of': '2023',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/amp/6014872'],
        },
    ],
    'g3738b7b1': [{
        'name': 'Марс Гайнутдинов',
        'id': None,
        'share': '100%',
        'as_of': '2007-2023',
        'source': ['Деловой Петербург', 'https://www.dp.ru/a/2026/03/12/beneficiar-peterburgskoj-zvezdi'],
    }],
    'g130b6d10': [{
        'name': 'Росимущество',
        'id': None,
        'as_of': 'до 2024',
        'source': ['Ведомости', 'https://www.vedomosti.ru/business/articles/2025/08/08/1130442-rosspirtprom-priobrel-vodki'],
    }],
    'gf15533aa': [{
        'name': '«Нортекс»',
        'id': None,
        'share': '100%',
        'as_of': '2023-05-31',
        'source': ['Nortex', 'https://nortex-chem.ru/news/Kompaniya-Nortex-priobrela-zavod-Lanxess/'],
    }],
    'g00f14033': [{
        'name': 'ВТБ с партнёрами',
        'id': None,
        'share': '29,4%',
        'as_of': '2020',
        'source': ['РБК', 'https://www.rbc.ru/rbcfreenews/5e43bc5c9a7947a2636b9f60'],
    }],
    'g49ed9c48': [{
        'name': 'ГК Verme',
        'id': None,
        'as_of': '2025',
        'source': ['Ведомости', 'https://www.vedomosti.ru/technologies/industries_and_markets/news/2025/10/09/1145756-headhunter-investiroval-v-moya-smena'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1-18."""
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
