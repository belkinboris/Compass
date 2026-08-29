#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Карточка ГК «Ланит»/Elari несла дату-заглушку (год 2022), хотя источник
датирован 2024 годом, — и сумму без пометки оценки, хотя источник прямо
называет её оценкой третьего лица, а сами стороны условия не раскрывают.

ЧТО СЛОМАНО. Карточка `g0be89c20» («ГК «Ланит» купила российские активы
израильской Elari») стояла с `date: "2022"`. Единственный источник
(iz.ru, «Частное дело. Израильский разработчик гаджетов Elari продал
активы в РФ») ДАТИРОВАН «1 февраля 2024, 00:01» — статья не называет
отдельной, более ранней даты закрытия сделки; независимый WebSearch
(telecomdaily.ru, kommersant.ru, lanit.ru — пресс-релиз самой группы
«Ланит») подтверждает ТУ ЖЕ дату: «Это объявление было сделано 1 февраля
2024 года». Согласуется и с находкой волны 3 самопроверки ИНН: юрлицо
покупателя (ELARI IT) зарегистрировано в январе 2024 года — за несколько
дней до объявления сделки, а не в 2022-м. Год «2022» — заглушка того же
класса, что уже чинился `fix_placeholder_dates.py` (родня урока «Дата
новости — не дата сделки», только здесь и года не было никакого — просто
неверный).

ЧТО С СУММОЙ. `eco.sum` нёс «500 млн ₽» без пометки — источник же прямо
называет её оценкой: «По словам участника рынка электроники, знакомого с
представителями одной из её сторон, стоимость российского бизнеса Elari
могла составлять до 500 млн рублей» — и WebSearch независимо подтверждает
«Финансовые условия сделки стороны не разглашают» (lanit.ru, официальный
пресс-релиз). Дописана пометка «(по оценке)» — тот же принцип, что уже
применён к десяткам других карточек (`sum_is_supported()` в `review.py`).

Запуск:
    python3 pipeline/fix_elari_lanit_date_and_sum.py            # сухой прогон
    python3 pipeline/fix_elari_lanit_date_and_sum.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'g0be89c20'
TARGET_COMPANY = 'g351f3735'
OLD_DATE = '2022'
NEW_DATE = '2024-02-01'
OLD_SUM = '500 млн ₽'
NEW_SUM = '500 млн ₽ (по оценке)'
OLD_DESC = 'В 2022 году их купила ГК «Ланит» за 500 млн ₽.'
NEW_DESC = 'В 2024 году их купила ГК «Ланит» за 500 млн ₽ (по оценке).'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    companies = data['companies']

    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    deal_pending = deal.get('date') == OLD_DATE
    if deal_pending:
        assert deal.get('sum') == OLD_SUM, '%s: sum уже не %r (сейчас %r)' % (DEAL_ID, OLD_SUM, deal.get('sum'))
        assert deal.get('eco', {}).get('sum') == OLD_SUM, \
            '%s: eco.sum уже не %r (сейчас %r)' % (DEAL_ID, OLD_SUM, deal.get('eco', {}).get('sum'))
    else:
        assert deal.get('date') == NEW_DATE, '%s: date в неожиданном состоянии: %r' % (DEAL_ID, deal.get('date'))

    company = companies.get(TARGET_COMPANY)
    assert company is not None, 'нет профиля %s' % TARGET_COMPANY
    desc_pending = company.get('desc') == OLD_DESC
    if not desc_pending:
        assert company.get('desc') == NEW_DESC, \
            '%s: desc в неожиданном состоянии: %r' % (TARGET_COMPANY, company.get('desc'))

    if deal_pending:
        print('Сделка: %s | %s' % (DEAL_ID, deal.get('title')))
        print('date: %r -> %r (источник датирован 1 февраля 2024, а не 2022 — заглушка)' % (OLD_DATE, NEW_DATE))
        print('sum и eco.sum: %r -> %r (источник называет её оценкой, а стороны условия не раскрывают)'
              % (OLD_SUM, NEW_SUM))
    else:
        print('Сделка %s: date/sum уже поправлены прошлым прогоном.' % DEAL_ID)
    if desc_pending:
        print('Профиль %s: desc %r -> %r' % (TARGET_COMPANY, OLD_DESC, NEW_DESC))
    else:
        print('Профиль %s: desc уже поправлен прошлым прогоном.' % TARGET_COMPANY)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    if deal_pending:
        deal['date'] = NEW_DATE
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_SUM
    if desc_pending:
        company['desc'] = NEW_DESC

    assert by_id[DEAL_ID]['date'] == NEW_DATE
    assert by_id[DEAL_ID]['sum'] == NEW_SUM
    assert by_id[DEAL_ID]['eco']['sum'] == NEW_SUM
    assert companies[TARGET_COMPANY]['desc'] == NEW_DESC

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
