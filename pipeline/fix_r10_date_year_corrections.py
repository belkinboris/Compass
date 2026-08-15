# -*- coding: utf-8 -*-
"""15 августа 2026: две карточки из партии дочитывания тонких карточек несли
даты притока/импорта вместо даты события источника — та же болезнь, что
`fix_osnova_sviblovo_date.py` и `fix_nordline_arctic_sum_misattribution.py`,
и по той же причине не через `review.py` (`date_is_supported()` намеренно
не даёт менять год через обычную таблицу FIXES).

  c90380a10 (Мосбиржа/брокер): год верный (2024), но день/месяц — заглушка
      импорта (2024-03-01). Источник — «Ъ», номер газеты за 16.08.2024:
      «Газета «Коммерсантъ» №147 от 16.08.2024, стр. 7». Это НЕ через
      обычный FIXES: `date_is_supported()` ищет день и месяц, названные
      ПРОПИСЬЮ («16 августа»), а в тексте статьи есть только газетная шапка
      в цифровом формате — дата от этого не менее достоверна (это дата
      выпуска самой статьи), но не проходит регулярку review.py.
  c4fcc6d29 (МГКЛ/банк драгметаллов): год стоял 2025 (заглушка, без
      месяца/дня) — независимая проверка тремя источниками (Коммерсантъ
      09.07.2026 10:59, Ведомости 09.07.2026 09:30, abireg.ru 09.07.2026)
      единогласно датирует решение совета директоров МГКЛ 9 июля 2026 года,
      а не 2025-м. Разбор источников за 2025 год ничего похожего не находит
      — переговоры о покупке банка начались в марте 2026-го (см. уже
      перенесённый eco.context).

Запуск:
    python3 pipeline/fix_r10_date_year_corrections.py            # сухой прогон
    python3 pipeline/fix_r10_date_year_corrections.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

FIXES = [
    dict(id='c90380a10', old='2024-03-01', new='2024-08-16',
         why='дата выпуска газеты «Ъ» №147 (16.08.2024, стр. 7) — заглушка импорта '
             'заменена на день/месяц публикации источника, год не менялся'),
    dict(id='c4fcc6d29', old='2025', new='2026-07-09',
         why='три независимых СМИ (Коммерсантъ, Ведомости, abireg.ru) датируют решение '
             'совета директоров МГКЛ 9 июля 2026 года; заглушка «2025» без месяца/дня '
             'заменена на подтверждённую полную дату'),
]


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for fix in FIXES:
        deal = by_id.get(fix['id'])
        assert deal is not None, 'нет сделки %s' % fix['id']
        assert deal.get('date') == fix['old'], \
            '%s: дата уже другая: %r, ожидали %r' % (fix['id'], deal.get('date'), fix['old'])
        print('%s: date %r -> %r  (%s)' % (fix['id'], fix['old'], fix['new'], fix['why']))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for fix in FIXES:
        by_id[fix['id']]['date'] = fix['new']

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
