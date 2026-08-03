# -*- coding: utf-8 -*-
"""Черновики карточек по объявлениям фирм из архива @LawFirms — партия на проверку.

ЗАЧЕМ ПАРТИЯМИ. Разбор архива нашёл 65 объявлений о сделках, которых нет в
базе. Заливать их разом нельзя: тормоз `NEW_CARDS_NEED_REVIEW` (прогон E9)
стоит именно потому, что первый прогон классификатора на живом потоке дал
высокий процент ложных срабатываний. Партия из 10 — размер, который человек
реально прочитывает за один присест.

ЧТО ОТБИРАЕТСЯ. Российские сделки с названными сторонами. Международные
новости канала (IPO SpaceX, Prada/Versace, Truth Social, аэропорт Афин)
намеренно пропущены: база — про российский рынок. Пропущены и посты-вопросы
(«Если кто знает, какие юрфирмы сопровождали эту сделку»), где фирма не
названа вовсе, а правило приняло за имя начало фразы.

ЧТО ЗАПОЛНЯЕТСЯ. Только то, что штатный `draft.py` вытаскивает механически
(сумма, тип, статус, стороны, отрасль по профилю компании) плюс консультант
из `advisors.py`. Ничего не сочиняется: пустое поле остаётся пустым, его
заполнит человек или следующая новость.

Запуск:
    python3 pipeline/draft_lawfirms_batch.py            # показать партию
    python3 pipeline/draft_lawfirms_batch.py --write    # сложить в data/inbox/drafts/
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'ingest'))

import advisors     # noqa: E402
import draft        # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
ARCHIVE = os.path.join(ROOT, 'data', 'inbox', 'raw', 'lawfirms_archive.jsonl')
DRAFTS = os.path.join(ROOT, 'data', 'inbox', 'drafts')

# Партия 1: отобраны вручную из 65 по признаку «российская сделка с названными
# сторонами». Номер поста — это и есть идентификатор в канале.
BATCH = [11173, 11001, 10967, 9989, 9772, 9383, 8526, 8295, 7988, 7705]


def main(write=False):
    rows = {}
    for line in open(ARCHIVE, encoding='utf-8'):
        if line.strip():
            row = json.loads(line)
            rows[row['post_id']] = row
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

    missing = [p for p in BATCH if p not in rows]
    assert not missing, 'постов нет в архиве: %s' % missing

    out = []
    for post_id in BATCH:
        row = rows[post_id]
        text = row['text']
        item = {'title': text[:200], 'summary': text[:600],
                'url': row['url'], 'date': row['date'],
                'source_id': 'tg:LawFirms', 'source_name': 'РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ (@LawFirms)',
                'published': row['date']}
        card = draft.build(item, comps)
        found = advisors.lead_advisor(text)
        if found:
            firms, role, sentence = found
            card['adv'] = [[role, f, '%s Источник: %s' % (sentence[:300], row['url'])] for f in firms]
        card['post_text'] = text
        out.append(card)

    for i, card in enumerate(out, 1):
        print('\n%s\n%d. %s' % ('=' * 78, i, card.get('title') or '(без заголовка)'))
        print('   дата: %s   источник: %s' % (card.get('date'), card['src'][0][1]))
        for key, label in (('sum', 'сумма'), ('type', 'тип'), ('status', 'статус'),
                           ('buyer', 'покупатель'), ('asset', 'предмет'), ('seller', 'продавец'),
                           ('ind', 'отрасль')):
            if card.get(key):
                print('   %-11s %s' % (label + ':', card[key]))
        for role, firm, _ in card.get('adv', []):
            print('   %-11s %s — %s' % ('консультант:', firm, role))

    if write:
        os.makedirs(DRAFTS, exist_ok=True)
        path = os.path.join(DRAFTS, 'lawfirms_batch1.json')
        json.dump(out, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('\nЧерновики сложены в %s (в базу НЕ записаны)' % path)
    else:
        print('\n\nПоказ без записи. Сложить черновики — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
