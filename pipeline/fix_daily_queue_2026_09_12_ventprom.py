# -*- coding: utf-8 -*-
"""Приток, 12 сентября 2026: новая карточка — акции АО «Артемовский
машиностроительный завод «Вентпром»» (производитель промышленных
вентиляторов, Свердловская область) обращены в доход государства по
решению Ленинского районного суда Екатеринбурга (17 августа 2026). Истец —
заместитель прокурора Свердловской области, дело — «о запрете деятельности
общественных объединений» (более 20 исполнительных листов, среди
ответчиков — бывший владелец Олег Горшков). Источник — mergers.ru
(прочитан лично, WebFetch); ИНН профиля (6602010624) подтверждён
rusprofile.ru/id/394753 и spark-interfax.ru (ОГРН 1069602006583). Тип и
статус — по образцу уже заведённых карточек национализации (c1062263e,
c151696b4, gd95bf2d7): «M&A», «Закрыта» — передача акций уже состоялась
решением суда, а не обсуждается. Пишется в pending.json — карточку должна
пройти accept_card.py перед консолью.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEALS_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
REGISTRY_PATH = os.path.join(ROOT, 'pipeline', 'fns_registry.py')

TARGET_ID = 'g3bceee3d'
CARD_ID = 'gb98fcce5'

TARGET_PROFILE = {
    "name": "Артемовский машиностроительный завод «Вентпром»",
    "ind": "Машиностроение",
    "desc": "Производитель промышленных вентиляторов и холодильного оборудования в Артёмовском районе Свердловской области.",
    "kpi": ["Профиль", "Автоматический"],
}

CARD = {
    "id": CARD_ID,
    "date": "2026-08-17",
    "title": "Акции завода «Вентпром» обращены в доход государства по решению суда",
    "ind": "Машиностроение",
    "type": "M&A",
    "status": "Закрыта",
    "src": [
        ["mergers.ru", "https://mergers.ru/news/Akcii-zavoda-Ventprom-izyaty-v-dohod-gosudarstva-po-resheniyu-suda-87471"],
    ],
    "from_ingest": True,
    "eco": {
        "sum": "—",
        "share": "Акции АО «Артемовский машиностроительный завод «Вентпром»» перешли в доход государства (100% предприятия).",
        "val": "—",
        "target_fin": "По РСБУ за 2025 год чистая прибыль «Вентпрома» составила 139,13 млн ₽ — в 5,7 раза больше, чем годом ранее; выручка выросла на 5,7%, до 3,03 млрд ₽.",
        "fin": "—",
        "rationale": "—",
        "context": "Прежний совладелец — Олег Горшков, которому на март 2018 года принадлежало 27,9% акций.",
        "finadv": "—",
    },
    "law": {
        "struct": "—",
        "appr": "Акции перешли в доход государства решением Ленинского районного суда Екатеринбурга от 17 августа 2026 года по делу «о запрете деятельности общественных объединений» — истцом выступал заместитель прокурора Свердловской области, по делу вынесено более 20 исполнительных листов, среди ответчиков — Олег Горшков и другие лица.",
        "adv": [],
        "terms": "—",
    },
    "target": TARGET_ID,
    "asset": "Артемовский машиностроительный завод «Вентпром»",
}


def main(write):
    with open(DEALS_PATH, encoding='utf-8') as f:
        deals_data = json.load(f)
    assert TARGET_ID not in deals_data['companies'], 'профиль уже существует'
    assert not any(d['id'] == CARD_ID for d in deals_data['deals']), 'карточка уже есть в базе'

    with open(PENDING_PATH, encoding='utf-8') as f:
        pending_data = json.load(f)
    assert not any(c['id'] == CARD_ID for c in pending_data['cards']), 'карточка уже в очереди'

    deals_data['companies'][TARGET_ID] = TARGET_PROFILE
    pending_data['cards'].append(CARD)

    print('Добавлен профиль:', TARGET_ID, '(Вентпром)')
    print('Добавлена карточка в очередь:', CARD_ID)

    if write:
        with open(DEALS_PATH, 'w', encoding='utf-8') as f:
            json.dump(deals_data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending_data, f, ensure_ascii=False, indent=1)
            f.write('\n')

        registry_block = '''
# Приток — 12 сентября 2026: ИНН АО «Вентпром» (карточка gb98fcce5,
# национализация акций по решению суда). Подтверждено двумя независимыми
# регистровыми источниками (rusprofile.ru/id/394753, spark-interfax.ru),
# ОГРН 1069602006583.
REGISTRY += [
    {"company_id": 'g3bceee3d', "decision": "confirmed", "inn": '6602010624',
     "reason": "Приток (12.09.2026): ИНН АО «Артемовский машиностроительный завод «Вентпром»» подтверждён rusprofile.ru и spark-interfax.ru, ОГРН 1069602006583.",
     "date": '2026-09-12'},
]
'''
        with open(REGISTRY_PATH, encoding='utf-8') as f:
            registry_src = f.read()
        marker = 'def by_company_id() -> dict[str, dict]:'
        assert marker in registry_src
        assert 'g3bceee3d' not in registry_src
        registry_src = registry_src.replace(marker, registry_block.strip('\n') + '\n\n' + marker, 1)
        with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
            f.write(registry_src)

        print('Записано.')
    else:
        print('Сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    import sys
    main('--write' in sys.argv)
