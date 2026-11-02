# -*- coding: utf-8 -*-
"""Приток 10:20 МСК — `enrich.py` (сухой прогон) предложил карточке
gc6fa5d80 (Главпочтамт на Мясницкой) статус «Закрыта» по статье
Retailer.ru. Аукцион еще не состоялся (назначен на 9 декабря 2026) —
статью прочитали целиком: она описывает ТОТ ЖЕ, еще не прошедший аукцион,
а «продала» в тексте относится к фоновой справке о ДРУГОМ, уже проданном
активе («В январе 2026 года «Почта России» продала здание Главного
почтамта в Санкт-Петербурге»). `draft.guess_status()` ищет слова статуса
по всему тексту статьи, не различая предмет — known_issues/intake.md,
«Прецедент в контексте карточки поднимает статус на «Закрыта»».

Без записи в `retracted` то же предложение вернулось бы на следующем
прогоне `enrich.py` по тому же кэшу (enrich.py.is_retracted()).

Запуск: python3 pipeline/archive/2026-11/fix_gc6fa5d80_status_retracted_2026_11_02.py --write
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'
WRONG_STATUS = 'Закрыта'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    target = [d for d in data['deals'] if d.get('id') == 'gc6fa5d80']
    assert len(target) == 1, target
    card = target[0]
    assert card.get('status') == 'Обсуждается', repr(card.get('status'))
    card.setdefault('retracted', {}).setdefault('status', [])
    if WRONG_STATUS not in card['retracted']['status']:
        card['retracted']['status'].append(WRONG_STATUS)

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('gc6fa5d80: «%s» записано в retracted.status. ЗАПИСАНО.' % WRONG_STATUS)
    else:
        print('Сухой прогон: записал бы «%s» в retracted.status. Повторите с --write.' % WRONG_STATUS)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
