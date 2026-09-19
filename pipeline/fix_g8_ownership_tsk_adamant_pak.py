# -*- coding: utf-8 -*-
"""Качество, 19 сентября 2026 — все три уровня очереди дочитывания снова
измерены и снова пусты, продолжение пункта G8 из бэклога («Собственники
компании на её странице»). Три закрытые сделки, факт — о покупателе после
сделки, проверка независимым чтением источника (саб-агент).

1) `gc0638d38` (ООО «ЦК», покупатель лизингового и факторингового бизнеса
   Volkswagen Financial Services, сделка закрыта 25 января 2024) — карточка
   `geb645292` уже называла структуру в прозе. Читатель подтвердил дословно
   по Интерфаксу (2 февраля 2024): «новосибирское АО «ЦК», бенефициаром
   которого через ООО «ДНК» является Ким». Источник называет юрлицо «АО
   «ЦК»», карточка и профиль — «ООО «ЦК»» (расхождение организационно-
   правовой формы, не имени); утверждение «владелец Экспобанка» ни один
   источник не подтвердил — записан только подтверждённый факт (Ким через
   ООО «ДНК»), без непроверенной детали.

2) `g18b68845` (Холдинг «Адамант», покупатель двух стекольных заводов AGC)
   — карточка `gcf0f7334» уже называла бенефициара в прозе. Читатель
   подтвердил дословно по «Деловому Петербургу» (22 февраля 2024):
   «Основной бенефициар — Игорь Лейтис (№ 18 в Рейтинге миллиардеров
   "ДП"-2023)».

3) `g527da4e8` (ПромАвтоКонсалт, покупатель российского бизнеса Schaeffler)
   — карточка `g5fb64cd9` уже называла бенефициара в прозе. Читатель
   подтвердил дословно по Коммерсанту (18 декабря 2023): «По данным ЕГРЮЛ,
   "Промавтоконсалт" принадлежит Александру Горлову».

Запуск:
    python3 pipeline/fix_g8_ownership_tsk_adamant_pak.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_tsk_adamant_pak.py --write    # запись
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit('/pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

INTERFAX_TSK = ['Интерфакс', 'https://www.interfax.ru/business/944303']
DP_ADAMANT = ['Деловой Петербург', 'https://www.dp.ru/a/2024/02/22/peterburgskij-adamant-kupil']
KOMMERSANT_PAK = ['Коммерсантъ', 'https://www.kommersant.ru/doc/6410800']

OWNERSHIP = {
    'gc0638d38': [
        dict(name='Игорь Ким (через ООО «ДНК»)', id=None, share=None,
             as_of='2024-02', source=INTERFAX_TSK),
    ],
    'g18b68845': [
        dict(name='Игорь Лейтис', id=None, share=None,
             as_of='2024-02', source=DP_ADAMANT),
    ],
    'g527da4e8': [
        dict(name='Александр Горлов', id=None, share=None,
             as_of='2023-12', source=KOMMERSANT_PAK),
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
