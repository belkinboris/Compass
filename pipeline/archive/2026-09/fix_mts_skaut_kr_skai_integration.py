# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g43c78df8` («МТС приобрела контроль в разработчике телематических
решений СКАУТ-КР», апрель 2023, Закрыта) — `eco.context` был заглушкой
(«—»), хотя интеграция после сделки хорошо задокументирована.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- comnews.ru/content/225843/2023-04-27/2023-w17/mts-priobrela-kontrol-kompanii-skaut-kr
  (27.04.2023): «Сделка позволит интегрировать уникальную платформу
  SKAI, разработанную «СКАУТ-КР», в продуктовые решения МТС»; компания
  «будет функционировать в периметре группы МТС как самостоятельная
  компания, которой продолжит руководить нынешняя команда основателей и
  менеджмента».

НЕ ВНЕСЕНО: (1) довела ли МТС долю до 100% — по данным реестрового
агрегатора (list-org.com, без личной проверки первички) доля МТС
по-прежнему 51%, а Висневские сохраняют 49% — не внесено как факт без
прямой выписки ЕГРЮЛ; (2) финансовые показатели за 2024-2025 годы (по
тому же агрегатору — выручка выросла более чем вдвое, убыток тоже
вырос) — тот же класс осторожности, не проверено личным чтением
первички; (3) официальное название продукта SKAI и точная дата
ребрендинга — сайт продукта (skai.online) отдал 403 при попытке
проверки, не подтверждено напрямую.

Запуск: python3 pipeline/fix_mts_skaut_kr_skai_integration.py
        python3 pipeline/fix_mts_skaut_kr_skai_integration.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g43c78df8'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Сделка позволила интегрировать платформу SKAI, разработанную '
    '«СКАУТ-КР», в продуктовые решения МТС по мониторингу транспорта; '
    'сама компания продолжила работать в периметре группы МТС как '
    'самостоятельная структура под руководством прежней команды '
    'основателей и менеджмента.'
)

OLD_SRC = [['Интерфакс', 'https://www.interfax.ru/amp/898045']]
NEW_SRC = OLD_SRC + [
    ['ComNews', 'https://www.comnews.ru/content/225843/2023-04-27/2023-w17/mts-priobrela-kontrol-kompanii-skaut-kr'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
