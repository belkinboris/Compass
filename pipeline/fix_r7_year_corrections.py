# -*- coding: utf-8 -*-
"""Одиннадцать карточек 2022–2023 годов раунда 7 (партия 5 агентов), у
которых год в дате не совпадает с годом источника — систематическая ошибка
года-заглушки, а не единичная опечатка (см. CLAUDE.md, коммит раунда 7).

Батч 3 нашёл девять таких карточек разом, батч 5 — ещё две; во всех
случаях единственный/основной источник карточки датирован не тем годом,
что стоит в поле `date`, и описывает событие, которое на момент
объявленной в карточке даты («2023») ещё не могло произойти (компания-
покупатель не была создана, ЕГРЮЛ ещё не зафиксировал переход).

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. `date_is_supported()` категорически не
пускает смену года через FIXES («год не совпадает: уточнять день можно,
переносить год — нет») — сознательная граница, не недоработка (см.
CLAUDE.md, fix_osnova_sviblovo_date.py). Смена года — отдельный скрипт со
своим assert на исходное состояние.

ГОД БЕЗ ДНЯ ТАМ, ГДЕ ТОЧНАЯ ДАТА СОБЫТИЯ НЕ НАЗВАНА. У шести карточек
источник называет только дату ПУБЛИКАЦИИ статьи или общий период, а не
точный день самого события (регистрации в ЕГРЮЛ, закрытия сделки) — туда
идёт только год, а период остаётся текстом в eco.context, если оно было
пустым (тот же приём, что fix_placeholder_dates.py). У пяти карточек
источник называет точный день события — туда идёт полная дата.

ЗАПУСК:
    python3 pipeline/fix_r7_year_corrections.py            # сухой прогон
    python3 pipeline/fix_r7_year_corrections.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (id, old_date, new_date, eco_context_addition_or_None, src_label, src_url)
FIXES = [
    ('g02a89309', '2023', '2025-12-05', None,
     'Ведомости', 'https://www.vedomosti.ru/realty/articles/2025/12/11/1162351-struktura-gazprombanka-stala-vladeltsem'),
    ('ge1fbcfb8', '2023', '2024',
     'Сведения о смене владельца зафиксированы в ЕГРЮЛ к 4 декабря 2024 '
     'года, когда об этом сообщил AK&M.',
     'AK&M', 'https://www.akm.ru/news/kompaniya_optovoy_torgovli_optikom_kupila_logisticheskogo_operatora_iz_podmoskovya/'),
    ('g54dc2165', '2023', '2022', None,
     'RB.RU', 'https://rb.ru/news/megafon-onefactor/'),
    ('g7c8f9112', '2023', '2025-12-29', None,
     'CNews', 'https://www.cnews.ru/news/top/2026-01-12_softline_venture_vlozhilsya_millionami'),
    ('g3875e8f5', '2023', '2025', None,
     'РИА Недвижимость', 'https://realty.ria.ru/20251202/tishinka-2059121888.html'),
    ('g0a6cea12', '2023', '2025-04-15', None,
     'Полюс', 'https://polyus.com/ru/media/press-releases/sale-of-the-marokskoye-deposit/'),
    ('g703c4f62', '2023', '2024', None,
     'Коммерсантъ', 'https://www.kommersant.ru/doc/7267872'),
    ('gf76413f3', '2023', '2024', None,
     'Korabel.ru', 'https://www.korabel.ru/news/comments/suek_vyshla_iz_portovogo_biznesa.html'),
    ('gef02a680', '2023', '2024', None,
     'Коммерсантъ', 'https://www.kommersant.ru/doc/6760695'),
    ('g1caed4b7', '2023', '2025', None,
     'Коммерсантъ', 'https://www.kommersant.ru/doc/8041497'),
    ('c4341479b', '2023', '2024', None,
     'Telegram', 'https://t.me/dealsma/4634'),
]


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for cid, old_date, new_date, ctx, label, url in FIXES:
        deal = by_id[cid]
        assert deal.get('date') == old_date, \
            '%s: date уже другой: %r (ожидали %r)' % (cid, deal.get('date'), old_date)
        if ctx:
            cur_ctx = (deal.get('eco') or {}).get('context')
            assert cur_ctx in (None, '', '—'), \
                '%s: eco.context уже не пуст: %r' % (cid, cur_ctx)
        print('ПРАВИМ %s: date %r -> %r' % (cid, old_date, new_date))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for cid, old_date, new_date, ctx, label, url in FIXES:
        deal = by_id[cid]
        deal['date'] = new_date
        if ctx:
            deal.setdefault('eco', {})['context'] = ctx
        existing_urls = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
        if url not in existing_urls:
            deal.setdefault('src', []).append([label, url])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
