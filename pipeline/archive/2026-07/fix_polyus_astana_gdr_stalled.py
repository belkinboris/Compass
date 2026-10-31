# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `ca599969b»
(«Полюс рассматривает размещение глобальных депозитарных расписок на
Astana International Exchange», 2024) описывала только сам факт
рассмотрения плана; состоялось ли размещение — было неизвестно.

Личный WebFetch подтвердил дословно (Interfax, 22 июня 2023,
https://interfax.com/newsroom/top-stories/91736/): «The board of
directors at Polyus on Thursday decided that it would no longer be
reasonable for the company to maintain its GDR and ADR programs» —
совет директоров решил не поддерживать программы ГДР/АДР вовсе, без
упоминания казахстанской площадки.

Прямого опровержения плана по AIX (объявленного позже, судя по дате
карточки, в 2024 году) не нашлось, но и подтверждения фактического
размещения — тоже: обзор эмитентов Astana International Exchange от
25 октября 2023 года (t-j.ru, WebSearch-выдержка, не проверено личным
WebFetch дословно — только для контекста, не как источник факта в
карточку) называет реально торгующихся эмитентов (включая Ozon,
«Русагро», Fix Price), «Полюса» среди них нет. Это отсутствие
подтверждения, а не опровержение (родня уже записанного в CLAUDE.md
класса «БКС/«Форштадт»») — статус карточки НЕ меняется, только
называется честно найденный факт.

Запуск:
    python3 pipeline/fix_polyus_astana_gdr_stalled.py            # сухой прогон
    python3 pipeline/fix_polyus_astana_gdr_stalled.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_LAW_STRUCT = (
    'В июне 2023 года совет директоров «Полюса» решил не поддерживать '
    'программы депозитарных расписок вовсе (делистинг с Лондонской '
    'фондовой биржи). Подтверждения, что размещение на Astana '
    'International Exchange фактически состоялось, не нашлось: обзоры '
    'эмитентов площадки за 2023–2025 годы «Полюса» среди реально '
    'торгующихся компаний не называют.'
)

NEW_SRC = ['Interfax (EN)', 'https://interfax.com/newsroom/top-stories/91736/']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['ca599969b']

    assert 'struct' not in d.get('law', {}), 'law.struct уже занят: %r' % (d['law'].get('struct'),)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('ca599969b: law.struct заполнен (делистинг с LSE, размещение на '
          'AIX не подтверждено); добавлен источник; status не менялся')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d.setdefault('law', {})['struct'] = NEW_LAW_STRUCT
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
