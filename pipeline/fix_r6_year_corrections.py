# -*- coding: utf-8 -*-
"""Восемь карточек 2022 года, которые на самом деле — 2023 (партия 5 агентов,
раунд 6, 15 августа 2026).

ЧТО СЛОМАНО. У всех восьми карточек день/месяц в источнике СОВПАДАЕТ с уже
записанным в базе — расходится только год. Проверено дважды: сначала
WebSearch-агентом, затем — дословной проверкой самого текста статьи (дата
публикации в шапке страницы + сам факт закрытия), см. коммит. Примеры:
gd607171c несёт «2022-02-02», источник (vedomosti.ru/.../2023/02/07/...,
опубликован 07.02.2023) прямо пишет «сделка была закрыта 2 февраля» — тот же
день и месяц, год другой.

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. `date_is_supported()` категорически не пускает
смену года через FIXES («год не совпадает: уточнять день можно, переносить
год — нет») — это сознательная граница, а не недоработка (см. CLAUDE.md,
запись про fix_osnova_sviblovo_date.py). Смена года — отдельный скрипт со
своим assert на исходное состояние, как и было с тем прецедентом.

ГОД БЕЗ ДНЯ ТАМ, ГДЕ ДЕНЬ НЕ НАЗВАН. У g2a27e6b5 источник говорит «в июне»
без числа, у g020432e9 — «в феврале» без числа: писать «2023-06-01» значило
бы выдумать день. В дату идёт только год, месяц остаётся текстом в
eco.context (тот же приём, что fix_placeholder_dates.py).

ЗАПУСК:
    python3 pipeline/fix_r6_year_corrections.py            # сухой прогон
    python3 pipeline/fix_r6_year_corrections.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (id, old_date, new_date, old_status, new_status, eco_context_addition_or_None, src_label, src_url)
FIXES = [
    ('g2a27e6b5', '2022', '2023', 'Обсуждается', 'Закрыта',
     'В июне 2023 года «АвтоВАЗ» закрыл сделку по приобретению 100% акций '
     'РН банка у холдинговой компании BARN B.V.',
     'Интерфакс', 'https://www.interfax.ru/business/919177'),
    ('g343154dd', '2022-03-01', '2023-03-01', 'Закрыта', 'Закрыта', None,
     'Интерфакс', 'https://www.interfax.ru/business/889368'),
    ('g020432e9', '2022-03-01', '2023', 'Обсуждается', 'Закрыта',
     'Сделка закрыта в феврале 2023 года: структура Игоря Кима (ООО '
     '«Экспокап») приобрела лизинговую и факторинговую «дочки» CNH '
     'Industrial в России.',
     'Интерфакс', 'https://www.interfax.ru/business/898224'),
    ('gd607171c', '2022-02-02', '2023-02-02', 'Закрыта', 'Закрыта', None,
     'Ведомости', 'https://www.vedomosti.ru/business/articles/2023/02/07/961917-protek-vikupil-u-shelkova-aktivi-bion'),
    ('gecf3eca5', '2022', '2023-04-26', 'Обсуждается', 'Закрыта', None,
     'TAdviser', 'https://www.tadviser.ru/index.php/Компания:АЛД_Автомотив'),
    ('c7fd83d05', '2022-07-01', '2023-07-16', 'Закрыта', 'Закрыта', None,
     'Коммерсантъ', 'https://www.kommersant.ru/doc/6109525'),
    ('gff6e08fe', '2022-09-01', '2023-08-23', 'Закрыта', 'Закрыта', None,
     'Medvestnik', 'https://medvestnik.ru/content/news/Sberbank-priobrel-dolu-v-klinikah-Evroonko.html'),
    ('cdcf1a650', '2022-09-01', '2023-09-18', None, 'Закрыта', None,
     'Коммерсантъ', 'https://www.kommersant.ru/doc/6223624'),
]


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for cid, old_date, new_date, old_status, new_status, ctx, label, url in FIXES:
        deal = by_id[cid]
        assert deal.get('date') == old_date, \
            '%s: date уже другой: %r (ожидали %r)' % (cid, deal.get('date'), old_date)
        assert deal.get('status') == old_status, \
            '%s: status уже другой: %r (ожидали %r)' % (cid, deal.get('status'), old_status)
        if ctx:
            cur_ctx = (deal.get('eco') or {}).get('context')
            assert cur_ctx in (None, '', '—'), \
                '%s: eco.context уже не пуст: %r' % (cid, cur_ctx)
        print('ПРАВИМ %s: date %r -> %r, status %r -> %r' % (
            cid, old_date, new_date, old_status, new_status))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for cid, old_date, new_date, old_status, new_status, ctx, label, url in FIXES:
        deal = by_id[cid]
        deal['date'] = new_date
        deal['status'] = new_status
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
