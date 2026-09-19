# -*- coding: utf-8 -*-
"""Качество, 19 сентября 2026 — все три уровня очереди дочитывания снова
измерены и снова пусты, продолжение пункта G8 из бэклога («Собственники
компании на её странице»). Как и в прошлых прогонах, отобраны только
кандидаты, где текст описывает структуру ПОКУПАТЕЛЯ уже ПОСЛЕ сделки
(не бенефициара продавца до неё).

1) `gfda9fe6c` («Карачинская звезда», бывший завод «Чистозерье») —
   карточка `g1ce3ddfc» уже называла новую структуру в прозе. WebFetch по
   Коммерсанту подтвердил дословно: «В «ТД Усть-Каменский», согласно
   Kartoteka.ru, 99% принадлежат Евгению Громчакову, 1% — Андрею
   Голодову.»

2) `g456d8881` (ООО «Дока Рус» и ООО «Дока Липецк») — карточка
   `g981fc9c5» уже называла структуру покупателя. WebFetch по второй
   ссылке Коммерсанта (первая не содержала деталей — годится, что
   карточка сама даёт две ссылки на разные заметки одного издания)
   подтвердил дословно: «94,5% долей которого принадлежит Кириллу
   Игнахину, 2,5% — ООО «Портофино Кэпитал» (через цепочку юрлиц
   контролируется Дмитрием Водянниковым) и 3% — гендиректору обеих
   компаний Александру Огневу.»

3) `g021f076c` (ООО «Леони Рус») — карточка `g1e73548b» уже называла
   владельцев покупателя. WebFetch по Коммерсанту подтвердил дословно:
   «завод приобрело ООО «Импульс» предпринимателей Ильи и Дениса
   Черневых».

Запуск:
    python3 pipeline/fix_g8_ownership_karachinskaya_doka_leoni.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_karachinskaya_doka_leoni.py --write    # запись
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit('/pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

KOMMERSANT_KARACHINSKAYA = ['Коммерсантъ', 'https://www.kommersant.ru/doc/6822105']
KOMMERSANT_DOKA = ['Коммерсантъ', 'https://www.kommersant.ru/doc/6905521']
KOMMERSANT_LEONI = ['Коммерсантъ', 'https://www.kommersant.ru/doc/6818888']

OWNERSHIP = {
    'gfda9fe6c': [
        dict(name='ООО «Торговый дом Усть-Каменский» (99% — Евгений '
                   'Громчаков, 1% — Андрей Голодов)',
             id=None, share='100%', as_of='2024-06', source=KOMMERSANT_KARACHINSKAYA),
    ],
    'g456d8881': [
        dict(name='Кирилл Игнахин (через ООО «ЛПФ Капитал»)', id=None,
             share='94,5%', as_of='2024-06', source=KOMMERSANT_DOKA),
        dict(name='Александр Огнев (через ООО «ЛПФ Капитал»)', id=None,
             share='3%', as_of='2024-06', source=KOMMERSANT_DOKA),
        dict(name='ООО «Портофино Кэпитал» (через ООО «ЛПФ Капитал»; '
                   'контролируется Дмитрием Водянниковым)',
             id=None, share='2,5%', as_of='2024-06', source=KOMMERSANT_DOKA),
    ],
    'g021f076c': [
        dict(name='ООО «Импульс» (Илья и Денис Черневы)', id='g61f26c16',
             share='100%', as_of='2024-02', source=KOMMERSANT_LEONI),
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
