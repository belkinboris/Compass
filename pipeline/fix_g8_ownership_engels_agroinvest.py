# -*- coding: utf-8 -*-
"""Качество, 19 сентября 2026 — все три уровня очереди дочитывания снова
измерены и снова пусты, продолжение пункта G8 из бэклога («Собственники
компании на её странице»).

Внимание при отборе кандидатов в этот раз: часть текстовых совпадений
«принадлежит/бенефициар» в очереди описывает ПРЕЖНЕГО владельца (продавца
до сделки), а не текущего — например, «Юнифрост приобрел 100% Меридиана»
рядом с фразой «основным бенефициаром бизнеса выступает Владимир Малахов»
(это бенефициар ПРОДАВЦА, до сделки; сегодня владелец — Юнифрост, он же
buyer карточки). Такие кандидаты сознательно пропущены — записывать их в
`ownership` значило бы вносить устаревший факт. Взяты только два, где
текст описывает СТРУКТУРУ ПОКУПАТЕЛЯ уже ПОСЛЕ сделки.

1) `ge788d903` («Энгельс Электроинструменты») — карточка `gd4645195`
   называет покупателя (ООО «Интернет проекты», связана с Softline) и
   его внутреннюю структуру. Личный WebFetch по Mergers.ru подтвердил
   дословно: «Сейчас ей принадлежит доля 99%, еще 1% — ООО «Аталайя»»
   (речь о Елене Волотовской, вице-президенте Softline по инвестициям).
   `buyer` карточки не заведён на профиль компании (`None`) — сама
   «Интернет проекты» тоже без профиля, поэтому вся структура — одной
   описательной строкой, как уже принято для «Белой скалы».

2) `gd873b039` (ООО «Агроинвест», владеет маслозаводом «Масленица») —
   карточка `gd7fd670e» уже называла обе доли в прозе. WebFetch по
   Интерфаксу подтвердил дословно: «Компания "ЭФКО" стала владельцем
   31,4% ООО "Агроинвест"»; «Остальные 68,6% принадлежат катарской "КГА
   Холдинг ЛЛС", владельцы которой не раскрыты» — записаны ОБА совладельца
   (ЭФКО — по своему профилю, «КГА Холдинг ЛЛС» — текстом, её бенефициары
   сам источник называет нераскрытыми).

Запуск:
    python3 pipeline/fix_g8_ownership_engels_agroinvest.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_engels_agroinvest.py --write    # запись
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit('/pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

MERGERS_ENGELS = ['Mergers.ru', 'https://mergers.ru/news/Severgrupp-Mordashova-prodala-OOO-Jengels-Jelektroinstrumenty-byvshij-zavod-Bosch-85439']
INTERFAX_AGROINVEST = ['Интерфакс', 'https://www.interfax.ru/business/1020897']

OWNERSHIP = {
    'ge788d903': [
        dict(name='ООО «Интернет проекты» (структура Softline; 99% — '
                   'Елена Волотовская, вице-президент Softline по '
                   'инвестициям, 1% — ООО «Аталайя»)',
             id=None, as_of='2025-04', source=MERGERS_ENGELS),
    ],
    'gd873b039': [
        dict(name='ЭФКО', id='g5db3de73', share='31,4%',
             as_of='2025-04', source=INTERFAX_AGROINVEST),
        dict(name='КГА Холдинг ЛЛС (Катар)', id=None, share='68,6%',
             as_of='2025-04', source=INTERFAX_AGROINVEST),
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
