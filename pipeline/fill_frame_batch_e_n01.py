# -*- coding: utf-8 -*-
"""Три карточки притока 2022 года («from_compact»: «channel») пришли без
единой структурной связи стороны сделки: заголовок называет и покупателя, и
предмет прямым текстом, но `buyer`/`seller`/`target`/`asset` не заполнены,
хотя нужные профили компаний в базе уже есть.

- `cb33a285d` (Baker Hughes продаёт буровой сегмент российского бизнеса
  местному менеджменту): продавец — профиль `g631ec584` (Baker Hughes),
  покупатель — не компания, а «местный менеджмент» текстом (`buyer_name`,
  тот же приём, что и у `g4dd7a75c` — Schneider Electric/местный
  менеджмент), предмет — буровой сегмент бизнеса.
- `cdfe91cd0` («Росатом» увеличивает долю в ГК «Дело» до 49%, реализовав
  опцион): покупатель — профиль `rosatom`, предмет — профиль `delo` (ГК
  «Дело»); отдельного продавца не заполняю — источник описывает досрочную
  реализацию опциона, а не покупку доли у названного третьего лица.
- `caedef395` («ЭР-Телеком» покупает 51% разработчика систем виртуализации
  «Шаркс датацентр»): покупатель — профиль `gdc8edba1` (ЭР-Телеком
  Холдинг), предмет — профиль `g72026d3e` (Шаркс Датацентр).

Почему не через review.py: `buyer`/`target`/`seller` — ссылки на профили
(внутренние id), а не текст из статьи, дословную проверку по цитате для них
провести нельзя (id не встречается в тексте источника буквально) — тот же
барьер, что уже был у Henkel/Nokian.

Запуск: python3 pipeline/fill_frame_batch_e_n01.py
        python3 pipeline/fill_frame_batch_e_n01.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

FRAME = {
    'cb33a285d': dict(seller='g631ec584', buyer_name='Местный менеджмент',
                       asset='буровой сегмент российского бизнеса Baker Hughes'),
    'cdfe91cd0': dict(buyer='rosatom', target='delo'),
    'caedef395': dict(buyer='gdc8edba1', target='g72026d3e',
                       asset='51% долей ООО «Шаркс датацентр»'),
}


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    todo = {}
    for cid, fields in FRAME.items():
        card = cards[cid]
        if all(card.get(k) == v for k, v in fields.items()):
            print('УЖЕ ПРИМЕНЕНО %s' % cid)
            continue
        for k in fields:
            assert k not in card, '%s: поле %r уже задано' % (cid, k)
        todo[cid] = fields
        print('ПРАВИМ  %s: %s' % (cid, fields))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    for cid, fields in todo.items():
        cards[cid].update(fields)
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
