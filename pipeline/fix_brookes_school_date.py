# -*- coding: utf-8 -*-
"""Дата карточки не совпадает с датой её собственного источника.

`gb7a906e5` («Группа «Пионер» продала здание школы Brookes School Moscow
Игорю Рыбакову») стоит с датой 2024-01-01 — это заглушка «известен только
год» (таких карточек 339, дата всегда 1 января). У карточки один источник,
и это не фоновая ссылка, а прямой репортаж о самой сделке — Ведомости,
27 января 2023: адрес статьи «ribakov-pokupaet-odnu-iz-chastnih-shkol»
(«Рыбаков покупает одну из частных школ») слово в слово совпадает с
предметом карточки. Дата в дате публикации самого источника надёжнее
заглушки — переносим её.

НЕ РАСПРОСТРАНЯЕМ ПРАВИЛО. Тем же способом (URL источника содержит дату,
отличную от даты карточки с заглушкой «год известен, день — 1 января»)
нашлось ещё 23 карточки, но для них дата в URL не обязательно дата
конкретно ЭТОЙ сделки — источник может быть фоновой ссылкой на архивную
статью или другую публикацию того же СМИ (например, у `g2544a5cb` в
источнике стоит статья 2014 года при карточке 2024 года — явно фоновая, не
объявление сделки). Каждую из 23 нужно читать отдельно, это не сделано —
см. `PRODUCT_ROADMAP.md`.

Запуск:
    python3 pipeline/fix_brookes_school_date.py            # сухой прогон
    python3 pipeline/fix_brookes_school_date.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DID = 'gb7a906e5'
OLD_DATE, NEW_DATE = '2024-01-01', '2023-01-27'
SRC_URL = 'https://www.vedomosti.ru/society/articles/2023/01/27/960635-ribakov-pokupaet-odnu-iz-chastnih-shkol'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}
    d = by_id[DID]

    assert d.get('date') == OLD_DATE, f'дата уже не {OLD_DATE!r}: {d.get("date")!r}'
    urls = {s[1] for s in (d.get('src') or []) if len(s) > 1}
    assert SRC_URL in urls, 'ожидаемый источник не найден в карточке'

    print(f'{DID} [date]: {OLD_DATE!r} -> {NEW_DATE!r} (по дате публикации источника)')
    if write:
        d['date'] = NEW_DATE
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
