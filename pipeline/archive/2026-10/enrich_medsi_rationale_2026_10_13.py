# -*- coding: utf-8 -*-
"""Карточка `gcf05509a` — vc.ru (пересказ РБК, `raw_screen.py --enrich
d82866850=gcf05509a`) дает то, чего не было ни у Коммерсанта, ни у
Ведомостей: прямую цитату официальной позиции ОБЕИХ сторон о мотивах
сделки (а не только прогноз стороннего аналитика) и свежие
финансовые показатели «Медси» за первое полугодие 2026 года.

eco.context: хвост про мотив банка держался на предположении аналитика
Aspring Capital («параллель... увидел аналитик» — его собственная догадка,
не позиция банка). Теперь есть дословная позиция АФК «Система» («сделка —
закономерный шаг в подготовке к возможному IPO») и самого Альфа-банка
(«участие в капитале компании с растущим бизнесом», «портфель качественных
активов», курс на миноритарные доли) — аналитик остается, но его оценка
(объем портфеля ~50 млрд ₽, срок и доходность) теперь явно подчинена
прямым цитатам сторон, а не заменяет их.

eco.target_fin: добавлены показатели «Медси» за 1-е полугодие 2026 года
(выручка, чистая прибыль, доля рынка) — цифры за 2025 год не трогаются.

Источник: vc.ru (пересказ РБК) https://vc.ru/money/3191949-alfabank-aktsioner-seti-klinik-medsii

Запуск:
    python3 enrich_medsi_rationale_2026_10_13.py            # сухой прогон
    python3 enrich_medsi_rationale_2026_10_13.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
CARD_ID = 'gcf05509a'
VC_RU = ['vc.ru', 'https://vc.ru/money/3191949-alfabank-aktsioner-seti-klinik-medsii']

OLD_TARGET_FIN = ('Cosmos Hotel Group: 100 отелей, 5 брендов; выручка за 2025 год — 20,9 млрд '
                   '₽ (+20%); OIBDA — 7,3 млрд ₽ (+27%); рентабельность по OIBDA — 35%. '
                   '«Медси»: 138 клиник (на 31.12.2025); выручка за 2025 год — 61,4 млрд ₽ '
                   '(+22%); скорректированная OIBDA — 13,2 млрд ₽; чистая прибыль — 5,2 млрд '
                   '₽; чистый долг/OIBDA — 0,2x.')
NEW_TARGET_FIN = OLD_TARGET_FIN + (' В первом полугодии 2026 года «Медси» увеличила выручку на '
                                    '14,2% — до 34,5 млрд ₽, чистая прибыль превысила 3 млрд ₽ '
                                    '(+14,3%); доля компании на рынке коммерческой медицины — '
                                    '3,5%.')

OLD_CONTEXT_TAIL = ('Параллель с собственной стратегией банка увидел аналитик Aspring Capital '
                     'Темир Азизбек: он напоминает, что Альфа-банк формирует портфель '
                     'миноритарных долей в растущих компаниях с целью довести его объем до 50 '
                     'млрд ₽. Левицкий лишь предполагает срок и доходность: два-четыре года и '
                     '20-25% — но это его прогноз, не позиция банка.')
NEW_CONTEXT_TAIL = ('Свои мотивы назвали обе стороны: в АФК «Система» сделку назвали '
                     '«закономерным шагом в подготовке компании к возможному выходу на биржу в '
                     'среднесрочной перспективе», а в Альфа-банке объяснили интерес к покупке '
                     'доли в «компании с растущим бизнесом» общей стратегией — и дальше '
                     'набирать именно такие, преимущественно миноритарные, пакеты. Аналитик '
                     'Aspring Capital Темир Азизбек оценивает итоговый объем такого портфеля '
                     'банка в 50 млрд ₽; сроки и доходность (два-четыре года, 20-25%) — это '
                     'прогноз Левицкого, а не позиция банка.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    card = by_id[CARD_ID]

    assert card['eco']['target_fin'] == OLD_TARGET_FIN
    assert OLD_CONTEXT_TAIL in card['eco']['context']

    print('ПРАВКА %s: eco.target_fin (+1п2026), eco.context (мотив — цитаты сторон), +src vc.ru' % CARD_ID)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    card['eco']['target_fin'] = NEW_TARGET_FIN
    card['eco']['context'] = card['eco']['context'].replace(OLD_CONTEXT_TAIL, NEW_CONTEXT_TAIL)
    existing_urls = {s[1] for s in card.get('src', []) if len(s) > 1}
    if VC_RU[1] not in existing_urls:
        card.setdefault('src', []).append(list(VC_RU))

    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_by_id = {d['id']: d for d in fresh['deals']}
    fresh_card = fresh_by_id[CARD_ID]
    assert fresh_card['eco']['target_fin'] == OLD_TARGET_FIN, 'карточку кто-то уже поправил — перечитайте'
    idx = fresh['deals'].index(fresh_card)
    fresh['deals'][idx] = card
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
