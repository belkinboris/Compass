# -*- coding: utf-8 -*-
"""Приток 27 ноября 2026: карточке gmru-nspk-privatization (продажа миноритарного
пакета НСПК) дописан этап переговоров — первый зампред ВТБ Дмитрий Пьянов сказал,
что банк, вероятно, согласится на основные условия ЦБ (Интерфакс, 27.11.2026).
Источник добавлен партией fixes/intake_2026_11_27_cian_official.py (поле src).

Запуск: python3 pipeline/add_nspk_vtb_event_2026_11_27.py [--write]
"""
import json
import os
import sys

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'static', 'data', 'deals_promoted.json')
ID = 'gmru-nspk-privatization'
URL = 'https://www.interfax.ru/business/1131768'
EVENT = {
    'kind': 'negotiations',
    'date': '2026-11-27',
    'title': 'ВТБ готов принять условия ЦБ',
    'note': '«Мы не можем разглашать шаги, которые предпринимает регулятор по этому вопросу. '
            'Полагаю, что мы согласимся на основные условия регулятора», — сказал Пьянов 27 ноября.',
    'source': ['Интерфакс', URL],
}


def main(write):
    data = json.load(open(BASE, encoding='utf-8'))   # перечитываем прямо перед записью
    card = next(d for d in data['deals'] if d['id'] == ID)
    events = card.setdefault('events', [])
    if any(e.get('date') == EVENT['date'] and e.get('title') == EVENT['title'] for e in events):
        print('Уже записано.')
        return
    assert events and events[-1]['date'] == '2026-09-24', events[-1:]
    assert card['status'] == 'Обсуждается', card['status']
    events.append(EVENT)
    if write:
        with open(BASE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
