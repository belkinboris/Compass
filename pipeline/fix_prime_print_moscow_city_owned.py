# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `cdcf1a650`
(«Передача долей в сети типографий «Прайм Принт» от Amedia в
управление Росимущества», 18 сентября 2023) описывала только сам факт
передачи; дальнейшая судьба московской типографии была неизвестна.

Личный WebFetch подтвердил дословно (Audit-it.ru,
https://www.audit-it.ru/contragent/1025001199519_ao-praym-print-moskva):
«Г.МОСКВА права учредителя осуществляет ДЕПАРТАМЕНТ ГОРОДСКОГО
ИМУЩЕСТВА ГОРОДА МОСКВЫ» (данные с 25.12.2023); статус — «коммерческая,
действующая»; выручка за 2025 год — 1,2 млрд ₽ (снижение на 3,7% к
2024 году), прибыль — 33 млн ₽ (рост в 19,6 раза к 2024 году).

Типография не вернулась к прежнему владельцу и не продана в частные
руки — перешла в собственность города Москвы и продолжает работать.
Две версии, всплывшие в поиске (продажа инвестору из Татарстана за
17,7 млрд ₽ по «указу №186», продажа Умару Кремлёву), при проверке НЕ
подтвердились ни одним первоисточником — не вносятся.

Запуск:
    python3 pipeline/fix_prime_print_moscow_city_owned.py            # сухой прогон
    python3 pipeline/fix_prime_print_moscow_city_owned.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_ECO_TARGET_FIN = (
    'С 25 декабря 2023 года права учредителя московской типографии '
    '(АО «Прайм Принт Москва») осуществляет Департамент городского '
    'имущества Москвы — предприятие действующее, в частные руки не '
    'продано. Выручка за 2025 год — 1,2 млрд ₽, прибыль — 33 млн ₽ '
    '(рост в 19,6 раза к 2024 году).'
)

NEW_SRC = ['Audit-it.ru', 'https://www.audit-it.ru/contragent/1025001199519_ao-praym-print-moskva']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['cdcf1a650']

    assert d['eco'].get('target_fin') in (None, '—'), 'eco.target_fin уже занят: %r' % (d['eco'].get('target_fin'),)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('cdcf1a650: eco.target_fin заполнен (типография под управлением '
          'города Москвы, финансовые показатели 2025); добавлен источник')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['target_fin'] = NEW_ECO_TARGET_FIN
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
