# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `cfeca52ce`
(«Детский мир завершил реорганизацию с выделением дочерней компании
ООО ДМ и запуском программы выкупа акций», 30 мая 2023) описывала
только ЗАПУСК программы выкупа; чем она завершилась и что стало с
публичным статусом компании — было неизвестно.

Личный WebFetch подтвердил дословно:

1) Ведомости, 17 октября 2023,
   https://www.vedomosti.ru/investments/news/2023/10/17/1001010-detskii-mir:
   «Компания приобрела 58,26% акций, принадлежащих нерезидентам» (первый
   байбэк, завершён 20 сентября); «Компания приобрела 2,04 млн бумаг за
   145,7 млн руб.» (второй байбэк, по 71,5 ₽ за акцию).

2) РеалноеВремя, 15 февраля 2024,
   https://realnoevremya.ru/news/302982-pao-detskiy-mir-likvidiruyut:
   «Акционеры «Детского мира» приняли решение о ликвидации ПАО»; «Все
   акции ликвидированного ПАО «Детский мир» будут погашены».

Бизнес продолжает работать как частное ООО «ДМ» — публичная компания
ликвидирована, но не сама сеть. Точная дата прекращения торгов на
бирже источниками не подтверждена дословно — не вносится.

Запуск:
    python3 pipeline/fix_detsky_mir_buyback_completion_and_liquidation.py            # сухой прогон
    python3 pipeline/fix_detsky_mir_buyback_completion_and_liquidation.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_ECO_FIN = (
    'Первый байбэк завершён 20 сентября 2023 года — выкуплено 58,26% '
    'акций, принадлежавших нерезидентам. Позже компания выкупила ещё '
    '2,04 млн бумаг за 145,7 млн ₽ по 71,5 ₽ за акцию. 15 февраля '
    '2024 года акционеры приняли решение о ликвидации ПАО «Детский '
    'мир» — все акции будут погашены, бизнес продолжает работать как '
    'частное ООО «ДМ».'
)

NEW_SRC = [
    ['Ведомости', 'https://www.vedomosti.ru/investments/news/2023/10/17/1001010-detskii-mir'],
    ['РеалноеВремя', 'https://realnoevremya.ru/news/302982-pao-detskiy-mir-likvidiruyut'],
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['cfeca52ce']

    assert d['eco'].get('fin') in (None, '—'), 'eco.fin уже занят: %r' % (d['eco'].get('fin'),)
    urls = {s[1] for s in d['src']}
    for src in NEW_SRC:
        assert src[1] not in urls, 'источник уже добавлен: %s' % src[1]

    print('cfeca52ce: eco.fin заполнен (завершение байбэка, ликвидация '
          'ПАО); добавлены два источника')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['fin'] = NEW_ECO_FIN
    d['src'].extend(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
