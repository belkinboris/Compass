# -*- coding: utf-8 -*-
"""ТРК «Родник» и «Алмаз»: одна сделка с двумя этапами, а не две карточки.

ЧТО ЧИНИТ. Владелец 8 сентября 2026, увидев в поиске две карточки об одной
сделке: «Вместо того чтобы делать вторую тупейшую пустую надо было
разобраться, что это две вехи (два этапа) одной сделки. Этап выставлены на
торги и этап продано».

Дубль уже слит (`pipeline/merge_specs/2026-09-08-ciups-rodnik-almaz.json`), но
слияние само по себе историю не рассказывает: у оставшейся карточки не было
НИ ОДНОГО события, и «Ход сделки» на экране не рисовался вовсе
(`timelineHtml` требует минимум двух строк). Все даты этапов при этом уже
лежали в карточке прозой — в «Условиях» и в «Контексте», то есть читатель мог
их найти, только прочитав два абзаца подряд.

Скрипт заводит ровно те два этапа, которые назвал владелец, и ничего сверх
того: 29 июля 2026 — актив выставлен на торги со стартовой ценой 12,16 млрд ₽,
17 августа 2026 — продан на публичном предложении за 6,08 млрд ₽. Три
несостоявшихся раунда между ними остаются подробностью в «Условиях»: они не
меняют картину сделки, а этап, который ничего не меняет, только удлиняет
ленту (то же правило, по которому `timelineHtml` не рисует блок из одной
строки).

ФАКТЫ ТОЛЬКО ИЗ САМОЙ КАРТОЧКИ. Ни одного числа, имени и дня, которых не было
бы в её `law.terms`, `eco.val` и `eco.context` до этой правки, — проверяется
`assert` перед записью: каждое число из текста этапа обязано встречаться в
тексте карточки.

Запуск:
    python3 pipeline/fix_trk_chelyabinsk_milestones.py            # сухой прогон
    python3 pipeline/fix_trk_chelyabinsk_milestones.py --write
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'

DEAL_ID = 'gmru-psb-tpk-chelyabinsk'

EVENTS = [
    {
        'kind': 'announced',
        'date': '2026-07-29',
        'title': 'Актив выставлен на торги',
        'note': ('Росимущество выставило на торги 100% ООО «Родник» и ООО '
                 '«Управляющая компания «Содействие»» единым лотом. Стартовая '
                 'цена — 12 164 397 000 ₽, задаток для участия — '
                 '2 432 879 400 ₽. Заявки принимали с 29 июля по 4 августа '
                 '2026 года.'),
        'source': ['Ведомости',
                   'https://www.vedomosti.ru/strana/ural/news/2026/07/29/1217268-snova-vistavili'],
    },
    {
        'kind': 'closed',
        'date': '2026-08-17',
        'title': 'Сделка завершена',
        'note': ('Продажа состоялась с четвёртой попытки — на публичном '
                 'предложении, после трёх несостоявшихся аукционов. Лот ушёл за '
                 '6 082 198 500 ₽, вдвое дешевле стартовой цены. Победителем '
                 'стало петербургское ООО «Центр инжиниринговых услуг при '
                 'проектировании и строительстве».'),
        'source': ['Ведомости',
                   'https://www.vedomosti.ru/realty/articles/2026/08/17/1221818-vladelets-otelya-vikupaet-tsentri'],
    },
]

NUM = re.compile(r'\d[\d\s ]*(?:[.,]\d+)?')


def digits(text):
    """Числа текста без пробелов-разделителей — чтобы «12 164 397 000» и
    «12 164 397 000 ₽» считались одним числом."""
    return {re.sub(r'[\s ]', '', m.group(0)).rstrip('.,') for m in NUM.finditer(text)}


def card_text(card):
    return json.dumps(card, ensure_ascii=False)


def main(write=False):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    deal = next((d for d in data['deals'] if d['id'] == DEAL_ID), None)
    assert deal, 'карточки %s нет в базе' % DEAL_ID
    assert not deal.get('events'), 'у карточки уже есть этапы: %r' % (deal.get('events'),)

    # Ни одного числа из ниоткуда: каждое число этапа обязано быть в карточке.
    have = digits(card_text(deal))
    for ev in EVENTS:
        invented = sorted(d for d in digits(ev['note'] + ' ' + ev['title']) if d not in have)
        assert not invented, ('в этапе %s есть числа, которых нет в карточке: %s'
                              % (ev['kind'], invented))
        assert ev['source'][1] in card_text(deal), 'источник этапа не из карточки: %s' % ev['source'][1]

    print('=== %s: этапы ===' % DEAL_ID)
    for ev in EVENTS:
        print(' %s · %s · %s' % (ev['date'], ev['kind'], ev['title']))
        print('   ', ev['note'])
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['events'] = EVENTS
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    print('\nЗаписано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
