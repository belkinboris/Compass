# -*- coding: utf-8 -*-
"""Карточка g7c192c64 «Тодд Бёли продал свою долю в «Челси»» прошла ворота
притока 18.09.2026 ошибочно: russian_evidence() приняла упоминание Романа
Абрамовича как признак российского рынка, но источник (Коммерсантъ) называет
его лишь ИСТОРИЧЕСКИМ контекстом — Абрамович продал «Челси» консорциуму
Тодда Бёли ещё в 2022 году и стороной ЭТОЙ сделки (Бёли/Марк Уолтер продают
долю Clearlake Capital Group) не является. Ни продавцы, ни покупатель, ни
сам клуб к российскому рынку отношения не имеют — честный «нероссийский
контур без российского элемента», который мы не публикуем (CLAUDE.md).

Карточка ещё не отправлена в консоль (send_drafts не запускался после
promote.py) — снимаем из pending.json, а не через модерацию.

Запуск: python3 pipeline/fix_remove_chelsea_no_russian_nexus.py [--write]
"""
import json
import sys

PENDING_PATH = 'static/data/pending.json'


def main(write):
    data = json.load(open(PENDING_PATH, encoding='utf-8'))
    cards = data['cards']
    before = len(cards)
    target = [c for c in cards if c['id'] == 'g7c192c64']
    assert len(target) == 1, target
    assert target[0]['title'] == 'Тодд Бёли продал свою долю в «Челси»'
    assert not target[0].get('draft_sent'), 'карточка уже отправлена в консоль — снимать нельзя этим скриптом'
    data['cards'] = [c for c in cards if c['id'] != 'g7c192c64']
    assert len(data['cards']) == before - 1

    if write:
        json.dump(data, open(PENDING_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Снято: g7c192c64. ЗАПИСАНО.')
    else:
        print('Сухой прогон: снял бы g7c192c64. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
