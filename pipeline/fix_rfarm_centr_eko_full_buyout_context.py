# -*- coding: utf-8 -*-
"""Месячная очередь, 9 сентября 2026 — дочитывание карточки `gf090d86e`
(«"Р-Фарм" приобрела 49,9% в группе "Центр ЭКО"», добавлена в базу
3 августа 2026, полностью обыскана в тот же день).

Дельта-поиск (саб-агент + личная проверка) нашёл продолжение сюжета:
29 мая 2026 года структура «Р-Фарм» (АО «Эко холдинг») выкупила у
Сергея Лебедева ОСТАВШИЕСЯ 50,1% акций и стала 100%-м владельцем «Центр
ЭКО». Личный WebFetch (vedomosti.ru, 3 июня 2026) подтвердил дословно:
«Структура ГК «Р-фарм» – АО «Эко холдинг» – выкупила у Сергея Лебедева
оставшиеся 50,1% акций в группе «Центр ЭКО»»; «сделка была закрыта 29
мая»; «её сумму стороны не раскрывают».

Это отдельное, более позднее событие с ДРУГОЙ долей (50,1% против 49,9%
в этой карточке) — не дополнение к структурным полям данной сделки
(`buyer`/`seller`/`sum` этой карточки по-прежнему верно описывают именно
декабрьскую 2024 года покупку 49,9%), а кандидат на отдельную карточку.
Факт о завершении полного выкупа добавлен только в `eco.context` этой
карточки как честная ссылка на дальнейшую судьбу, само событие вынесено
в CLAUDE.md «Известные проблемы» для приточной рутины.

Запуск:
    python3 pipeline/fix_rfarm_centr_eko_full_buyout_context.py            # сухой прогон
    python3 pipeline/fix_rfarm_centr_eko_full_buyout_context.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_RATIONALE = (
    'В ближайшие два месяца партнёры разработают новую стратегию '
    'развития компании.'
)
NEW_ECO_RATIONALE = OLD_ECO_RATIONALE + (
    ' 29 мая 2026 года «Р-Фарм» выкупила у Сергея Лебедева оставшиеся '
    '50,1% акций и стала 100%-м владельцем «Центр ЭКО»; сумму этой '
    'сделки стороны также не раскрыли.'
)

NEW_SRC = ['Ведомости', 'https://www.vedomosti.ru/business/articles/2026/06/03/1202336-struktura-gk-r-farm-polnostyu-vikupila-set-klinik']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['gf090d86e']

    assert d['eco']['rationale'] == OLD_ECO_RATIONALE, \
        'gf090d86e eco.rationale уже другой: %r' % (d['eco']['rationale'],)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('gf090d86e: eco.rationale дополнен (полный выкуп 29 мая 2026); '
          'добавлен источник vedomosti.ru')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['rationale'] = NEW_ECO_RATIONALE
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
