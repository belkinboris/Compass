# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gmru-roshim-vnt` («Росхим» может приобрести Восточный нефтехимический
терминал в Приморье, Обсуждается, 21 июля 2026) — поле «Цель сделки»
(`eco.rationale`) пустовало, хотя мотив покупки прямо назван в
источнике: это часть более широкой портовой стратегии «Росхима».

Проверено ЛИЧНО прямым WebFetch (infranews.ru/novosti/70778-roshim-
interesuetsya-pokupkoj-vostochnogo-neftehimicheskogo-terminala-v-
primore/): «Ранее сообщалось об интересе компании к Петербургскому
нефтяному терминалу в контексте стратегии холдинга по консолидации
логистических активов для экспорта химической продукции»; «"Росхим"
достраивает морской терминал в порту Находки для Находкинского завода
минеральных удобрений».

НЕ ВНЕСЕНО: сделка «Росхим»/Петербургский нефтяной терминал (передача
55% акций Росимуществом) — это ДРУГАЯ, отдельная и, по всей видимости,
уже закрытая сделка (другой предмет, другая сторона — госимущество, а
не «СпецХимТранс»), не относящаяся к этой карточке; решение о новой
карточке — за притоком. Дата закрытия/сумма сделки по самому ВНТ
по-прежнему не найдены нигде — публикаций позже 21 июля 2026 года не
нашлось, `status` НЕ меняется.

`buyer`/`seller`/`target`/`status` карточки НЕ тронуты.

Запуск: python3 pipeline/fix_roshim_vnt_port_strategy_rationale.py
        python3 pipeline/fix_roshim_vnt_port_strategy_rationale.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gmru-roshim-vnt'

OLD_ECO_RATIONALE = '—'
NEW_ECO_RATIONALE = (
    'Интерес к ВНТ — часть более широкой стратегии «Росхима» по '
    'консолидации портовой логистики для экспорта химической продукции: '
    'холдинг ранее интересовался Петербургским нефтяным терминалом и '
    'достраивает собственный морской терминал в порту Находки для '
    'Находкинского завода минеральных удобрений.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['rationale'] == OLD_ECO_RATIONALE

    print('=== eco.rationale: станет ===')
    print(NEW_ECO_RATIONALE)

    if write:
        deal['eco']['rationale'] = NEW_ECO_RATIONALE
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
