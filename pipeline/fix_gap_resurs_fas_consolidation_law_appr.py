# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g99448cd9 (ГАП «Ресурс»
выкупила 4 агрокомпании в Саратовской области, декабрь 2024): дельта-поиск
разрешил вопрос, прямо поставленный самой карточкой в law.appr («может
попытаться консолидировать 100% доли... как только получит одобрение от
ФАС»; ведомство на тот момент ходатайство не получало). 6 мая 2025 года ФАС
одобрила ходатайство ООО «Ростовская зерновая компания «Ресурс» (РЗК
«Ресурс», входит в ГАП «Ресурс») о приобретении оставшихся 70% долей в тех
же четырёх юрлицах (Клин-2002, Садко, Белопольское, Аверо) — с учётом уже
имевшихся долей итоговая доля составила 100%. Не через review.py: цитата
из НОВОГО источника (oleoscope.com) отвечает на вопрос, поставленный в поле,
которое уже содержит текст из другого источника.

Запуск: python3 pipeline/fix_gap_resurs_fas_consolidation_law_appr.py
        python3 pipeline/fix_gap_resurs_fas_consolidation_law_appr.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g99448cd9'

OLD_APPR = (
    'По мнению собеседника “Ъ”, ГАП «Ресурс» может попытаться '
    'консолидировать 100% доли в приобретенных юрлицах, как только получит '
    'одобрение от Федеральной антимонопольной службы. В ведомстве заявили '
    '“Ъ”, что пока не получали соответствующее ходатайство.'
)
APPR_ADDITION = (
    ' 6 мая 2025 года ФАС одобрила ходатайство ООО «Ростовская зерновая '
    'компания «Ресурс» (РЗК «Ресурс», входит в ГАП «Ресурс») о приобретении '
    'оставшихся 70% долей в этих же четырёх юрлицах — с учётом уже '
    'имевшихся долей итоговая доля составила 100%.'
)
NEW_APPR = OLD_APPR + APPR_ADDITION

NEW_SRC = [
    ['Oleoscope', 'https://oleoscope.com/news/fas-razreshila-gap-resurs-pokupku-aktivov-maslichnyh/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['appr'] == OLD_APPR
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== law.appr: станет ===')
    print(NEW_APPR)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['law']['appr'] = NEW_APPR
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
