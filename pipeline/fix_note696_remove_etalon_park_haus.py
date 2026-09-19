# -*- coding: utf-8 -*-
"""Приток 19.09.2026, часовой прогон 10:20 МСК — ответ на заметку владельца
№696: «Удаляй карту просто». Прямая выписка ЕГРЮЛ (уже в самой карточке)
показывает, что единственный владелец участка — «Специализированный
застройщик «Семья-7»» краснодарской группы «СК Семья», связи ни с
«Эталоном», ни с «Рамо-М» не найдено. Карточка не описывает подтверждённую
сделку ни одной из заявленных сторон — удаляем целиком, без замены.
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals']
    target = [d for d in deals if d['id'] == 'g8ce554c5']
    assert len(target) == 1, target
    assert target[0]['title'] == (
        'Девелопер «Эталон» покупает участок земли у «Рамо-М» рядом с ТЦ '
        '«Парк хаус» в Санкт-Петербурге'
    )

    tp = data.get('telegram_posts', {})
    assert tp.get('g8ce554c5') is None

    data['deals'] = [d for d in deals if d['id'] != 'g8ce554c5']

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('g8ce554c5 удалена. ЗАПИСАНО.')
    else:
        print('Сухой прогон. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
