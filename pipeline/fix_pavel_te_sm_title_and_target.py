# -*- coding: utf-8 -*-
"""G3 (заголовки карточек — «звучит по-человечески», юрлицо вместо реального
имени), месячный прогон качества 18.09.2026: карточка `g672c6dfe`
(«Павел Тё вышел из капитала ООО «СМ»»).

ООО «СМ» — не реальный бизнес, а холдинговая прослойка без собственного
имени/бренда: её единственный актив — 25%-я доля в ООО «Рязанская
чаеразвесочная фабрика» (РЧФ), реальном, узнаваемом бизнесе (бренды «Три
дружных слона», TeaTale). У этой же сделки уже есть карточка-близнец на
ВХОД в позицию — `g9f76fe60` («Павел Тё приобрел 25% Рязанской
чаеразвесочной фабрики», 2023 год) — она называет реальный бизнес в
заголовке и ссылает `target` на профиль РЧФ (`g8ee31e1c`), а не на
промежуточную прослойку. Карточка о ВЫХОДЕ должна называться и быть
привязана так же, для единообразия и понятности читателю: заголовок с
именем незнакомой аббревиатуры «СМ» ничего не сообщает о том, о каком
бизнесе вообще идёт речь.

Дословная цитата (Коммерсантъ, doc/7923870, уже в `src`) подтверждает
связь: «Подконтрольное Павлу Тё ООО «Велна» вышло из числа соучредителей
ООО СМ, на балансе которого находились 25% в ООО «Рязанская
чаеразвесочная фабрика» (РЧФ)» — это же предложение уже дословно лежит в
`eco.context` карточки. Осторожность прежнего чтения (сохранилась ли доля
РЧФ у «СМ» после смены владельцев «СМ», источник не уточняет) относится к
СТРУКТУРЕ доли, а не к тому, что Тё вышел из своей экономической позиции в
РЧФ, — это переименование не добавляет и не убирает ни одного факта,
только называет уже описанную связь в заголовке и структурной ссылке.

Запуск: python3 pipeline/fix_pavel_te_sm_title_and_target.py           # проверка
        python3 pipeline/fix_pavel_te_sm_title_and_target.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g672c6dfe'
OLD_TITLE = 'Павел Тё вышел из капитала ООО «СМ»'
NEW_TITLE = 'Павел Тё вышел из доли в Рязанской чаеразвесочной фабрике'
OLD_TARGET = 'goooosm'
NEW_TARGET = 'g8ee31e1c'
RCF_NAME = 'Рязанская чаеразвесочная фабрика'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в deals_promoted.json' % CARD_ID
    assert card['title'] == OLD_TITLE, 'title уже другой: %r' % card['title']
    assert card.get('target') == OLD_TARGET, 'target уже другой: %r' % card.get('target')

    rcf = data['companies'].get(NEW_TARGET)
    assert rcf is not None, '%r не найден в companies' % NEW_TARGET
    assert rcf.get('name') == RCF_NAME, 'неверный профиль: %r' % rcf.get('name')

    print('ПРАВИМ %s:' % CARD_ID)
    print('  title:  %r -> %r' % (OLD_TITLE, NEW_TITLE))
    print('  target: %r -> %r (%s)' % (OLD_TARGET, NEW_TARGET, RCF_NAME))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['title'] = NEW_TITLE
    card['target'] = NEW_TARGET
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
