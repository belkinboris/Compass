# -*- coding: utf-8 -*-
"""Недельная очередь 18.09.2026: карточка `gf080e8f0` (СберИнвест
приобрёл 30% в «ЦОД СПб») — дельта-поиск нашёл Mergers.ru с независимым
подтверждением ТОЧНОЙ ДАТЫ сделки, расходящейся с тем, что стояло в
карточке.

ГЛАВНАЯ НАХОДКА — СМЕНА ГОДА. Карточка несла `date: "2025"` (год без
месяца) — а единственный найденный источник (Mergers.ru, дословно) прямо
называет: «7 сентября 2026 года в распоряжение ООО «Сбербанк Инвестиции»
... перешла 30-процентная доля в ООО «ЦОД СПб»». 2025-й, судя по всему, —
год РЕГИСТРАЦИИ самого юрлица-предмета («ЦОД СПб» зарегистрировано
28.03.2025), перепутанный на этапе разбора с годом СДЕЛКИ. Это перенос
в ДРУГОЙ год, а не уточнение дня внутри известного — `review.py` для
такого не годится по правилу CLAUDE.md («review.py не умеет переносить
сделку в другой год»), правится одноразовым скриптом с `assert` на
исходное состояние, как и было сделано раньше для `fix_osnova_sviblovo_
date.py` и аналогичных случаев.

Заодно: `eco.context` (был пуст) заполнен тем, что источник рассказывает
о самом «ЦОД СПб» — операционная компания проекта строительства ДВУХ
дата-центров, партнёр проекта ГК «ЦОД Эксперт», её управляющий Дмитрий
Шаров (экс-владелец ИТ-холдинга «Филанко», создатель сети ЦОД
Platforma.ru). Продавец доли НЕ вносится как факт: источник называет
только структурный контекст (в учредителях, помимо СберИнвеста, ООО
«Управление» с долей 70%), но НЕ пишет прямо «Управление продало долю
Сберу» — реконструкция, а не прямое утверждение источника (см. CLAUDE.md,
«Переносить факт можно, сочинять — нет»).

Источник: https://mergers.ru/news/Sberbank-kupil-dolyu-v-COD-SPb-87531
(кэш: data/inbox/raw/2026-09-18-weekly-cluster1d.jsonl)

Запуск: python3 pipeline/fix_codspb_sber_date_and_context.py [--write]
"""
import argparse
import json
import re
from pathlib import Path

DATA = Path('/home/user/static/data/deals_promoted.json')
DEAL_ID = 'gf080e8f0'

OLD_DATE = '2025'
NEW_DATE = '2026-09-07'

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    '«ЦОД СПб» выступает операционной компанией проекта по строительству '
    'двух дата-центров в Санкт-Петербурге. Ведущим консалтинговым, '
    'инженерным и управляющим партнером в рамках данной инициативы '
    'является ГК «ЦОД Эксперт», среди учредителей которой также числится '
    'ООО «Управление». При этом владельцем самого «Управления» указан '
    'Дмитрий Шаров, который одновременно выполняет обязанности '
    'управляющего «ЦОД Эксперт». Он является экс-владельцем и '
    'гендиректором ИТ-холдинга «Филанко», а также создателем сети '
    'дата-центров Platforma.ru.'
)

QUOTE_DATE = (
    '7 сентября 2026 года в распоряжение ООО «Сбербанк Инвестиции» '
    '(входит в экосистему Сбера) перешла 30-процентная доля в ООО «ЦОД '
    'СПб».'
)
QUOTE_CONTEXT = NEW_CONTEXT

SRC_URL = 'https://mergers.ru/news/Sberbank-kupil-dolyu-v-COD-SPb-87531'


def flat(s):
    return re.sub(r'[^0-9a-zа-яё]+', '', str(s or '').lower().replace('ё', 'е'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE, 'дата уже другая: %r' % deal['date']
    assert deal['eco']['context'] == OLD_CONTEXT, 'eco.context уже другой: %r' % deal['eco']['context']
    assert '7 сентября' in QUOTE_DATE and '2026' in QUOTE_DATE
    assert flat(NEW_CONTEXT) in flat(QUOTE_CONTEXT), 'eco.context не лежит дословно в цитате'

    print('date: %r -> %r' % (OLD_DATE, NEW_DATE))
    print('eco.context:', NEW_CONTEXT)

    if args.write:
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_CONTEXT
        urls = {s[1] for s in (deal.get('src') or []) if isinstance(s, list) and len(s) > 1}
        if SRC_URL not in urls:
            deal.setdefault('src', []).append(['Mergers.ru', SRC_URL])
        json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main()
