# -*- coding: utf-8 -*-
"""Качество, 22 сентября 2026 (ежедневный прогон 21:37 МСК) — все три уровня
очереди дочитывания снова измерены и снова пусты, продолжение пункта G8 из
бэклога («Собственники компании на её странице»). Один кандидат, закрытая
сделка, факт про структуру ПОКУПАТЕЛЯ, проверен саб-агентом дословной
цитатой источника.

`g0be9547a` (ГеоПроМайнинг, покупатель золотодобывающих активов в
Забайкалье через дочернюю структуру ООО «Кряж Инвест») — карточка
`gmru-geopromining-zabaikalie` уже называла бенефициара в прозе. Саб-агент
подтвердил дословно по mergers.ru/Коммерсанту (20.07.2026): «Бенефициар
«ГеоПроМайнинга», следует из отчётности,— Александр Орехов, бывший деловой
партнёр основателя AEON Романа Троценко». Доля не названа — только сам
факт бенефициарного владения, без процента.

Второй кандидат этого захода (Акрон Холдинг / завод «Транскат») НЕ взят:
саб-агент установил, что «Акрон Холдинг» (наш профиль) и «АО «Акрон
Индустрия»» (юрлицо, названное в источнике как реальный покупатель, 99,99%
+ 0,01% у Павла Морозова лично) — РАЗНЫЕ юрлица с разными ИНН, связанные
общим директором. В нашем профиле ИНН не хранится, проверить, к какому
юрлицу он на самом деле привязан, нечем — писать факт на возможно не то
юрлицо рискованнее, чем оставить поле пустым.

Запуск:
    python3 pipeline/fix_g8_ownership_geopromining.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_geopromining.py --write    # запись
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit('/pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

MERGERS_GPM = ['mergers.ru', 'https://mergers.ru/news/GeoProMajning-kupil-aktivy-po-dobyche-zolota-v-Zabajkale-87237']

OWNERSHIP = {
    'g0be9547a': [
        dict(name='Александр Орехов', id=None, share=None,
             as_of='2026-07', source=MERGERS_GPM),
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
            print(f"    {o['name']} — {o.get('share') or '(доля не названа)'} (на {o['as_of']})")
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
