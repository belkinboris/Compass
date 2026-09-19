# -*- coding: utf-8 -*-
"""Качество, 19 сентября 2026 — все три уровня очереди дочитывания снова
измерены и снова пусты, продолжение пункта G8 из бэклога («Собственники
компании на её странице»). Оба кандидата — закрытые сделки, факт про
структуру ПОСЛЕ сделки.

1) `gdb2fdb1a` (ООО «Апр-Сити/ТВД», прямой покупатель аэропорта Магас) —
   карточка `g97d0d2a2` уже называла владельца в прозе. WebFetch по
   Интерфаксу подтвердил дословно: «100% долей владеет ООО «РВБ»
   (объединенная компания Wildberries & Russ)». Разбивку 65%/35% между
   Wildberries и Russ Outdoors, которую карточка приводит в `extra`, ЭТА
   статья не подтверждает — записан только подтверждённый факт (100% у
   РВБ), без непроверенной детализации. Ownership поставлен на профиль
   САМОЙ «Апр-Сити/ТВД» (прямого юрлица-покупателя), а не на профиль
   аэропорта — на аэропорт уже есть корректный `buyer` (РВБ).

2) `gfd9eea5c` («Кенди Флип Роботс») — карточка `g65deaa28` уже называла
   долю фонда «Восход» в прозе. WebFetch по Mergers.ru дал ПОЛНУЮ
   структуру владения дословно: «Владельцами ООО «Кенди Флип Роботс»...
   выступают Владимир Марголин (36,1%) и Сергей Коренков (27,1%), а также
   ООО «Хайв» (23,9%) и «Восход» (12,9%)» — записаны все четыре
   совладельца, а не только инвестора этой сделки.

Запуск:
    python3 pipeline/fix_g8_ownership_magas_kendi.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_magas_kendi.py --write    # запись
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit('/pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

INTERFAX_MAGAS = ['Интерфакс', 'https://www.interfax.ru/business/1048260']
MERGERS_KENDI = ['Mergers.ru', 'https://mergers.ru/news/Venchurnyj-fond-Voshod-investiroval-v-razrabotchika-datatech-platformy-SenseMachine-85447']

OWNERSHIP = {
    'gdb2fdb1a': [
        dict(name='ООО «РВБ» (Wildberries & Russ)', id='g549ab474',
             share='100%', as_of='2025-09', source=INTERFAX_MAGAS),
    ],
    'gfd9eea5c': [
        dict(name='Владимир Марголин', id=None, share='36,1%',
             as_of='2025-05', source=MERGERS_KENDI),
        dict(name='Сергей Коренков', id=None, share='27,1%',
             as_of='2025-05', source=MERGERS_KENDI),
        dict(name='ООО «Хайв»', id=None, share='23,9%',
             as_of='2025-05', source=MERGERS_KENDI),
        dict(name='Венчурный фонд «Восход»', id='g427bcb12', share='12,9%',
             as_of='2025-05', source=MERGERS_KENDI),
    ],
}


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    companies = data['companies']

    for cid, ownership in OWNERSHIP.items():
        assert cid in companies, f"нет профиля {cid}"
        assert not companies[cid].get('ownership'), f"{cid} уже несёт ownership: {companies[cid].get('ownership')!r}"
        print(f"{cid} ({companies[cid]['name']}): += ownership")
        for o in ownership:
            print(f"    {o['name']} — {o.get('share', '(доля не названа)')} (на {o['as_of']})")
        companies[cid]['ownership'] = ownership

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
