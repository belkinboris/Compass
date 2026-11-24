# -*- coding: utf-8 -*-
"""Приемка партии 5 (16-19 ноября, очередь 24 ноября 2026) поправила два
факта структурным скриптом/прямой правкой без вызова fact_edit_guard.log() —
prepush_check.py отказал пушить: «правка факта без подтверждающей цитаты у
2 полей»: g13f5c85b date ('2026-11-06' -> '2026'), g93df6a58 eco.share
('50% долей в группе «Комфорт»' -> '50% акций в АО «ВК Комфорт»»). Значения
полей уже стоят верно (проверено assert) — этот скрипт только дописывает
подтверждения в card['fact_log'].

g13f5c85b: источники («Коммерсантъ», https://www.kommersant.ru/doc/9081283)
говорят только, что «Рубеж» ПРИОБРЕЛ площади — без дня сделки; 06.11.2026
был днем публикации, не днем события (date_basis у карточки не стоял) —
день снят до года.

g93df6a58: предмет сделки — АО «ВК Комфорт» (ИНН 7706724054), а не ООО
«Комфорт», и доля оформлена как акции (АО), не доли (ООО) — подтверждено
независимо по девяти агрегаторам реестра (rusprofile.ru, Контур.Фокус,
companies.rbc.ru, saby.ru, checko.ru и др., см. accepted_notes.notes
карточки) и собственной историей компании (spark.ru: «Ведис Комфорт» ->
«ВК Комфорт», АО). Цитата — не из статьи-первоисточника (та за платным
доступом), а описание самой находки с привязкой к проверенному ИНН.

Запуск: python3 pipeline/fact_log_2026_11_24_batch5.py --write
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'приток, 24 ноября 2026'

ENTRIES = [
    ('g13f5c85b', 'date', '2026',
     '«Рубеж», российский разработчик интеллектуальных систем безопасности, приобрел 5 тыс. кв. м '
     'офисной недвижимости в офисном здании «Upside Кунцево» на западе Москвы. Об этом рассказали '
     'два источника "Ъ" на рынке недвижимости.',
     'https://www.kommersant.ru/doc/9081283'),
    ('g93df6a58', 'eco.share', '50% акций в АО «ВК Комфорт»',
     'Предмет сделки — АО «ВК Комфорт» (ИНН 7706724054, КПП 770801001, ОГРН 1097746503106, Москва, '
     'рег. 02.09.2009, ген. директор Алексей Яценко) — подтверждено независимо минимум девятью '
     'агрегаторами реестра (rusprofile.ru, Контур.Фокус, companies.rbc.ru, saby.ru, checko.ru и др.) '
     'и собственной историей компании по блогу на spark.ru (создана в 2009 как «Ведис Комфорт», '
     'переименована в «ВК Комфорт»); форма АО означает акции, не доли.',
     'https://www.vedomosti.ru/realty/articles/2026/11/10/1243876-fsk-vishla-iz-kapitala'),
]


def get_field(card, field):
    if '.' in field:
        head, tail = field.split('.', 1)
        return (card.get(head) or {}).get(tail)
    return card.get(field)


def apply(data):
    cards = {d['id']: d for d in data['deals']}
    for cid, field, new, quote, url in ENTRIES:
        card = cards[cid]
        cur = get_field(card, field)
        assert cur == new, '%s %s: ожидали %r, стоит %r' % (cid, field, new, cur)
        fact_edit_guard.log(card, field, new, quote, url, BY)


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    print('подтверждений добавлено: %d' % len(ENTRIES))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv[1:]))
