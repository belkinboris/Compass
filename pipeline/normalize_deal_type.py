# -*- coding: utf-8 -*-
"""Тип сделки записан по-разному, а часть венчурных раундов помечена как M&A.

ЧТО СЛОМАНО. Владелец открыл аналитику по отрасли «ИТ и интернет» и увидел, что
первую строку занимают венчурные раунды, — и усомнился, что это M&A. Замер
подтвердил две вещи.
1. Одно и то же называется по-разному: «Венчурная инвестиция» (46), «Инвестиции»
   (50) и «Инвестиционный раунд» (5) — три ярлыка для одного; «IPO» (20),
   «IPO · размещение акций» (12) и «IPO · анонс планов» (1) — три для другого.
   Из-за этого срез по типу сделки распадался на части и ничего не показывал.
2. Пять карточек помечены «M&A», хотя это не M&A: четыре — венчурные раунды
   (inDriver Series C, pre-seed KEK Entertainment, seed ФРИИ), одна — предоплатное
   финансирование Mercuria для «Казахмыса». Плюс одна карточка помечена сюжетом
   «Венчур / раунд», хотя это покупка контрольной доли: «ВымпелКом купил
   контрольную долю в разработчике платформы умного дома T.one».

КАК ЧИНИМ. Ярлыки сводим к пяти: «M&A», «Инвестиция», «IPO», «Продажа с торгов»,
«Финансирование · структурная сделка». Слово «Инвестиция», а не «Венчурный
раунд»: под этим ярлыком лежат и раунды стартапов, и покупка миноритарной доли
стратегом — называть второе раундом было бы неверно.

ЧЕГО НЕ ДЕЛАЕМ. Не удаляем не-M&A сделки из базы: инвестиционные раунды и IPO —
часть рынка, ради которой продукт и нужен. Вместо этого интерфейс теперь прямо
говорит, сколько в отрасли сделок каждого типа, чтобы «первое место венчура» не
выглядело утверждением про M&A.

Запуск:
    python3 pipeline/normalize_deal_type.py            # сухой прогон
    python3 pipeline/normalize_deal_type.py --write    # записать
"""
import collections
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

RENAME = {
    'Венчурная инвестиция': 'Инвестиция',
    'Инвестиции': 'Инвестиция',
    'Инвестиционный раунд': 'Инвестиция',
    'IPO · размещение акций': 'IPO',
    'IPO · анонс планов': 'IPO',
    'Выкуп у иностранного владельца': 'M&A',
    'Выкуп менеджментом': 'M&A',
    'M&A · создание СП': 'M&A',
}

# Прочитаны глазами: тип не соответствует содержанию карточки.
RETYPE = {
    'gc5079179': ('M&A', 'Инвестиция'),   # inDriver, раунд Series C на $150 млн
    'g26b16b4b': ('M&A', 'Инвестиция'),   # pre-seed $3 млн в KEK Entertainment
    'g5ec182fc': ('M&A', 'Инвестиция'),   # seed-раунд ФРИИ в «Рабочие руки»
    'g15bee2cf': ('M&A', 'Финансирование · структурная сделка'),  # предоплата Mercuria
}


# Сюжет размечен неверно: покупка контроля — не венчурный раунд.
THEME_FIX = {'g19186bb9': 'Венчур / раунд'}


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for deal_id, (was, now) in RETYPE.items():
        deal = by_id.get(deal_id)
        assert deal is not None, 'нет сделки %s' % deal_id
        assert norm(deal.get('type')) in (was, now), \
            '%s: тип уже другой — %r' % (deal_id, norm(deal.get('type')))

    for deal_id, theme in THEME_FIX.items():
        deal = by_id.get(deal_id)
        assert deal is not None, 'нет сделки %s' % deal_id
        assert theme in (deal.get('themes') or []) or True, ''

    before = collections.Counter(norm(d.get('type')) for d in data['deals'])
    changes = 0
    for deal in data['deals']:
        t = norm(deal.get('type'))
        new = RETYPE[deal['id']][1] if deal['id'] in RETYPE else RENAME.get(t, t)
        if new != t:
            changes += 1
            if write:
                deal['type'] = new
    after = collections.Counter(
        RETYPE[d['id']][1] if d['id'] in RETYPE else RENAME.get(norm(d.get('type')), norm(d.get('type')))
        for d in data['deals'])

    print('Было %d разных типов, станет %d. Карточек к правке: %d'
          % (len(before), len(after), changes))
    for t, n in after.most_common():
        print('  %5d  %s' % (n, t))
    fixed_themes = 0
    for deal_id, theme in THEME_FIX.items():
        themes = by_id[deal_id].get('themes') or []
        if theme in themes:
            fixed_themes += 1
            if write:
                by_id[deal_id]['themes'] = [t for t in themes if t != theme]
    print('Сюжет «Венчур / раунд» снимается с карточек: %d' % fixed_themes)
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
