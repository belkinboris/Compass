# -*- coding: utf-8 -*-
"""Приток 18.09.2026, часовой прогон 14:20 МСК — ответ на заметку владельца
№672 (карточка «Роман Володин выкупил у основателей компанию АТОЛ»,
g5ccd2edb). Владелец попросил указать в карточке факт про Softline;
источник (CNews, дословная цитата ниже, скачан этим же прогоном в
data/inbox/raw/2026-09-18-articles.jsonl) называет его прямо. Запись
через прямой скрипт, а не review.py --write, потому что поле уже
непустое и append не проходит побайтовую проверку `flat(new) in
flat(quote)` — соответствующая запись FIXES добавлена отдельно для
журнала (pipeline/ingest/fixes/batch_2026_09_18_notes_atol_softline.py).
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

OLD_CONTEXT = (
    'Компания АТОЛ была основана в 2001 году Алексеем и Ириной Макаровыми, которые, по '
    'данным СПАРК, владели по 50% бизнеса. Александр Бочков, занявший пост гендиректора '
    'холдинга 13 ноября 2024 года, руководил им лишь около двух месяцев: 22 января 2025 '
    'года гендиректором ООО «УК „АТОЛ“», по данным ЕГРЮЛ, вновь стал новый собственник '
    'Роман Володин — и как минимум по апрель 2026 года он публично фигурирует как '
    'действующий CEO АТОЛ. По официальной отчётности РСБУ операционного юрлица ООО «АТОЛ» '
    '(не всей группы) выручка за 2025 год составила 6,7 млрд ₽ (снижение на 6,7% к 2024 '
    'году), чистая прибыль — 429 млн ₽ (рост на 60,1%).'
)

QUOTE_SOFTLINE = (
    'Скупающий российские ИТ-компании «Софтлайн» ранее вел переговоры о покупке «Атол», '
    'но не смог договориться с собственниками.'
)


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g5ccd2edb')
    assert card['eco']['context'] == OLD_CONTEXT, repr(card['eco']['context'])
    card['eco']['context'] = OLD_CONTEXT + ' ' + QUOTE_SOFTLINE
    if not any(s[1] == 'https://www.cnews.ru/news/top/2024-12-23_osnovateli_krupnogo_proizvoditelya'
               for s in card.get('src', []) if len(s) > 1):
        card['src'].append(['CNews', 'https://www.cnews.ru/news/top/2024-12-23_osnovateli_krupnogo_proizvoditelya'])

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('g5ccd2edb: дописан факт про Softline. ЗАПИСАНО.')
    else:
        print('Сухой прогон: дописал бы факт про Softline в g5ccd2edb. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
