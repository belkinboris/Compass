# -*- coding: utf-8 -*-
"""Карточка ga58eb450 («Русал» приобрёл 26% акций индийского
глинозёмного завода Pioneer Aluminium Industries Limited) несла
ЧУЖИЕ факты сразу от ТРЁХ других, не связанных сделок — классический
случай перепутанных карточек при разборе одной большой партии
(«digest ChatGPT round1», `batch_digest_r1_auto.py`).

Проверено прямым чтением каждого источника (WebFetch):
- `law.struct` («Вертикаль Инвестиции получил более 12,5% акций ПАО
  «Софтлайн»») и `law.terms` («Lock up... 2 года») — источники
  alumnipartners.ru/projects/8947/ и interfax.ru/business/1041787 НЕ
  упоминают Русал/Pioneer вовсе, речь про Sk Capital/«Вертикаль
  Инвестиции»/Softline — это карточка `ge9937266`.
- `eco.val` (оценка Юрия Левицкого «до 1,8-2 млрд руб.») и
  `eco.target_fin` (выручка 8,1 млрд руб., прибыль 121,6 млн руб.) —
  источники vedomosti.ru/.../rosspirtprom-priobrel-vodki и retail.ru
  прямо о ДРУГОЙ сделке — «Росспиртпром»/Тульский винокуренный завод
  1911, у которой уже есть своя карточка `g3ece5143` С ЭТИМИ ЖЕ
  фактами — то есть данные не потеряны, а задвоены на чужую карточку.
- Ещё 6 из 9 записей `src` — тоже чужие (Softline, ВТБ/«Камелия»,
  тот же Тульский завод); ни одна не подтверждает факт о Pioneer
  Aluminium/Индии/глинозёме.

Оставлены только: `eco.rationale`/`eco.context`/`eco.share` (верно,
из `batch_a_2025.py`, про Pioneer) и ОДИН настоящий источник —
interfax.ru/business/1042354 (проверен: «"Русал" завершил первый этап
покупки акций в Pioneer Aluminium Industries Limited, получив 26%
акций за $243,75 млн»).

Запуск: python3 pipeline/fix_rusal_pioneer_alumina_misattribution.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ga58eb450'

OLD_LAW_STRUCT = (
    'По результатам сделки Вертикаль Инвестиции получил более 12,5% '
    'акций ПАО «Софтлайн».'
)
OLD_LAW_TERMS = 'Lock up по продаже акций — 2 года после закрытия сделки.'
OLD_ECO_VAL = (
    'Инвестиционный директор BGP Capital Юрий Левицкий оценивает '
    'стоимость предприятия до 1,8–2 млрд руб. без учета долгов.'
)
OLD_ECO_TARGET_FIN = (
    'В 2024 г. его выручка увеличилась на 37,9% до 8,1 млрд рублей, а '
    'чистая прибыль упала на 160% (121,6 млн рублей).'
)

BAD_SRC_URLS = {
    'https://alumnipartners.ru/projects/8947/',
    'https://www.interfax.ru/business/1041787',
    'https://softline.ru/about/news/pao-softlayn-obyavlyaet-o-roste-po-vsem-klyuchevym-pokazatelyam-po-itogam-2025-goda',
    'https://www.kommersant.ru/doc/7992454',
    'https://www.vedomosti.ru/business/articles/2025/08/08/1130442-rosspirtprom-priobrel-vodki',
    'https://www.pravda.ru/news/economics/2259094-ross-spirt-prom-acquires-tula-distillery/',
    'https://www.retail.ru/news/rosspirtprom-priobrel-kontrolnyy-paket-aktsiy-tulskogo-vinokurennogo-zavoda-1911-9-avgusta-2025-267711/',
    'https://tulapressa.ru/2026/03/tulskoe-pravitelstvo-vyshlo-iz-sostava-uchreditelej-vinokurennogo-zavoda/',
}


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['law']['terms'] == OLD_LAW_TERMS
    assert deal['eco']['val'] == OLD_ECO_VAL
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN

    bad_src = [s for s in deal['src'] if len(s) > 1 and s[1] in BAD_SRC_URLS]
    assert len(bad_src) == 8, f"ожидалось 8 чужих источников, найдено {len(bad_src)}: {bad_src}"

    print(f'{CARD_ID}: снимаю 4 чужих поля (law.struct, law.terms, '
          f'eco.val, eco.target_fin) и {len(bad_src)} чужих источников')

    if write:
        deal['law']['struct'] = '—'
        deal['law']['terms'] = '—'
        deal['eco']['val'] = '—'
        deal['eco']['target_fin'] = '—'
        deal['src'] = [s for s in deal['src']
                        if not (len(s) > 1 and s[1] in BAD_SRC_URLS)]
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
