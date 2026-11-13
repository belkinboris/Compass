# -*- coding: utf-8 -*-
"""Карточка g9a4c7065, «Медисорб» купил химическую группу «Пермхим»: структурные
поля по прочтению источников и ЕГРЮЛ — по просьбе партнера (тема «Клод»,
сообщение 3435, 13 ноября 2026). Черновик лежал в очереди с 11 ноября непрочитанным.

ЧТО СТАВИТСЯ И ПОЧЕМУ:
  * дата — 2026-10-14: последняя из записей ЕГРЮЛ о переходе долей (06.10.2026 —
    ООО «НПП Синтез» и ООО «Промхимэкспорт», 14.10.2026 — ООО «Пермхим»);
    в черновике стоял день публикации «Ведомостей» (11.11.2026). Через review.py
    дата не идет: в реестре она цифрами, а `date_is_supported` ждет месяц прописью.
  * продавцы — Елена Лапшина (100% ООО «Пермхим») и Владимир Пономарев (100% ООО
    «НПП Синтез» и ООО «Промхимэкспорт») — по истории участников ЕГРЮЛ
    (datanewton.ru); пресса пишет только «у физических лиц» (Абирег).
  * покупатель — «Медисорб»: так во всех источниках; по ЕГРЮЛ доли записаны на
    АО «Эпимер» (ИНН 9717075461) — компанию по адресу «Медисорба» под той же
    управляющей ООО «МС Групп» (Абирег: «связанное с «Медисорбом» АО «Эпимер»).
    В схеме — группа, держатель долей назван в law.struct
    (docs/card_parties.md, «те, кто в реестре»: в реестр вошла структура покупателя).
  * сумма не раскрыта; «500 млн ₽» из черновика-дубля geac29290 — обещанные
    вложения в купленные предприятия, не цена.

Запуск:
    python3 pipeline/build_medisorb_permkhim_2026_11_13.py            # сухой прогон
    python3 pipeline/build_medisorb_permkhim_2026_11_13.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CARD_ID = 'g9a4c7065'
VED = 'https://www.vedomosti.ru/business/articles/2026/11/11/1244329-medisorb-kupil-himicheskuyu'
DN = 'https://datanewton.ru/contragents/'
SELLER = 'Елена Лапшина и Владимир Пономарев'
SRC = [
    ['Ведомости', VED],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/9094406'],
    ['Абирег', 'https://abireg.ru/newsitem/119168-medisorb-priobrel-gruppu-permkhim-i-vlozhit-bolee-500-mln-rubley-v-ee-razvitie/'],
    ['Фармпром', 'https://pharmprom.news/medisorb-rasshiryaet-promyshlennuyu-bazu-dlya-razvitiya-proizvodstva-farmacevticheskix-substancij/'],
    ['ЕГРЮЛ: ООО «Пермхим»', DN + '1025901607533'],
    ['ЕГРЮЛ: ООО «НПП Синтез»', DN + '1025901611746'],
    ['ЕГРЮЛ: ООО «Промхимэкспорт»', DN + '1145958061700'],
]


def patch(card):
    assert card['date'] == '2026-11-11', card['date']
    assert card.get('buyer_name') == '«Медисорб»' and not card.get('seller'), (card.get('buyer_name'), card.get('seller'))
    assert card['src'] == [['Ведомости', VED]], card['src']
    assert card['eco']['sum'] == '—' and not card.get('sum')
    card['date'] = '2026-10-14'
    card['sum'] = 'Не раскрыта'
    card['eco']['sum'] = 'Не раскрыта'
    card['seller'] = SELLER
    card['seller_src'] = 'text'
    card['src'] = [list(s) for s in SRC]
    card['kind'] = 'acquisition'
    card['party_evidence']['seller'] = [{'value': SELLER, 'field': 'seller',
                                         'method': 'manual_source_review', 'url': DN + '1025901607533'}]
    for ev in card.get('events', []):
        if ev.get('kind') == 'closed':
            assert ev['date'] == '2026-11-11', ev['date']
            ev['date'] = '2026-10-14'
    return card


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))   # читается прямо перед записью
    cards = [c for c in pending['cards'] if c['id'] == CARD_ID]
    if not cards:
        print('ОТКАЗ: %s нет в очереди' % CARD_ID)
        return 1
    if cards[0].get('seller') == SELLER:
        print('УЖЕ ПРИМЕНЕНО')
        return 0
    card = patch(cards[0])
    print(json.dumps({k: card.get(k) for k in ('date', 'sum', 'buyer_name', 'seller', 'asset', 'src', 'kind')},
                     ensure_ascii=False, indent=1))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
