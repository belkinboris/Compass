# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gf6be51a1
(Ростелеком продал 100% акций GNC-Alfa/OVIO компании Вива Армения) —
дата сделки была перепутана на ДВА ГОДА, а карточка описывала только
промежуточный шаг (регуляторное согласие), а не реальное закрытие.
Проверено лично прямым WebFetch каждого источника.

ДАТА. Карточка несла «2024-07-02» — источник этой даты, interfax.ru/
business/1034004, датирован 1 ИЮЛЯ 2025 ГОДА (проверено WebFetch), и сам
текст говорит о том, что КРОУ «НАМЕРЕНА разрешить» продажу — то есть это
даже не согласование, а анонс намерения. Настоящее согласие КРОУ дано
2 июля 2025 года (abireg.ru, дословно: «Комиссия по регулированию
общественных услуг Армении (КРОУ) 2 июля 2025 года одобрила сделку»)
— на год позже даты в карточке. Но и это не закрытие: реальная продажа
потребовала ВТОРОГО, антимонопольного согласования — «Комиссия по защите
экономической конкуренции Армении» одобрила сделку около 18 июня 2026
года (Sputnik Армения: по состоянию на 18.06.2026 сделка «будет завершена
в ближайшие дни»), и закрытие объявлено статьями от 7-8 июля 2026 года
(Коммерсантъ, ComNews, CNews, smart-lab — все независимо). Точный день
закрытия ни один источник не называет («в ближайшие дни» — не дата),
поэтому в `date` идёт ТОЛЬКО год (2026), а не выдуманное число (тот же
принцип, что уже применён в `fix_osnova_sviblovo_date.py`). Перенос в
другой год не проходит через `review.py` (правило CLAUDE.md), поэтому
отдельный скрипт с assert на исходное значение.

ДОБАВЛЕНО/ИЗМЕНЕНО:
- `law.appr` (было «Публично не сообщалось», хотя extra уже пересказывало
  факт согласования прозой) — дословные цитаты: КРОУ «не представили
  возражений» со стороны Службы нацбезопасности и министерства
  высокотехнологичной промышленности (interfax.ru/business/1034270), плюс
  второе, более позднее согласование антимонопольной комиссии в июне 2026.
- `sum`/`eco.sum`/`eco.val` — атрибуция сильнее прежней безымянной оценки
  по мультипликатору: замгендиректора OVIO Борис Демирханян оценил сделку
  примерно в $40 млн (interfax.ru/business/1034270, дословная цитата),
  старая расчётная оценка ~$37 млн (по EV/OIBDA=3,5) сохранена в `eco.val`
  как более ранний, менее авторитетный расчёт.
- `eco.context` (новое поле) — история сделки (переговоры велись почти
  10 лет, с 2017 года, включая несостоявшийся вариант с Molitro Holdings
  около 2021 года) и планы Viva после закрытия (конвергентная платформа,
  инвестиции $150 млн в 5G за 3 года).

НЕ включены: консультанты сделки — не найдены ни в одном из ~15
проверенных источников; прямая причина продажи (санкции/стратегия) — ни
один источник её не формулирует явно, только упоминание многолетних
переговоров.

Запуск: python3 pipeline/fix_rostelecom_gncalfa_viva_date_and_details.py
        python3 pipeline/fix_rostelecom_gncalfa_viva_date_and_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf6be51a1'

OLD_DATE = '2024-07-02'
NEW_DATE = '2026'

OLD_SUM = '~$37 млн (по оценке)'
NEW_SUM = '~$40 млн (по оценке)'
OLD_ECO_SUM = '≈$37 млн (по оценке)'
NEW_ECO_SUM = '≈$40 млн (по оценке)'

OLD_APPR = 'Публично не сообщалось'
NEW_APPR = (
    'КРОУ Армении одобрила сделку 2 июля 2025 года; «Служба нацбезопасности '
    'и министерство высокотехнологичной промышленности Армении, по данным '
    'КРОУ, не представили возражений по поводу сделки» (Интерфакс). Второе, '
    'антимонопольное согласование — Комиссия по защите экономической '
    'конкуренции Армении — дано около 18 июня 2026 года (Sputnik Армения).'
)

OLD_VAL = 'Расчётная оценка; ~$37 млн (по оценке)'
NEW_VAL = (
    'Заместитель гендиректора OVIO Борис Демирханян: «Стоимость сделки '
    'будет определена в ходе финальных обсуждений, но на сегодняшний день '
    'она оценивается примерно в $40 млн» (Интерфакс). Более ранняя '
    'расчётная оценка по мультипликатору EV/OIBDA=3,5 давала ≈$37 млн '
    '(abireg.ru).'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Переговоры о продаже GNC-Alfa велись почти 10 лет: начались в 2017 '
    'году, около 2021 года обсуждался несостоявшийся вариант с кипрским '
    'офшором Molitro Holdings. После закрытия Viva объявила о создании '
    '«полноценной конвергентной платформы, объединяющей мобильную связь, '
    'фиксированный интернет, телевидение... в единую экосистему» и '
    'инвестициях $150 млн в 5G и облачную инфраструктуру за 3 года.'
)

NEW_SRC = [
    ['interfax.ru', 'https://www.interfax.ru/business/1034270'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/8797894'],
    ['ComNews', 'https://www.comnews.ru/content/246269/2026-07-08/2026-w28/1009/rostelekom-posle-10-let-peregovorov-izbavilsya-edinstvennogo-zarubezhnogo-aktiva'],
    ['Sputnik Армения', 'https://am.sputniknews.ru/20260618/v-armenii-obedinyatsya-dva-krupnykh-telekom-operatora-regulyator-odobril-sdelku-103620812.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['sum'] == OLD_SUM
    assert deal['eco']['sum'] == OLD_ECO_SUM
    assert deal['law']['appr'] == OLD_APPR
    assert deal['eco']['val'] == OLD_VAL
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print(f'=== date: {OLD_DATE!r} -> {NEW_DATE!r} ===')
    print(f'=== sum: {OLD_SUM!r} -> {NEW_SUM!r} ===')
    print(f'=== eco.sum: {OLD_ECO_SUM!r} -> {NEW_ECO_SUM!r} ===')
    print('=== law.appr: было ===')
    print(OLD_APPR)
    print('=== law.appr: станет ===')
    print(NEW_APPR)
    print('=== eco.val: станет ===')
    print(NEW_VAL)
    print('=== eco.context (новое поле): станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['date'] = NEW_DATE
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_ECO_SUM
        deal['law']['appr'] = NEW_APPR
        deal['eco']['val'] = NEW_VAL
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
