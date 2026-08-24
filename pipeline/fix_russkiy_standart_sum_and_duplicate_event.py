# -*- coding: utf-8 -*-
"""«Русский Стандарт водка»/офисно-складской комплекс (`gb9a22f5f`):
почасовой приток 24 августа переопубликовал ту же новость (dp.ru), и
`enrich.py` механически дописал два поля из того же источника, который
уже целиком лежит в карточке:

1. `sum: "2 млрд ₽"` — но это НАЧАЛЬНАЯ ЦЕНА торгов, назначенных на 28
   сентября (статус карточки «Обсуждается», сделка ещё не состоялась), а
   не цена закрытой сделки. Уже правильно классифицировано как оценка
   старта аукциона в `eco.val`, а не как факт сделки — верхнеуровневое
   `sum` вводит читателя в заблуждение (тот же класс урока, что уже
   записан: «Число может быть верным фактом и совсем не той величиной»).
2. Продублированное событие `kind:"negotiations"` с тем же URL, что и
   `src[0]`, и с `note`, обрубленным на середине предложения («…Автор
   фото: РАД 11:21 24 августа 2026 11:21 90 просмотров Читайте нас в
   мессенджере Max Читайте нас в…») — тот же факт уже полностью и честно
   изложен в `eco.context`/`eco.val`; отдельная строка «Хода сделки» с
   обрубленным текстом ничего не добавляет и хуже читается.

Запуск: python3 pipeline/fix_russkiy_standart_sum_and_duplicate_event.py           # проверка
        python3 pipeline/fix_russkiy_standart_sum_and_duplicate_event.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gb9a22f5f'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card.get('sum') == '2 млрд ₽', (
        'sum уже другое: %r' % card.get('sum'))
    assert len(card.get('events') or []) == 1, (
        'events уже другое: %r' % card.get('events'))
    ev = card['events'][0]
    assert ev.get('kind') == 'negotiations', 'событие уже другое'
    assert ev.get('source', [None, None])[1] == card['src'][0][1], (
        'источник события не совпадает с src[0]')

    print('ДО: sum=%r, events=%r' % (card.get('sum'), card.get('events')))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    del card['sum']
    card['events'] = []
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
