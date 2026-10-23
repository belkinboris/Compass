# -*- coding: utf-8 -*-
"""Новая карточка: структура группы «Ареал» (бывшая Highland Gold) получила
75% ООО «Аврора-Ресурс» — владельца лицензии на рудное золото на
Пертинъярвинском участке в Карелии (по просьбе партнёра, Коммерсантъ
23 октября 2026).

ПОЧЕМУ РУКАМИ. Фильтр притока не узнал заголовок «вошли в золотодобывающий
проект» (починен коммитом ac723a49). Карточка собирается так же, как кнопкой
«в работу»: черновик → `promote.to_card` → `pending.json` с `pending_since`;
дальше обычный путь (write_card.py, accept_card.py, второе чтение,
send_drafts.py).

ЧТО ИЗВЕСТНО И ЧЕГО НЕТ (сверено со статьёй и реестрами):
  * покупатель формально — АО «Кросс Холдинг» (ИНН 9725127025), им с
    6 ноября 2025 управляет МКАО «Ареал» (ИНН 2540277272, профиль
    `gb6301f1c` «Highland Gold»); группой профиль покупателя не
    подменяется (docs/card_parties.md, «Покупатель — ровно в раскрытой
    части и формально»). 20 октября 2026 МКАО «Ареал» стало и управляющей
    компанией «Аврора-Ресурс».
  * продавец — АО «Аврора-Менеджмент» (ИНН 4716018750): по истории
    участников ЕГРЮЛ (datanewton) 16 октября 2026 его доля упала со 100% до
    25% (2 500 ₽), а «Кросс Холдинг» получил 75% (7 500 ₽); уставный капитал
    не менялся (10 000 ₽) — это переход доли, а не допэмиссия.
  * дата — 2026-10-16, запись о смене участников в ЕГРЮЛ
    (docs/card_status_dates.md, «Дата — день события»).
  * сумма не раскрыта; 300–500 млн ₽ — оценка всего месторождения с учётом
    капзатрат Максимом Шапошниковым (советник управляющего фондом
    «Индустриальный код») — в eco.val, не в sum.
  * лицензия ПТЗ 01645 БР по региональному реестру (на 1 марта 2017 года)
    выдана 16 января 2012 года «Аврора-Менеджменту» сроком до 15 января
    2037 года; «2011» из пересказа партнёра — дата соседней лицензии
    (Соанварский участок), «запасы на балансе с 2018 года» — ни в одном
    найденном источнике, в карточку не идёт.

id — константой (docs/intake_run.md, «id ручной сборки — константой»):
повторный запуск не заводит второй карточки.

Запуск:
    python3 pipeline/build_areal_aurora_2026_10_23.py            # сухой прогон
    python3 pipeline/build_areal_aurora_2026_10_23.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g5e1a7c24'
AREAL = 'gb6301f1c'   # профиль «Highland Gold» = МКАО «Ареал», ИНН 2540277272

KOMMERSANT = ['Коммерсантъ', 'https://www.kommersant.ru/doc/9044869']
ABN = ['Агентство Бизнес Новостей', 'https://abn.agency/2026/10/23/struktury-areala-poluchili-kontrol-nad-zolotorudnym-proektom-v-karelii/']
MERGERS = ['Mergers.ru', 'https://mergers.ru/news/Struktury-Areal-voshli-v-zolotodobyvayuschij-proekt-v-Karelii-87685']
EGRUL = ['ЕГРЮЛ: история участников «Аврора-Ресурс»',
         'https://datanewton.ru/api/v2/history?ogrn=1097847297503&startDate=2000-01-01&attributes=OWNERS']
NEDRA = ['Недра Карелии: реестр лицензий', 'http://nedrark.karelia.ru/licenz_deistv_neob.php']

SELLER = 'АО «Аврора-Менеджмент»'

DRAFT = {
    'date': '2026-10-16',
    'title': 'Структура «Ареала» получила 75% золоторудного проекта в Карелии',
    'ind': 'ГМК и добыча',
    'type': 'M&A',
    'status': 'Закрыта',
    'sum': 'Не раскрыта',
    'src': [KOMMERSANT, ABN, MERGERS, EGRUL, NEDRA],
    'asset': '75% ООО «Аврора-Ресурс»',
    'seller': SELLER,
    'events': [{
        'kind': 'closed',
        'date': '2026-10-16',
        'title': '«Кросс Холдинг» стал владельцем 75% «Аврора-Ресурс»',
        'note': 'В ЕГРЮЛ записано, что доля «Аврора-Менеджмента» сократилась со 100% до 25%, '
                'а 75% перешли к АО «Кросс Холдинг» из группы «Ареал».',
        'source': EGRUL,
    }],
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    if any(c['id'] == CARD_ID for c in pending['cards']) or any(d['id'] == CARD_ID for d in promoted['deals']):
        print('УЖЕ ЕСТЬ: %s — повторно не собираю' % CARD_ID)
        return 0
    assert promoted['companies'][AREAL]['name'] == 'Highland Gold', promoted['companies'][AREAL]['name']
    for c in pending['cards'] + promoted['deals']:
        blob = json.dumps(c, ensure_ascii=False)
        if 'Аврора-Ресурс' in blob or 'Пертинъярв' in blob:
            print('ОТКАЗ: похожая карточка уже есть: %s %s' % (c['id'], c['title']))
            return 1

    card = promote.to_card(DRAFT, CARD_ID)
    card['eco']['sum'] = 'Не раскрыта'
    # Подписи реестров — свои: edition_label по домену дал бы «Datanewton.ru».
    card['src'] = [list(s) for s in DRAFT['src']]
    card['events'][0]['source'] = list(EGRUL)
    card['kind'] = 'acquisition'
    card['party_evidence'] = {
        'seller': [{'value': SELLER, 'method': 'registry_owner_history', 'url': EGRUL[1]}],
        'target': [{'value': DRAFT['asset'], 'field': 'asset', 'method': 'registry_owner_history',
                    'url': EGRUL[1]}],
    }
    card['pending_since'] = datetime.now(timezone.utc).isoformat()
    print('НОВАЯ КАРТОЧКА %s: %s' % (CARD_ID, card['title']))
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))  # перечитать прямо перед записью
    if any(c['id'] == CARD_ID for c in fresh['cards']):
        print('УЖЕ ЕСТЬ в pending.json — не пишу')
        return 0
    fresh['cards'].append(card)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
