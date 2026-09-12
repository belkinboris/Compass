# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — двадцатая партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, шестнадцатый-семнадцатый час подряд).

Тот же расширенный триггер, что и в партиях 9-19. С учётом уже занятых
96 профилей (пассы 1-19) замер дал 198 уникальных компаний-кандидатов.
Отобраны шесть с однозначным направлением (проверено по
`target`/`buyer`/`seller_id` каждой сделки) и без оговорок.

- `gdc33d226` (Платим, target инвестраунда `gbfb079af`): по данным
  «Контур-Фокуса», на момент сделки (декабрь 2022) 56% ООО «Платим»
  принадлежало основателю Леониду Румянцеву, 23% — Алексею Мишуровскому,
  16% — Александру Прокофьеву, 5% — Наилю Абдуллину.
- `ge8c9b2bc` (3S Group, target сделки `gdd85a5b9`): с 4 июня 2024 года
  99% девелопера принадлежит Артёму Чайке (профиль `gbef46925`, buyer
  этой же сделки), 1% — Александру Китаеву.
- `gdf730902` (ООО «Глобал МК», target сделки `g054eba01`): компания на
  58,12% принадлежит Игорю Краснолуцкому и на 41,88% — структуре
  Газпромбанка, ЗПИФ «Яшма».
- `g90a7c12d` (ООО «Интеллектуальные стройрешения», target сделки
  `ge9489d60` — покупка ГК «Полипластик» 25% сервиса QMonitoring): по
  данным ЕГРЮЛ, Даниилу Кручинину и гендиректору Аркадию Фроймчуку
  принадлежит по 44,10% (в карточке округлено до 44,05%), ещё 11,9% —
  у ООО «Матрикс».
- `gfe3416fc` (КонтролХак, target сделки `gabc53206` — доля Росатома):
  опцион реализован 3 июля 2023 года, новым учредителем стало ООО
  «ИнноХаб», 100% которого принадлежит АО «Атомэнергопром» (структура
  Росатома).
- `gd28693f6` (ООО «Техсервис», target сделки `g4cb8fc20` — интерес
  Росатома к золотодобывающему проекту): на момент сделки (2022) 35%
  принадлежало структуре «Ростеха» «РТ-Развитие бизнеса», 55,25% —
  кипрской Arsanol Holdings Ltd, 9,75% — юристу Илье Рыбалкину. (В поле
  `extra` той же карточки для Arsanol ошибочно стоит «19%» — это доля
  Антона Елистратова ВНУТРИ Arsanol, а не доля Arsanol в «Техсервисе»;
  верная сумма — по `eco.share`, она сходится ровно в 100%.)

Отклонённый кандидат того же прохода: `gb92763b6` (ООО «Энки», buyer
сделки `g3e3f5e9c`) — предложение источника («которым владеет ООО
«Элемент» бенефициара Виктора Мосина, руководителя структур «Кроста»
Алексея Добашина») не разделяет однозначно, к кому относится «руководитель
структур «Кроста»» — к Мосину или это отдельное упоминание Добашина;
неоднозначный референт, не вносится.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass20.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass20.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'gdc33d226': [
        {
            'name': 'Леонид Румянцев',
            'id': None,
            'share': '56%',
            'as_of': '2022-12',
            'source': ['vc.ru (данные «Контур-Фокуса»)', 'https://vc.ru/money/567570-servis-priema-platezhey-platim-privlek-23-4-mln-rubley-ot-top-menedzhera-banka-blank-i-osnovatelya-kudago'],
        },
        {
            'name': 'Алексей Мишуровский',
            'id': None,
            'share': '23%',
            'as_of': '2022-12',
            'source': ['vc.ru (данные «Контур-Фокуса»)', 'https://vc.ru/money/567570-servis-priema-platezhey-platim-privlek-23-4-mln-rubley-ot-top-menedzhera-banka-blank-i-osnovatelya-kudago'],
        },
        {
            'name': 'Александр Прокофьев',
            'id': None,
            'share': '16%',
            'as_of': '2022-12',
            'source': ['vc.ru (данные «Контур-Фокуса»)', 'https://vc.ru/money/567570-servis-priema-platezhey-platim-privlek-23-4-mln-rubley-ot-top-menedzhera-banka-blank-i-osnovatelya-kudago'],
        },
        {
            'name': 'Наиль Абдуллин',
            'id': None,
            'share': '5%',
            'as_of': '2022-12',
            'source': ['vc.ru (данные «Контур-Фокуса»)', 'https://vc.ru/money/567570-servis-priema-platezhey-platim-privlek-23-4-mln-rubley-ot-top-menedzhera-banka-blank-i-osnovatelya-kudago'],
        },
    ],
    'ge8c9b2bc': [
        {
            'name': 'Артём Чайка',
            'id': 'gbef46925',
            'share': '99%',
            'as_of': '2024-06-04',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6712251'],
        },
        {
            'name': 'Александр Китаев',
            'id': None,
            'share': '1%',
            'as_of': '2024-06-04',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6712251'],
        },
    ],
    'gdf730902': [
        {
            'name': 'Игорь Краснолуцкий',
            'id': None,
            'share': '58,12%',
            'as_of': '2022-12',
            'source': ['Vademecum', 'https://vademec.ru/news/2023/02/13/dochka-gazprombanka-stala-sovladeltsem-peterburgskoy-seti-lahta-clinic/'],
        },
        {
            'name': 'ЗПИФ «Яшма» (структура Газпромбанка)',
            'id': None,
            'share': '41,88%',
            'as_of': '2022-12',
            'source': ['Vademecum', 'https://vademec.ru/news/2023/02/13/dochka-gazprombanka-stala-sovladeltsem-peterburgskoy-seti-lahta-clinic/'],
        },
    ],
    'g90a7c12d': [
        {
            'name': 'Даниил Кручинин',
            'id': None,
            'share': '44,05%',
            'as_of': '2026',
            'source': ['audit-it.ru (данные ЕГРЮЛ)', 'https://www.audit-it.ru/contragent/1247700113330_ooo-intellektualnye-stroyresheniya'],
        },
        {
            'name': 'Аркадий Фроймчук',
            'id': None,
            'share': '44,05%',
            'as_of': '2026',
            'source': ['audit-it.ru (данные ЕГРЮЛ)', 'https://www.audit-it.ru/contragent/1247700113330_ooo-intellektualnye-stroyresheniya'],
        },
        {
            'name': 'ООО «Матрикс»',
            'id': None,
            'share': '11,9%',
            'as_of': '2026',
            'source': ['audit-it.ru (данные ЕГРЮЛ)', 'https://www.audit-it.ru/contragent/1247700113330_ooo-intellektualnye-stroyresheniya'],
        },
    ],
    'gfe3416fc': [{
        'name': 'ООО «ИнноХаб» (100% — АО «Атомэнергопром», структура Росатома)',
        'id': None,
        'as_of': '2023-07-03',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5771545'],
    }],
    'gd28693f6': [
        {
            'name': '«РТ-Развитие бизнеса» (структура Ростеха)',
            'id': None,
            'share': '35%',
            'as_of': '2022',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5707294'],
        },
        {
            'name': 'Arsanol Holdings Ltd (Кипр)',
            'id': None,
            'share': '55,25%',
            'as_of': '2022',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5707294'],
        },
        {
            'name': 'Илья Рыбалкин',
            'id': None,
            'share': '9,75%',
            'as_of': '2022',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5707294'],
        },
    ],
}


def main(write=False):
    """Идемпотентен, как pass1-19."""
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
