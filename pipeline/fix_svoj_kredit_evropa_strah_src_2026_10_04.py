# -*- coding: utf-8 -*-
"""Качество, 4 октября 2026 (ежедневный прогон 21:37 МСК) — первоисточник
вместо агрегатора (`split_discovery_sources.py --queue`), карточка
`gmru-svoj-kredit-evropa-strah` («Группа «Свой» купила страховщика
«Кредит Европа лайф» у «Кредит Европа банка»») держала единственным
источником mergers.ru. Саб-агент нашёл первоисточник — Frank Media,
который сам подробно и самостоятельно освещает именно эту сделку (не
просто пересказывает лицензии). Текст не лежит в локальном кэше притока,
а прямой забор (`fetch_article_texts.py`) вернул 0 знаков — frankmedia.ru
не отдаёт контент этой машине (тот же класс сбоя, что раньше у
kommersant.ru/rbc.ru) — поэтому правка не через `review.py`, а точечным
скриптом с `assert`.

Запуск:
    python3 pipeline/fix_svoj_kredit_evropa_strah_src_2026_10_04.py            # сухой прогон
    python3 pipeline/fix_svoj_kredit_evropa_strah_src_2026_10_04.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

NEW_SRC = ['Frank Media', 'https://frankmedia.ru/294898']


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'gmru-svoj-kredit-evropa-strah']
    assert len(target) == 1, target
    card = target[0]
    assert card.get('src') == [['mergers.ru', 'https://mergers.ru/news/Gruppa-Svoj-kupila-strahovschika-u-Kredit-Evropa-banka-87269']], card.get('src')
    assert not card.get('discovery_src'), card.get('discovery_src')

    old_src = card['src']
    card['discovery_src'] = old_src
    card['src'] = [NEW_SRC]

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('src карточки gmru-svoj-kredit-evropa-strah заменён на Frank Media, '
              'mergers.ru переехал в discovery_src. ЗАПИСАНО.')
    else:
        print('Сухой прогон: заменил бы src на Frank Media (mergers.ru -> discovery_src). Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
