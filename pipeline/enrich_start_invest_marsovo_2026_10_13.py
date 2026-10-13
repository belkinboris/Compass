# -*- coding: utf-8 -*-
"""Карточка `g3504df38` («Структура «Газпрома» продала проект отеля на
Марсовом поле», закрыта 28 сентября 2026) — слабый матчер `enrich.py` не
связал её с переопубликованной TAdviser-статьёй о той же сделке
(«"Старт Инвест" купил люксовый отель на Марсовом поле... Сделку оценили
в 3 млрд рублей», общих слов заголовка — всего 3): тот же класс дефекта,
что у Azimut/Ярославля (13 октября 2026, первая половина дня) и
Alfa-банк/«Медси» (тот же день, позже).

TAdviser (пересказ со ссылкой на «Коммерсантъ», интервью Виктории
Соболевской) добавляет факт, которого в карточке не было: «Старт Инвест»
купил не абстрактную «долю», а именно 100% ООО «Лотос Отели». И даёт
ВТОРУЮ, отличающуюся оценку цены той же сделки — 2,5–3 млрд ₽, тогда как
источник карточки («Деловой Петербург») называет 5–6 млрд ₽. Обе оценки —
от неназванных экспертов по одной и той же сделке перехода прав на
«Лотос отели»; записаны обе версии с атрибуцией, слияния в одну цифру нет
(принцип «честность данных выше полноты», CLAUDE.md).

Источник: TAdviser (пересказ «Коммерсантъ») https://www.tadviser.ru/a/790758

Запуск:
    python3 enrich_start_invest_marsovo_2026_10_13.py            # сухой прогон
    python3 enrich_start_invest_marsovo_2026_10_13.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
CARD_ID = 'g3504df38'
TADVISER = ['TAdviser', 'https://www.tadviser.ru/a/790758']

OLD_SHARE = '—'
NEW_SHARE = ('«Лотос Отели» — проектная компания под земельный участок 1,4 га на '
             'Марсовом поле; весь её капитал, 100% долей, теперь принадлежит '
             '«Старт Инвест».')

OLD_VAL = '—'
NEW_VAL = ('Источники по-разному оценивают стоимость перехода прав на «Лотос отели»: '
           '«Деловой Петербург» со ссылкой на экспертов, знакомых с проектом, называет '
           'порядка 5–6 млрд ₽; TAdviser со ссылкой на экспертов — 2,5–3 млрд ₽. '
           'Официально сумма сделки не раскрывалась.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    card = by_id[CARD_ID]

    assert card['eco']['share'] == OLD_SHARE
    assert card['eco']['val'] == OLD_VAL
    assert card['status'] == 'Закрыта'

    print('ПРАВКА %s: eco.share, eco.val, +источник TAdviser' % CARD_ID)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    card['eco']['share'] = NEW_SHARE
    card['eco']['val'] = NEW_VAL
    existing_urls = {s[1] for s in card.get('src', []) if len(s) > 1}
    if TADVISER[1] not in existing_urls:
        card.setdefault('src', []).append(list(TADVISER))

    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_by_id = {d['id']: d for d in fresh['deals']}
    fresh_card = fresh_by_id[CARD_ID]
    assert fresh_card['eco']['share'] == OLD_SHARE, 'карточку кто-то уже поправил — перечитайте'
    idx = fresh['deals'].index(fresh_card)
    fresh['deals'][idx] = card
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
