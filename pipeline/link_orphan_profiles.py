# -*- coding: utf-8 -*-
"""Профили без сделок — связать те, чьё имя уже написано в карточке.

ЗАЧЕМ. 157 профилей компаний не привязаны ни к одной сделке: страница
компании открывается и честно говорит «сделок в базе нет». У части из них
сделка на самом деле есть — просто сторона записана в карточке ТЕКСТОМ, а не
ссылкой на профиль: у карточки «Аэрофлот» приобрел 80% оператора
контакт-центров» продавец записан строкой «Teleperformance», и рядом в базе
лежит профиль «Teleperformance SE», о котором карточка не знает.

ГРАНИЦА. Связываем ТОЛЬКО при точном совпадении имени после снятия правовой
формы («ООО», «АО», «Ltd», «Group», «SE») и знаков препинания. Никакого
похожего написания, никакого вхождения подстрокой: «Продавец — «Интеррос»» и
профиль «Интеррос Капитал» — разные лица, и правило вхождения связало бы их.
Роль не выдумывается: она уже написана в карточке, мы лишь заменяем текст
ссылкой на профиль.

ЗАМЕР. Из 157 профилей имя встречается в тексте хотя бы одной карточки у 82,
ровно в одной — у 57, но ТОЧНОЕ совпадение с полем стороны есть только у 16,
а после ужесточения (сравнивать имя профиля, а не его псевдонимы) — у 13.
Остальные упоминаются в описании, а не в роли, и связывать их по упоминанию
значило бы назначать роль догадкой.

ПОЧЕМУ УЖЕСТОЧИЛИ. Первая версия сравнивала и псевдонимы, и юридическое
название — и дала три связки, две из которых неверны: продавец «Hempel»
указал на профиль «Hempel (российский завод)», а продавец «Morgan Stanley» —
на «Morgan Stanley (ТРЦ «Галерея»)». В обоих случаях профиль описывает
ПРЕДМЕТ сделки, а не её сторону; уточнение в скобках как раз и отличает одно
от другого. Это тот же дефект, что ловит `test_asset_is_not_a_party`, только
пришедший бы с другой стороны — не из данных, а из правила связывания.

ПОЧЕМУ `buyer_name` УДАЛЯЕТСЯ. У покупателя две формы записи — ссылка
(`buyer`) и имя текстом (`buyer_name`), и заполнять обе одновременно нельзя:
это ловит тест. Продавца это не касается: `seller` и `seller_id` в базе
сосуществуют, интерфейс предпочитает профиль.

Запуск:
    python3 pipeline/link_orphan_profiles.py            # сухой прогон
    python3 pipeline/link_orphan_profiles.py --write    # записать
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# Текстовое поле стороны -> поле-ссылка на профиль.
PAIRS = {'seller': 'seller_id', 'buyer_name': 'buyer', 'asset': 'target'}


def key(value):
    """Имя без правовой формы и знаков препинания — для точного сравнения."""
    text = str(value or '').lower().replace('ё', 'е')
    text = re.sub(r'\b(?:ооо|оао|зао|пао|ао|гк|ук|мкао|мкпао|ltd|llc|inc|plc|group|holding|se)\b',
                  ' ', text)
    return re.sub(r'[^a-zа-я0-9]+', '', text)


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals, companies = data['deals'], data['companies']
    match_keys = data.get('match_keys') or {}

    used = set()
    for d in deals:
        for field in ('buyer', 'target', 'seller_id', 'asset_id'):
            if d.get(field):
                used.add(d[field])
    orphans = {cid: c for cid, c in companies.items() if cid not in used}
    print('профилей без единой сделки: %d' % len(orphans))

    # Имя -> профиль. Если одно и то же имя у двух профилей, не связываем
    # ни один: выбор между ними был бы догадкой.
    by_name, ambiguous = {}, set()
    for cid, company in orphans.items():
        # Сравниваем ТОЛЬКО имя профиля, без псевдонимов и юридического
        # названия. По псевдониму «Hempel» продавец связался бы с профилем
        # «Hempel (российский завод)» — а это ПРЕДМЕТ сделки, а не её сторона:
        # ровно тот дефект, который в базе уже ловит `test_asset_is_not_a_party`.
        # Уточнение в скобках («(ТРЦ «Галерея»)», «(российский завод)») тем
        # самым остаётся значимым, и такие профили правило не трогает.
        k = key(company.get('name'))
        if len(k) >= 5:
            if k in by_name and by_name[k] != cid:
                ambiguous.add(k)
            by_name.setdefault(k, cid)
    for k in ambiguous:
        by_name.pop(k, None)

    plan = []
    for deal in deals:
        for text_field, ref_field in PAIRS.items():
            if deal.get(ref_field) or not deal.get(text_field):
                continue
            cid = by_name.get(key(deal[text_field]))
            if cid:
                plan.append((deal, text_field, ref_field, cid))

    for deal, text_field, ref_field, cid in plan:
        print('   %-12s %-11s «%s» -> %s «%s»'
              % (deal['id'], text_field, str(deal[text_field])[:30], cid,
                 str(companies[cid].get('name'))[:32]))
    print('\nсвязок: %d, профилей получат сделку: %d'
          % (len(plan), len({c for *_, c in plan})))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for deal, text_field, ref_field, cid in plan:
        assert not deal.get(ref_field), '%s: %s уже заполнено' % (deal['id'], ref_field)
        assert key(deal[text_field]) == key(companies[cid].get('name')), \
            '%s: имя перестало совпадать с именем профиля %s' % (deal['id'], cid)
        deal[ref_field] = cid
        if text_field == 'buyer_name':
            # Обе формы записи покупателя одновременно держать нельзя.
            deal.pop('buyer_name', None)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
