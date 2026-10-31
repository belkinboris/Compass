# -*- coding: utf-8 -*-
"""Новая карточка: «Гельтек» (производитель косметики, владелец Сергей
Кирш, бренды Geltek Baby и The U) купил бренд детской декоративной
косметики Nomi — с 13 октября 2026 ООО «Гельтек РНД» (100%-я дочка
«Гельтека») владеет 100% ООО «Компания новая идея», управляющей
компании бренда. Продавец не назван ни в одном источнике; доля именно
в Nomi (в отличие от доли в управляющей компании) отдельно не
уточняется. Сумма не раскрыта — Кирш сам отказался ее назвать
(New Retail). Статус «Закрыта» (переход контроля уже зарегистрирован).

Ворота отклонили черновик («не установлен предмет сделки» — заголовок
не называет ни сумму, ни явный актив по форме, которую матчер ждет).
Продавец и сумма — по новому правилу (искать обязательно) — искал
отдельным саб-агентом (WebSearch), нашел два независимых пересказа
того же сюжета (Sostav.ru, New Retail — оба со ссылкой на Shopper's,
первоисточник которого недоступен), ни продавца, ни суммы не нашел ни
в одном источнике, включая профильные (РБК, Коммерсантъ, Forbes не
писали) — честная пустота после настоящей попытки.

Источники (прочитаны полностью, кэш data/inbox/raw/2026-10-15-articles.jsonl):
  Retailer.ru (15.10.2026, со ссылкой на Shopper's)
    https://retailer.ru/brend-detskoj-kosmetiki-nomi-pereshjol-pod-kontrol-gelteka/
  New Retail (14.10.2026, прямая цитата Кирша, самый подробный пересказ)
    https://new-retail.ru/novosti/retail/geltek_priobryel_brend_detskoy_dekorativnoy_kosmetiki_nomi/
  Sostav.ru (14.10.2026, тот же сюжет, доп. деталь о Murkott не по этой сделке)
    https://www.sostav.ru/publication/geltek-priobrel-brend-detskoj-kosmetiki-nomi-87737.html

Запуск:
    python3 pipeline/build_nomi_geltek_2026_10_15.py            # сухой прогон
    python3 pipeline/build_nomi_geltek_2026_10_15.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_RETAILER = ['Retailer.ru', 'https://retailer.ru/brend-detskoj-kosmetiki-nomi-pereshjol-pod-kontrol-gelteka/']
SRC_NR = ['New Retail', 'https://new-retail.ru/novosti/retail/geltek_priobryel_brend_detskoy_dekorativnoy_kosmetiki_nomi/']
SRC_SOSTAV = ['Sostav.ru', 'https://www.sostav.ru/publication/geltek-priobrel-brend-detskoj-kosmetiki-nomi-87737.html']

BUYER_PROFILE = {
    'name': 'Гельтек',
    'ind': 'Потребительские товары',
    'desc': ('Российский производитель косметики, владелец — Сергей Кирш; бренды Geltek Baby '
             '(уход за детской кожей) и молодежная косметика The U. Покупку Nomi провел через '
             'свою 100%-ю дочку ООО «Гельтек РНД».'),
}

TARGET_PROFILE = {
    'name': 'Nomi',
    'ind': 'Потребительские товары',
    'desc': ('Бренд детской декоративной косметики на рынке с 2015 года: блеск для губ, тени, '
             'тушь для волос, кремы, румяна, лаки для ногтей. Компоненты закупают в Европе, '
             'производство — на контрактных фабриках в России. Управляющее юрлицо — ООО '
             '«Компания новая идея».'),
}

DRAFT = {
    'date': '2026-10-13',
    'title': 'Бренд детской косметики Nomi перешел под контроль «Гельтека»',
    'ind': 'Потребительские товары',
    'type': 'M&A',
    'status': 'Закрыта',
    'src': [SRC_RETAILER, SRC_NR, SRC_SOSTAV],
}


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))
    promoted = json.load(open(DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in promoted['deals']} \
        | set(promoted.get('companies', {}).keys())
    if any('Nomi' in (c.get('title') or '') for c in pending['cards']):
        print('ОТКАЗ: похожая карточка уже в pending.json')
        return 1

    buyer_id = promote.new_id(existing_ids)
    existing_ids.add(buyer_id)
    target_id = promote.new_id(existing_ids)
    existing_ids.add(target_id)
    card_id = promote.new_id(existing_ids)

    card = promote.to_card(DRAFT, card_id)
    card['buyer'] = buyer_id
    card['target'] = target_id
    card['asset'] = 'Nomi'
    card['pending_since'] = datetime.now(timezone.utc).isoformat()

    print('НОВАЯ КАРТОЧКА %s: %s' % (card_id, card['title']))
    print('  профиль покупателя %s: %s' % (buyer_id, BUYER_PROFILE['name']))
    print('  профиль предмета %s: %s' % (target_id, TARGET_PROFILE['name']))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh_pending = json.load(open(PENDING, encoding='utf-8'))
    if any(c['id'] == card_id for c in fresh_pending['cards']):
        print('ОТКАЗ: id уже занят — перечитайте и повторите')
        return 1
    fresh_pending['cards'].append(card)
    json.dump(fresh_pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    fresh_promoted = json.load(open(DATA, encoding='utf-8'))
    if buyer_id in fresh_promoted['companies'] or target_id in fresh_promoted['companies']:
        print('ОТКАЗ: id профиля уже занят — перечитайте и повторите')
        return 1
    fresh_promoted['companies'][buyer_id] = BUYER_PROFILE
    fresh_promoted['companies'][target_id] = TARGET_PROFILE
    json.dump(fresh_promoted, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
