# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m019: даты по реестру, оценка вместо цены, продавец без опоры.

Чего не умеет review.py: дата по истории участников ЕГРЮЛ (дня нет в статье прописью),
сумма «Не раскрыта» и снятие продавца.

gf3a811bd («УНК Холдинг»/«АТС-Авто»): по ЕГРЮЛ АО «МИГ» вошло в ООО «АТС-Авто» 6 марта 2025 года
  (50%, доля самого общества — прежние участники Алексей Сучков и Тимур Соин вышли 24 сентября 2024
  года), 25 апреля 2025 года — 51%, а Сучков вернулся с 49%. Доля Сучкова не уменьшалась — продавцом
  он не был; продавец снят. «≈50 млн ₽» — мнение эксперта Максима Худалова («вряд ли обошлась
  выше»), не цена сделки.
ga95b1d54 (ГАП «Ресурс»/«Рубеж»): по ЕГРЮЛ Павел Артемов вышел, четыре компании вошли 10 февраля
  2025 года; «6 млрд ₽» — оценка стоимости бизнеса собеседником «Коммерсанта», не цена — в eco.val.
g150f6855 («Самолет»/«Домиленд»): ПАО «ГК «Самолет» вошло 20 декабря 2024 года (Lagella Limited
  вышла в тот же день); 16 января 2025 года — день статьи РБК.

    python3 pipeline/archive/2026-11/reread_dates_sums_m019.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_dates_sums_m019', '2026-11-12'
EGRUL = 'ЕГРЮЛ, история участников (pipeline/party_legal_names.py)'
DATES = {
    'gf3a811bd': ('2025-03-01', '2025-03-06',
                  'ЕГРЮЛ, ООО «АТС-Авто» (ИНН 6321408579): 2025-03-06 joined АО «МИГ» (None → 50.0); '
                  '2025-03-06 left ООО «АТС-Авто» (50.0 → None); 2025-04-25 АО «МИГ» 50.0 → 51.0'),
    'ga95b1d54': ('2025-02-01', '2025-02-10',
                  'ЕГРЮЛ, ООО «Агрофирма «Рубеж» (ИНН 6445005149): 2025-02-10 left Артемов Павел Александрович '
                  '(100.0 → None); 2025-02-10 joined АО «Рест», АО «Южная гавань», ООО «Стойкий» (по 30.0), '
                  'ООО «Портгрейн» (10.0)'),
    'g150f6855': ('2025-01-16', '2024-12-20',
                  'ЕГРЮЛ, ООО «Клиентский сервис» (бывш. «Домиленд»): 2024-12-20 left Лагелла Лимитед '
                  '(75.6803 → None); 2024-12-20 joined ПАО «ГК «Самолет» (None → 75.6803)'),
}
SUMS = {
    'gf3a811bd': ('≈50 млн ₽ (по оценке)',
                  'По оценке независимого эксперта Максима Худалова, покупка доли вряд ли обошлась выше 50 млн руб.',
                  'https://www.kommersant.ru/doc/8007116'),
    'ga95b1d54': ('6 млрд ₽ (по оценке)',
                  'Собеседник “Ъ” на аграрном рынке указывает, что конечным покупателем актива являются структуры '
                  'ГАП «Ресурс» Виктора Наурузова. Стоимость бизнеса агрофирмы «Рубеж» он оценивает в 6 млрд руб.',
                  'https://www.kommersant.ru/doc/7497422'),
}
VAL = ('ga95b1d54', '—', 'По неофициальной оценке, весь бизнес агрофирмы «Рубеж» стоит около 6 млрд ₽.')
SELLER = ('gf3a811bd', 'Алексей Сучков',
          'Продавца в статье нет, а по ЕГРЮЛ доля Алексея Сучкова не уменьшалась: он и Тимур Соин вышли из '
          'ООО «АТС-Авто» 24 сентября 2024 года (их 50% перешли к самому обществу), 6 марта 2025 года АО «МИГ» '
          '(«УНК Холдинг») получило эти 50%, 25 апреля 2025 года — 51%, Сучков вернулся с 49%. Где искали: '
          'Коммерсантъ (8007116), ЕГРЮЛ (история участников), поиск по «АТС-Авто», «Сучков», «Кремлев» (RU), '
          'Telegram-канал «Русский автомобиль» по ссылке «Ъ» — продавцом никто не назван.')


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, (old, new, quote) in DATES.items():
        c = by[cid]
        if c['date'] == new and c.get('date_basis') == 'registry':
            continue
        assert c['date'] == old, (cid, c['date'])
        c['date'] = new
        c['date_basis'] = 'registry'
        fact_edit_guard.log(c, 'date', new, quote, '', BY, DAY)
        n += 1
    for cid, (old, quote, url) in SUMS.items():
        c = by[cid]
        if c['sum'] == 'Не раскрыта':
            continue
        assert c['sum'] == old and c['eco']['sum'] == old, (cid, c['sum'])
        c['sum'] = 'Не раскрыта'
        c['eco']['sum'] = 'Не раскрыта'
        c.setdefault('retracted', {}).setdefault('sum', []).append(old)
        fact_edit_guard.log(c, 'sum', 'Не раскрыта', quote + ' — оценка третьего лица, не цена сделки.', url, BY, DAY)
        fact_edit_guard.log(c, 'eco.sum', 'Не раскрыта', quote + ' — оценка третьего лица, не цена сделки.', url, BY, DAY)
        n += 1
    c = by[VAL[0]]
    if c['eco'].get('val') != VAL[2]:
        assert c['eco'].get('val') == VAL[1], c['eco'].get('val')
        c['eco']['val'] = VAL[2]
        fact_edit_guard.log(c, 'eco.val', VAL[2], SUMS['ga95b1d54'][1], SUMS['ga95b1d54'][2], BY, DAY)
        n += 1
    c = by[SELLER[0]]
    if 'seller' in c:
        assert c['seller'] == SELLER[1] and not c.get('seller_id'), c.get('seller')
        del c['seller']
        c.setdefault('retracted', {}).setdefault('seller', []).append(SELLER[1])
        c.setdefault('accepted_notes', {}).setdefault('no_profile', {})['seller'] = SELLER[2]
        fact_edit_guard.log(c, 'seller', None, SELLER[2], 'https://www.kommersant.ru/doc/8007116', BY, DAY)
        n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
