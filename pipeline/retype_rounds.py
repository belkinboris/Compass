# -*- coding: utf-8 -*-
"""Раунды и IPO, помеченные как M&A (продолжение замечания владельца).

ЧТО СЛОМАНО. В прогоне 35 тип сделки свели к пяти ярлыкам и исправили три
карточки, где венчурный раунд был помечен «M&A». Их искали через тему
«Венчур / раунд» — и поэтому нашли не всех: у карточки «Блоксели» темы нет
вовсе, а в заголовке прямо написано «привлекла 12,5 млн рублей от Synergy
Ventures и brainbox_I». Владелец эту карточку и открыл.

ЗАМЕР (прогон 36). Ищем по заголовку: признак раунда («привлекла N млн от…»,
«раунд», «Series A», «seed», «pre-IPO», «инвестировала N в…») и при этом нет
признака покупки («купил», «приобрёл», «выкупил», «продал»). Среди карточек с
типом «M&A» таких **13**, все прочитаны: 11 — инвестиционные раунды, 2 — IPO.

ПРО ЗАМЕР ОТДЕЛЬНО. Первый вариант правила нашёл 8 карточек вместо 13: в
шаблоне стояло `привлек\\w*\\s+[^,]{0,40}(?:млн|…)`, а в «привлекла 12,5 млн»
внутри числа стоит запятая — и класс `[^,]` обрывал совпадение. Ровно та
карточка, с которой начался разговор, в выборку не попала. Правило поправлено
на `[^.;]`, замер пересчитан.

ОБРАТНОЕ НАПРАВЛЕНИЕ ПРОВЕРЕНО И ЧИСТО. Карточек с типом «Инвестиция», чей
заголовок описывает покупку, — 12, но все они про миноритарные доли («Ростелеком
приобрел 5%», «фонд ТилТех купил 25%»). Это вложение в капитал, а не смена
контроля: ярлык «Инвестиция» у них верный, трогать не нужно.

Запуск:
    python3 pipeline/retype_rounds.py            # сухой прогон
    python3 pipeline/retype_rounds.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

# id -> новый тип. Прочитан заголовок и текст каждой карточки.
TABLE = {
    'g14356b25': 'Инвестиция',   # СТГ (CarMoney): 225–229 млн ₽ в капитал по закрытой подписке
    'g28d62a47': 'Инвестиция',   # Allright.io: $1,5 млн от Buran Venture Capital
    'g5900b49f': 'Инвестиция',   # Novakid: $1,5 млн посевных от LETA Capital и BonAngels
    'ge93aefc3': 'Инвестиция',   # «Блоксели»: 12,5 млн ₽ от Synergy Ventures и brainbox_I
    'gc8157b0b': 'Инвестиция',   # B2B-Export: $4 млн за 5% доли
    'g676504a3': 'Инвестиция',   # KAMA FLOW: 500 млн ₽ в ROBO
    'g2be4d6a0': 'Инвестиция',   # Amlab.me: 27,5 млн ₽ от ФРИИ и бизнес-ангела
    'g6322e160': 'Инвестиция',   # «ТилТех Капитал»: 6 млн ₽ в сервис подбора медуслуг
    'g8aeb631a': 'Инвестиция',   # Mo Meditation: $1 млн от Дмитрия Гришина и ангелов
    'g5ff3f9ee': 'Инвестиция',   # VEB Ventures: 500 млн ₽ в Deliver
    'g4882cbbe': 'Инвестиция',   # МИР: $820 тыс. от Atlas Ventures, ФРИИ и ангелов
    'g2a3a597b': 'IPO',          # Pre-IPO ГК «Марэкс»
    'g465977ce': 'IPO',          # МТС Банк: IPO на ₽11,5 млрд
}

ALLOWED = {'M&A', 'Инвестиция', 'IPO', 'Продажа с торгов', 'Финансирование · структурная сделка'}
ROUND = re.compile(
    r'привлек[а-яё]*\s+[^.;]{0,45}?(?:млн|млрд|тыс|\$|₽)|раунд|series\s+[a-e]\b|seed|посевн|'
    r'pre-?ipo|\bipo\b|венчурн|вложил[аи]?\s+\$?\d|проинвестир|инвестир[а-яё]*\s+\d', re.I)
BUY = re.compile(r'куп[ии]л|приобрел|приобрёл|выкуп|продал|продаж|слияни|консолидир|поглощ', re.I)


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    plan, done = [], []
    for deal_id, new_type in TABLE.items():
        deal = by_id.get(deal_id)
        assert deal is not None, 'нет сделки %s' % deal_id
        assert new_type in ALLOWED, '%s: ярлык %r вне списка' % (deal_id, new_type)
        current = norm(deal.get('type'))
        if current == new_type:
            done.append(deal_id)
            continue
        assert current == 'M&A', '%s: ожидали «M&A», а стоит %r' % (deal_id, current)
        title = norm(deal['title'])
        # Признак раунда обязан быть в заголовке, признака покупки быть не должно:
        # так правка не может втихую переклеить ярлык обычной сделке M&A.
        assert ROUND.search(title), '%s: в заголовке нет признака раунда' % deal_id
        assert not BUY.search(title), '%s: в заголовке есть признак покупки' % deal_id
        plan.append((deal_id, current, new_type, title, deal))

    assert len(plan) + len(done) == len(TABLE), 'часть карточек изменилась вне скрипта'
    if not plan:
        print('Уже применено: у всех %d карточек тип исправлен.' % len(TABLE))
        return

    print('Карточек к правке: %d (уже применено: %d)' % (len(plan), len(done)))
    for deal_id, cur, new, title, _ in plan:
        print('  %s  %s -> %s\n     %s' % (deal_id, cur, new, title[:95]))
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return
    for deal_id, _, new, _, deal in plan:
        deal['type'] = new
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано: %d карточек.' % len(plan))


if __name__ == '__main__':
    main('--write' in sys.argv)
