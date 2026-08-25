# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gf8dfe9c4 (Softline
покупает 51% DreamDocs): дельта-поиск нашёл точную дату анонса (16
апреля 2025 года — известен был только год) и, что важнее, нашёл повод
усомниться в собственном же поле `extra`: оно утверждало «в процессе
закрытия», а данные ЕГРЮЛ на 04.08.2025 (пять месяцев спустя после
анонса) показывают Аболмасова единственным (100%) владельцем АПЭРБОТ —
Softline/SL Soft среди участников не значится. Годовой отчёт Softline по
МСФО за 2025 год (разобран Коммерсантом) называет другие закрытые в этот
период M&A-сделки, но не упоминает DreamDocs/АПЭРБОТ вовсе — что было бы
странно, будь сделка реально закрыта. Категорическое утверждение о
статусе, ничем не подкреплённое и противоречащее прямой проверке
реестра, честнее снять, чем оставить.

Запуск: python3 pipeline/fix_softline_dreamdocs_status_correction.py
        python3 pipeline/fix_softline_dreamdocs_status_correction.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf8dfe9c4'

OLD_DATE = '2025'
NEW_DATE = '2025-04-16'

OLD_EXTRA = (
    'Сделка по приобретению 51% долей компании АПЭРБОТ, управляющей '
    'платформой DreamDocs для автоматизации обработки документов с '
    'использованием ИИ. Покупатель — SL Soft (входит в ГК Softline). '
    'Продавец — Аболмасов Александр Геннадьевич, который после сделки '
    'останется владельцем 49%. Статус: в процессе закрытия.'
)
NEW_EXTRA = (
    'Сделка по приобретению 51% долей компании АПЭРБОТ, управляющей '
    'платформой DreamDocs для автоматизации обработки документов с '
    'использованием ИИ. Покупатель — SL Soft (входит в ГК Softline). '
    'Продавец — Аболмасов Александр Геннадьевич, который после сделки '
    'останется владельцем 49%. По данным ЕГРЮЛ на 4 августа 2025 года, '
    'Аболмасов по-прежнему значился единственным (100%) участником '
    'АПЭРБОТ — подтверждения закрытия сделки в открытых источниках не '
    'нашлось.'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Анонс — рамочное соглашение о приобретении 51% доли, объявленное 16 '
    'апреля 2025 года. По данным пресс-релиза, контракты DreamDocs в 2024 '
    'году превысили 400 млн руб., к команде SL Soft после интеграции '
    'должны присоединиться около 50 специалистов.'
)

NEW_SRC = [
    ['slsoft.ru', 'https://slsoft.ru/news/sl-soft-usilivaet-portfel-ii-resheniy-za-schet-priobreteniya-platformy-dreamdocs/'],
    ['list-org.com', 'https://www.list-org.com/company/12442785'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['extra'] == OLD_EXTRA
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== date ===', NEW_DATE)
    print('=== extra ===')
    print(NEW_EXTRA)
    print('=== eco.context ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['date'] = NEW_DATE
        deal['extra'] = NEW_EXTRA
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
