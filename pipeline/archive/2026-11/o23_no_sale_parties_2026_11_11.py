# -*- coding: utf-8 -*-
"""Карточка очереди g90767425 («О23» / Ozon): утрата контроля — не продажа.

Второе чтение дважды вернуло карточку: подпись «Продавец» в схеме и строки
«Покупатель: не раскрыт / Продавцы: …» в посте сообщают о продаже, которой ни
один источник не подтверждает («у АО «О23» отсутствует новый контролирующий
акционер» — РБК, ПРАЙМ; «каким образом структуры Чачавы утратили контроль… и
кому перешли их доли, она не уточняет» — Frank Media). Поэтому:
  * сторон в схеме нет, причина — в `no_parties` (как у временного управления);
  * проект поста задан текстом (`post_override`) без строк покупателя и продавца —
    владелец правит и одобряет его в консоли, как любой проект поста;
  * `law.struct`: «кто получил доли» → «перешли ли акции к кому-то» (в одном
    ключе с полем доли).

    python3 pipeline/archive/2026-11/o23_no_sale_parties_2026_11_11.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CID = 'g90767425'
OLD_SELLER = 'Александр Чачава и подконтрольные ему структуры'
OLD_TAIL = 'Кто получил доли и как именно Чачава лишился контроля, Ozon не сообщил.'
NEW_TAIL = 'Как именно Чачава лишился контроля и перешли ли его акции к кому-то, Ozon не сообщил.'
NO_PARTIES = ('Утрата контроля, а не продажа: покупателя и продавца источники не называют. Контроль над АО «О23» '
              'утратили Александр Чачава и подконтрольные ему структуры; нового контролирующего акционера, по '
              'уведомлению «О23», нет.')
POST = ('<b>Александр Чачава лишился контроля над «О23», крупнейшим акционером Ozon</b>\n\n'
        '<b>Кто утратил контроль:</b> Александр Чачава и подконтрольные ему структуры\n'
        '<b>Новый контролирующий акционер:</b> отсутствует, по уведомлению «О23»\n'
        '<b>Предмет:</b> контроль над АО «О23», которому принадлежит 34,95% акций Ozon\n'
        '<b>Как утрачен контроль:</b> не сообщается\n'
        '<b>Отрасль:</b> E-commerce\n\n'
        '<b>Источник:</b> <a href="https://www.vedomosti.ru/business/news/2026/11/11/1244594-strukturi-chachavi-utratili-kontrol">Ведомости</a>\n'
        'Еще 4 источника — в карточке сделки\n\n'
        '#потребрынок #ecommerce #MA')


def apply(doc):
    c = next(x for x in doc['cards'] if x['id'] == CID)
    assert c.get('seller') == OLD_SELLER and not c.get('buyer') and not c.get('buyer_name'), c.get('seller')
    assert c['law']['struct'].endswith(OLD_TAIL), c['law']['struct'][-90:]
    assert not c.get('post_override') and not c.get('no_parties')
    c['seller'] = None
    c['no_parties'] = NO_PARTIES
    c['law']['struct'] = c['law']['struct'][:-len(OLD_TAIL)] + NEW_TAIL
    c['post_override'] = POST
    notes = (c.get('accepted_notes') or {}).get('no_profile') or {}
    notes.pop('seller', None)
    ev = c.get('party_evidence') or {}
    ev.pop('seller', None)
    return c


def main(write):
    raw = open(PENDING, encoding='utf-8').read()
    doc = json.loads(raw)
    c = apply(doc)
    print(c['no_parties']); print(c['law']['struct'][-110:]); print(c['post_override'])
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh = json.loads(open(PENDING, encoding='utf-8').read())
    apply(fresh)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
