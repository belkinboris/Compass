# -*- coding: utf-8 -*-
"""Качество, 19 сентября 2026 — все три уровня очереди дочитывания снова
измерены и снова пусты, продолжение пункта G8 из бэклога («Собственники
компании на её странице»).

Новый фильтр, добавленный в этот прогон: кандидаты берутся ТОЛЬКО из
сделок со статусом «Закрыта» — два кандидата в прошлый заход
(«Лабинский» ВТБ и «АГ Майнинг») оказались со статусом «Обсуждается»,
и записывать факт о покупателе как текущего владельца было бы
преждевременно (сделка ещё не закрыта, «Лабинский» к тому же — открытый
вопрос в «Известных проблемах» CLAUDE.md, решать его самовольно не стал).

1) `ge64430f4` (Пансионат Камелия, Swissotel Resort Сочи) — карточка
   `g3cd0f85e` (закрыта 8 августа 2025) уже называла долю в прозе.
   WebFetch по Интерфаксу подтвердил 75% Тараса Демуры; WebFetch по
   Frank Media подтвердил дословно: «Оставшиеся 25% в «Правильных
   решениях» принадлежат «ФС холдинг» бизнесмена Игоря Воскресенского.»

2) `gc3119b9e` (ОМЗ-ИТ) — карточка `ga80371a8` (закрыта 1 июля 2024)
   уже называла долю в прозе. WebFetch по Коммерсанту подтвердил
   дословно: «60% у «Софтлайн Проекты»»; «40% у ЗПИФ «Перспективные
   Технологии»».

Запуск:
    python3 pipeline/fix_g8_ownership_kamelia_omzit.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_kamelia_omzit.py --write    # запись
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit('/pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

FRANKMEDIA_KAMELIA = ['Frank Media', 'https://frankmedia.ru/213579']
INTERFAX_KAMELIA = ['Интерфакс', 'https://www.interfax.ru/business/1040232']
KOMMERSANT_OMZIT = ['Коммерсантъ', 'https://www.kommersant.ru/doc/6892984']

OWNERSHIP = {
    'ge64430f4': [
        dict(name='Тарас Демура (через ООО «Правильные решения»)',
             id=None, share='75%', as_of='2025-08', source=INTERFAX_KAMELIA),
        dict(name='«ФС холдинг» Игоря Воскресенского (через ООО '
                   '«Правильные решения»)',
             id=None, share='25%', as_of='2025-08', source=FRANKMEDIA_KAMELIA),
    ],
    'gc3119b9e': [
        dict(name='ООО «Софтлайн Проекты»', id='g6d96c661', share='60%',
             as_of='2024-07', source=KOMMERSANT_OMZIT),
        dict(name='ЗПИФ «Перспективные Технологии»', id=None, share='40%',
             as_of='2024-07', source=KOMMERSANT_OMZIT),
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
