# -*- coding: utf-8 -*-
"""Карточка g74dbc4b1, Валентин Петухов (Wylsacom) получил 30% ООО «Иммортал»: структурные поля
по статье «Ведомостей» и истории участников ЕГРЮЛ (владелец, 18 ноября 2026: «ты спокойно можешь
по реестру дату посмотреть, в статье даже указаны названия ООО»).

ЧТО СТАВИТСЯ И ПОЧЕМУ:
  * дата 17.11.2026 — запись ЕГРЮЛ о новых участниках (datanewton, история участников,
    ОГРН 1257700437136; в реестре имя через ноль: ООО «ИММ0РТАЛ», ИНН 9714081731).
  * тип — инвестиция, продавца нет: уставный капитал вырос с 10 000 до 25 000 руб., Петухов и
    Агневский внесли по 7 500 руб. и получили по 30%, номинал доли Меркулова (10 000 руб.) не
    изменился — его доля размыта до 40%, а не продана.
  * статус «Закрыта»: изменение уже внесено в реестр.
  * сумма не раскрыта: стороны на запросы «Ведомостей» не ответили.

Запуск:
    python3 pipeline/build_wylsacom_immortal_2026_11_18.py            # сухой прогон
    python3 pipeline/build_wylsacom_immortal_2026_11_18.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CARD_ID = 'g74dbc4b1'
VED = 'https://www.vedomosti.ru/media/articles/2026/11/18/1413027-wylsacom-stal-sovladeltsem'
EGRUL = 'https://datanewton.ru/contragents/1257700437136'
TITLE = 'Валентин Петухов (Wylsacom) получил 30% разработчика ИИ-сервисов «Иммортал»'
BUYER = 'Валентин Петухов (Wylsacom)'
ASSET = '«Иммортал»'


def patch(card):
    assert card['title'] == 'Wylsacom стал совладельцем разработчика ИИ-сервисов', card['title']
    assert card['date'] == '2026-11-18' and card['status'] == 'Обсуждается' and card['type'] == 'M&A', \
        (card['date'], card['status'], card['type'])
    assert card.get('buyer_name') == 'Wylsacom' and card.get('asset') == 'разработчик ИИ-сервисов'
    assert [s[1] for s in card['src']] == [VED], card['src']
    card['title'] = TITLE
    card['date'] = '2026-11-17'
    card['status'] = 'Закрыта'
    card['type'] = 'Инвестиция'
    card['kind'] = 'financing'
    card['ind'] = 'Искусственный интеллект'
    card['buyer_name'] = BUYER
    card['asset'] = ASSET
    card['sum'] = 'Не раскрыта'
    card['eco']['sum'] = 'Не раскрыта'
    card['src'].append(['ЕГРЮЛ: ООО «ИММ0РТАЛ», история участников', EGRUL])
    card['party_evidence'] = {
        'buyer': [{'value': BUYER, 'field': 'buyer_name', 'method': 'manual_source_review', 'url': EGRUL}],
        'target': [{'value': ASSET, 'field': 'asset', 'method': 'manual_source_review', 'url': VED}],
    }
    return card


TITLE2 = 'Валентин Петухов (Wylsacom) и Дмитрий Агневский купили доли в разработчике ИИ-сервисов «Иммортал»'  # по 30% у каждого — в eco.share
BUYER2 = 'Валентин Петухов (Wylsacom) и Дмитрий Агневский'
SHARE2 = 'По 30% долей в ООО «Иммортал» у Валентина Петухова и Дмитрия Агневского'


def patch2(card):
    """Второе чтение: в ту же запись ЕГРЮЛ на тех же условиях вошел и Агневский — он второй инвестор."""
    assert card['title'] == 'Валентин Петухов (Wylsacom) купил 30% разработчика ИИ-сервисов «Иммортал»', card['title']
    assert card['buyer_name'] == BUYER and card['eco']['share'] == '30% доли в ООО «Иммортал»'
    card['title'] = TITLE2
    card['buyer_name'] = BUYER2
    card['eco']['share'] = SHARE2
    card['party_evidence']['buyer'] = [{'value': BUYER2, 'field': 'buyer_name', 'method': 'manual_source_review', 'url': EGRUL}]
    return card


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))   # читается прямо перед записью
    cards = [c for c in pending['cards'] if c['id'] == CARD_ID]
    if not cards:
        print('ОТКАЗ: %s нет в очереди' % CARD_ID)
        return 1
    if cards[0]['title'] == TITLE2:
        print('УЖЕ ПРИМЕНЕНО')
        return 0
    if cards[0]['title'] != 'Wylsacom стал совладельцем разработчика ИИ-сервисов':
        patch2(cards[0])
        print(TITLE2)
        if write:
            json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        return 0
    card = patch(cards[0])
    print(json.dumps({k: card.get(k) for k in ('title', 'date', 'status', 'type', 'kind', 'buyer_name', 'asset', 'sum', 'src')},
                     ensure_ascii=False, indent=1))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
