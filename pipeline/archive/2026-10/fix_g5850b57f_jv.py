"""Яндекс/VK (g5850b57f): совместное предприятие, а не покупка.

Владелец 8 октября 2026: «это же СП, а не M&A… почему Яндекс покупатель,
если они могут с VK равноправно зайти?». По правилу docs/card_status_dates.md
(«Создание СП — тип „Создание СП“», обе стороны — участники) карточка
собрана неверно: тип «M&A», вторым участником стоял VK Tech — бизнес, который
VK вносит, а не сторона. Источники (CNews, Хабр, mergers.ru) называют
стороны «Яндекс» и VK.

Правит карточку там, где она сейчас лежит (pending.json или база), и, пока
карточка в предпросмотре, снимает отметку об отправленном проекте поста —
следующая отправка покажет владельцу пост с участниками.

Без ключа — сухой прогон; запись — --write.
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FILES = [os.path.join(ROOT, 'static/data/pending.json'),
         os.path.join(ROOT, 'static/data/deals_promoted.json')]
DEAL = 'g5850b57f'
VK, VK_TECH = 'g4e694234', 'g592a5a2b'


def fix(card, in_pending):
    # Повторный запуск 8 октября 2026 (16:40 UTC): рутина публикации перенесла
    # карточку в базу из старого снимка pending.json, и первая правка
    # потерялась при слиянии — поэтому assert на старое значение мягкий:
    # уже исправленное не трогаем.
    assert card.get('buyer') == 'yandex', card.get('buyer')
    assert card.get('type') in ('M&A', 'Создание СП'), card.get('type')
    assert card.get('target') in (VK_TECH, VK), card.get('target')
    card['type'] = 'Создание СП'
    card['target'] = VK
    for ev in (card.get('party_evidence') or {}).get('target') or []:
        if ev.get('value') == 'VK Tech':
            ev['value'] = 'VK'
    if in_pending:
        card['post_draft_sent'] = False
        card.pop('post_preview', None)
    else:
        # Владелец: «пост пока нажму не отправлять». Карточка уже в базе, а
        # нажатие под проектом поста до базы не доходит — ставим решение
        # прямо: канал молчит, карточка засевается бэклогом.
        card['no_post'] = True


def main(write):
    for path in FILES:
        data = json.load(open(path, encoding='utf-8'))      # свежий снимок прямо перед записью
        cards = data.get('cards') if 'cards' in data else data.get('deals')
        hit = [c for c in cards if c.get('id') == DEAL]
        if not hit:
            continue
        fix(hit[0], 'cards' in data)
        print('%s: %s → тип «Создание СП», участники yandex + %s'
              % (os.path.basename(path), DEAL, VK))
        if write:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
        else:
            print('Сухой прогон. Запись — с ключом --write.')
        return 0
    print('карточка %s не найдена' % DEAL)
    return 1


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
