# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g39766598 (Арам Габрелянов купил
телеграм-канал Baza): дельта-поиск нашёл разрешение уже
задокументированного в карточке противоречия («войдёт в состав New
Media Holding» по данным РБК vs «не станет частью холдинга» по словам
самого Габрелянова). Оказалось верным и то и другое отчасти: прямой
интеграции в сам холдинг нет, но 20 октября 2025 года, по данным
реестра, АО «Ньюс Медиа» приобрело 34% уставного капитала ООО «4 Кота»
(юрлица Baza) — Габрелянов сохранил 66%. Не через review.py: поле
eco.context уже несёт содержание об исходном противоречии, новый
источник его не продолжает дословно, а разрешает.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://lenizdat.ru/articles/1166534/

Запуск: python3 pipeline/fix_baza_newsmedia_stake_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g39766598'

OLD_CONTEXT = (
    'Источники РБК сообщили, что Baza войдет в состав основанного '
    'медиаменеджером холдинга New Media Holding, включающего Life, '
    'Telegram-каналы Mash и Shot. По их словам, оформление документов уже '
    'на финальной стадии. Сам господин Габрелянов заявил, что Baza не '
    'станет частью холдинга.'
)
CONTEXT_ADDITION = (
    'Противоречие разрешилось лишь отчасти: 20 октября 2025 года, по '
    'данным реестра, АО «Ньюс Медиа» приобрело 34% уставного капитала '
    'ООО «4 Кота» (юрлица Baza) — оставшиеся 66% остались под контролем '
    'Габрелянова. Формально в сам New Media Holding (основан Габреляновым '
    'в 2001 году) канал не интегрирован, но частичный контроль перешёл '
    'аффилированной структуре.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += разрешение противоречия "
          f"(частичная передача 34% «Ньюс Медиа», 20.10.2025)")
    deal['eco']['context'] = NEW_CONTEXT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
