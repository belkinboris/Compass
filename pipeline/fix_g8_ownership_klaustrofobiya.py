# -*- coding: utf-8 -*-
"""Качество, 19 сентября 2026 — все три уровня очереди дочитывания снова
измерены и снова пусты, продолжение пункта G8 из бэклога («Собственники
компании на её странице»). Кандидат — закрытая сделка (фильтр по статусу
действует с прошлого прогона), факт описывает структуру ПОСЛЕ сделки.

`g8fd0df01» (сеть квестов «Клаустрофобия») — карточка `ga0a49202` (GrimTeam
приобрёл сеть, закрыто 1 июля 2025) уже называла структуру в прозе. Личный
WebFetch по Sostav.ru подтвердил дословно: «51% в обоих юрлицах владеет
инвестор в бизнес квестов Вадим Змовик, 33% — инвестор GrimTeam Павел
Вараксин, 16% — сооснователь GrimTeam Евгений Авин» (структура создана в
двух новых юрлицах — «Клаустрофобия Онлайн» и «Клаустрофобия Офлайн» —
после сделки).

Запуск:
    python3 pipeline/fix_g8_ownership_klaustrofobiya.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_klaustrofobiya.py --write    # запись
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit('/pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SOSTAV_SRC = ['Sostav.ru', 'https://www.sostav.ru/publication/cet-kvestov-klaustrofobiya-smenila-vladeltsev-77407.html']

OWNERSHIP = {
    'g8fd0df01': [
        dict(name='Вадим Змовик', id=None, share='51%',
             as_of='2025-07', source=SOSTAV_SRC),
        dict(name='Павел Вараксин', id=None, share='33%',
             as_of='2025-07', source=SOSTAV_SRC),
        dict(name='Евгений Авин (Антонов)', id=None, share='16%',
             as_of='2025-07', source=SOSTAV_SRC),
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
