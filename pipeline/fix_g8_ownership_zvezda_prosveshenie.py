# -*- coding: utf-8 -*-
"""Качество, 19 сентября 2026 — все три уровня очереди дочитывания снова
измерены и снова пусты, продолжение пункта G8 из бэклога («Собственники
компании на её странице»).

Оба факта уже лежали в прозе карточек сделок; личный WebFetch подтвердил
каждый дословно по независимому источнику, отдельно от уже прочитанного
текста карточки.

1) `gd0b3d24e` («Звезда», производитель игрушек) — карточка `gbdd4f990`
   уже называла долю в прозе. WebFetch по Коммерсанту
   (https://www.kommersant.ru/doc/7264876) подтвердил дословно: «Юрлицо
   крупнейшего в России издательства настольных игр АО «Мир хобби»
   (бренд — Hobby World) с 24 октября стало владельцем 66% в ООО «Мир
   увлечений» и 56,25% — в ООО «Звезда»» (по данным «СПАРК-Интерфакс»).
   Дата у источника — 24 октября (карточка называла 23-е — расхождение
   на день, для `as_of` в формате «год-месяц» несущественно).

2) `g690e043b` («Просвещение», издательский холдинг) — карточка
   `gf9932079» уже называла итоговую долю в прозе. WebFetch по
   Коммерсанту (https://www.kommersant.ru/doc/8009248) подтвердил
   дословно: «У ВЭБа — 75%, у РФПИ — 25%» — ВЭБ.РФ консолидировал
   контрольный пакет после покупки ещё 25% у «Инвест ПРО».

Запуск:
    python3 pipeline/fix_g8_ownership_zvezda_prosveshenie.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_zvezda_prosveshenie.py --write    # запись
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit('/pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

KOMMERSANT_ZVEZDA = ['Коммерсантъ', 'https://www.kommersant.ru/doc/7264876']
KOMMERSANT_PROSVESHENIE = ['Коммерсантъ', 'https://www.kommersant.ru/doc/8009248']

OWNERSHIP = {
    'gd0b3d24e': [
        dict(name='Hobby World', id='gf969a0c9', share='56,25%',
             as_of='2024-10', source=KOMMERSANT_ZVEZDA),
    ],
    'g690e043b': [
        dict(name='ВЭБ.РФ', id='ga3f64b72', share='75%',
             as_of='2025-05', source=KOMMERSANT_PROSVESHENIE),
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
