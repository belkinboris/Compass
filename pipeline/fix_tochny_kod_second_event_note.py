# -*- coding: utf-8 -*-
"""Карточка `g1536c7fc» (Райффайзенбанк/«Точный код») — второй этап
«Сделка завершена», добавленный `enrich.py` 14 сентября 2026 по статье
TAdviser, скопировал служебный текст структурированной карточки TAdviser
(«История 2026: ...», «Программное обеспечение для финансы»,
«1,5 млн Российский рубль» — обрывки категорий вперемешку с прозой), а
не связное предложение. Первый этап (9 сентября, Frank Media) уже несёт
основной факт сделки, поэтому второй этап не удаляется (иначе `enrich.py`
предложит его снова на следующем часе — известная защита `known_event_urls`
держится только пока сама запись остаётся в `events[]`), а переписывается
человеческим текстом с двумя genuinely новыми фактами статьи: официальное
подтверждение банка Forbes и уставный капитал новой компании.

Источник: https://www.tadviser.ru/a/966210 (кэш `data/inbox/raw/2026-09-14.jsonl`)

Запуск: python3 pipeline/fix_tochny_kod_second_event_note.py --write
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

OLD_NOTE = (
    'История 2026: Российский Райффайзенбанк купил 49% «Точный код» '
    'Райффайзенбанк стал одним из соучредителей компании «Точный код», '
    'разрабатывающей Программное обеспечение для финансы. Доля банка '
    'составила 49%. Информацию о сделке Forbes подтвердили в…'
)

NEW_NOTE = (
    'Информацию о сделке Forbes подтвердили в пресс-службе Райффайзенбанка '
    '11 сентября 2026 года. Уставный капитал «Точного кода» — 1,5 млн ₽.'
)


def main():
    write = '--write' in sys.argv
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    found = False
    for c in data['deals']:
        if c.get('id') != 'g1536c7fc':
            continue
        for ev in c.get('events', []):
            if ev.get('note') == OLD_NOTE:
                found = True
                if write:
                    ev['note'] = NEW_NOTE
    assert found, 'исходный текст события не найден — карточка уже изменилась'
    print('Найдено и обновлено' if found else 'не найдено')
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main()
