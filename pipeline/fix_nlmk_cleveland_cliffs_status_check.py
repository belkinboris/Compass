# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g5a1ee21e
(НЛМК продает американские заводы Cleveland-Cliffs) — карточка стоит
«Обсуждается» с мая 2024 года; REVISION_BRIEF.md прямо требует для
незакрытых сделок обязательную проверку статуса как самого вредного
класса устаревания. Проверено лично прямым WebFetch.

Ни закрытия, ни срыва сделки НЕ НАЙДЕНО ни в одном источнике 2024-2026 —
но нашёлся сильный косвенный сигнал, что переговоры не продвинулись:
пресс-релиз Primetals Technologies от 22 апреля 2026 года прямо называет
NLMK Indiana частью группы НЛМК, без единого намёка на смену владельца.
Дословно: «NLMK Indiana is part of NLMK USA which employs more than
1,100 people across its facilities in Indiana and Pennsylvania and
produces 2.7 million tons of steel annually.»
https://www.primetals.com/en/news/nlmk-indiana-receives-gold-reliability-achievement-award-for-eaf-upgrade-with-primetals-technologies/

Это НЕ доказательство срыва переговоров (обе стороны никогда официально
их не подтверждали и в 2024-м, отказ от комментариев зафиксирован уже в
`law.terms`) — станционарное владение почти через два года после
объявления о переговорах лишь показывает, что если сделка и произойдёт,
на 22.04.2026 она ещё не произошла. `status` НЕ меняется: ни «Закрыта»,
ни «Не состоялась» не подтверждены явно (родня уже записанным случаям
«заявленные сроки закрытия прошли без подтверждения — статусы намеренно
НЕ изменены», VIM/Поклонка и Суточно/OneTwoTrip).

НЕ ВКЛЮЧЕНО: независимая оценка суммы (кроме $500 млн Bloomberg, которую
дублируют все источники без альтернативы); консультанты сделки — не
названы нигде; согласования OFAC/антимонопольных органов США — не
нашлось ни одного упоминания НЛМК в новостях OFAC 2025-2026 (только
генеральные лицензии по Роснефти/Лукойлу, к этой сделке отношения не
имеющие).

Запуск: python3 pipeline/fix_nlmk_cleveland_cliffs_status_check.py
        python3 pipeline/fix_nlmk_cleveland_cliffs_status_check.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g5a1ee21e'

OLD_CONTEXT = (
    'НЛМК приобрел завод в 2007 году в рамках совместного предприятия с '
    'Duferco Group, а в 2011 году стал его полноправным владельцем.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' По состоянию на 22 апреля 2026 года подтверждений закрытия или '
    'срыва переговоров не найдено: пресс-релиз производителя '
    'металлургического оборудования Primetals Technologies по-прежнему '
    'называет NLMK Indiana частью группы НЛМК — «NLMK Indiana is part of '
    'NLMK USA which employs more than 1,100 people across its facilities '
    'in Indiana and Pennsylvania».'
)

NEW_SRC = [
    ['Primetals Technologies', 'https://www.primetals.com/en/news/nlmk-indiana-receives-gold-reliability-achievement-award-for-eaf-upgrade-with-primetals-technologies/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    assert deal['status'] == 'Обсуждается'
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
