# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `c09e39da9`
(«Александр Светаков выставил ООО «Абсолют Страхование» на продажу»,
26 июня 2024) — исход уже известен базе и полностью описан в другой,
более поздней карточке (`absolut-strah`, 26 июня 2026, «ЦАНЦ»
приобрело 100% «Абсолют Страхование» за ≈10 млрд ₽) — своя же
`eco.context` карточки `absolut-strah` прямо ссылается на это же
объявление о продаже: «Актив выставили на продажу ещё в июне 2024
года; среди претендентов называли Совкомбанк, «Югорию» и группу МТС».

Это ровно тот класс, что уже применялся к Danone/«Балтике» в этой же
сессии (10 сентября): не пересказывать заново детали уже полностью
описанной сделки, а добавить короткую фразу-мост к её исходу.

Запуск:
    python3 pipeline/fix_absolut_strah_svetakov_sold_crossref.py            # сухой прогон
    python3 pipeline/fix_absolut_strah_svetakov_sold_crossref.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_CONTEXT = 'Страховая компания занимает 28-е место по объёму премий на рынке.'
NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' Продажа состоялась через два года: в июне 2026 года 100% «Абсолют '
    'Страхование» купило ОАО «ЦАНЦ» за ≈10 млрд ₽, компания сохранила '
    'название, офисы и команду.'
)


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['c09e39da9']

    assert d['eco']['context'] == OLD_ECO_CONTEXT, \
        'c09e39da9 eco.context уже другой: %r' % (d['eco']['context'],)

    print('c09e39da9: eco.context дополнен кросс-ссылкой на исход продажи '
          '(ЦАНЦ, июнь 2026, ≈10 млрд ₽) — детали не пересказаны, они уже '
          'полностью в absolut-strah')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['context'] = NEW_ECO_CONTEXT

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
