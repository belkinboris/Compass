# -*- coding: utf-8 -*-
"""Слой фактов (facts.py) и подтверждение чтением (pipeline/facts_confirm.py).

Что здесь проверяется — не «код делает заложенное», а границы механизма:
правило только предлагает (basis rule), в расчёт идёт только verified,
изменение карточки делает прочитанный факт stale, два несогласных чтения
дают disputed, а не «победил первый»; арифметика — отдельный уровень.
"""
import facts
from pipeline import facts_confirm as fc

REG = {'t1': {'company_id': 't1', 'decision': 'confirmed', 'inn': '7700000001'},
       'bank1': {'company_id': 'bank1', 'decision': 'bank', 'inn': '7700000002'}}
CTX = {'registry': REG, 'lot_ids': {'lot1'}}


def _deal(**kw):
    d = {'id': 'd1', 'title': 'X купил 100% ООО «Ромашка»', 'type': 'M&A', 'status': 'Закрыта', 'date': '2024-03-01',
         'sum': '1 000 млн ₽', 'target': 't1', 'buyer': 'b1', 'seller': 'Продавец', 'ind': 'ИТ и интернет',
         'eco': {'share': 'Куплено 100% долей'}}
    d.update(kw)
    return d


def _verified(d):
    f = facts.derive(d, CTX)
    for key in ('stake', 'price'):
        f[key]['basis'] = 'verified'
    f['price']['scope'] = 'equity'
    f['price']['attribution'] = 'parties'
    f['target']['perimeter'] = 'verified'
    f['target']['perimeter_report'] = {'inn': '7700000001', 'year': 2023, 'revenue_rub': 5e8}
    f['nature']['control_change_basis'] = 'verified'
    return facts.derive(dict(d, facts=f), CTX)


def test_rules_only_propose_and_multiple_needs_verified():
    f = facts.derive(_deal(), CTX)
    assert f['stake'] == dict(f['stake'], value=100.0, basis='rule')
    assert f['price']['meaning'] == 'disclosed' and f['price']['basis'] == 'rule' and f['price']['value_rub'] == 1e9
    assert f['admitted']['count'] is True
    # деньги только из прочитанных цен — и для графиков, и для списка крупнейших
    assert f['admitted']['purchase_sums'] is False and f['reasons']['purchase_sums'] == 'price_not_read'
    assert f['admitted']['top_purchases'] is False and f['reasons']['top_purchases'] == 'price_not_read'
    assert f['admitted']['multiple_text'] is False and f['reasons']['multiple_text'] == 'price_not_verified'
    v = _verified(_deal())
    assert v['admitted']['multiple_text'] is True and v['admitted']['top_purchases'] is True


def test_metrics_admit_independently():
    # цена не названа — число сделок и отрасль считаются, суммы нет
    f = facts.derive(_deal(sum='Не раскрыта'), CTX)
    assert f['admitted']['count'] and f['admitted']['industry'] and not f['admitted']['purchase_sums']
    assert f['reasons']['purchase_sums'] == 'price_not_disclosed'
    # доля не названа, цена прочитана — суммы считаются, мультипликатор нет
    d = _deal(eco={'share': '—'}, title='X купил ООО «Ромашка»')
    f = facts.derive(d, CTX); f['price']['basis'] = 'read'; f['price']['attribution'] = 'parties'
    f = facts.derive(dict(d, facts=f), CTX)
    assert f['admitted']['purchase_sums'] and f['reasons']['multiple_text'] in ('control_change_not_verified', 'price_not_verified', 'stake_not_verified')
    # допэмиссия — не покупка ни для сумм, ни для мультипликатора
    f = facts.derive(_deal(type='Инвестиция', title='Допэмиссия в пользу X'), CTX)
    assert f['nature']['cash_in'] and not f['admitted']['purchase_sums'] and f['reasons']['purchase_sums'] == 'not_purchase'
    # незакрытые торги — стартовая цена, не покупка
    f = facts.derive(_deal(type='Продажа с торгов', status='Обсуждается'), CTX)
    assert f['reasons']['purchase_sums'] == 'auction_open'
    # банк и лот — не мультипликатор, но суммы считаются
    assert facts.derive(_deal(target='bank1'), CTX)['reasons']['multiple_text'] == 'target_bank'
    assert facts.derive(_deal(target='lot1'), CTX)['reasons']['multiple_text'] == 'target_lot'
    assert facts.derive(_deal(target='unknown-co'), CTX)['reasons']['multiple_text'] == 'target_unconfirmed'


def test_verified_fact_survives_derive_but_goes_stale_when_card_changes():
    d = _deal()
    d['facts'] = _verified(d)
    again = facts.derive(d, CTX)
    assert again['price']['basis'] == 'verified' and again['admitted']['multiple_text']
    # сумма карточки изменилась (энрич принёс другую цену) — факт цены stale, допуск снят
    changed = dict(d, sum='2 000 млн ₽')
    f = facts.derive(changed, CTX)
    assert f['price']['basis'] == 'stale' and f['price']['stale_from'] == 'verified'
    assert not f['admitted']['multiple_text'] and f['reasons']['multiple_text'] == 'stale'
    assert not f['admitted']['top_purchases']
    # доля не менялась — её факт остался verified
    assert f['stake']['basis'] == 'verified'


def test_derive_is_idempotent_on_the_live_base():
    import json
    from pipeline import fns_registry
    base = json.load(open('static/data/deals_promoted.json', encoding='utf-8'))
    ctx = facts.build_ctx(base, fns_registry.REGISTRY)
    for d in base['deals'][:300]:
        once = facts.derive(d, ctx)
        assert facts.derive(dict(d, facts=once), ctx) == once, d['id']


def test_number_checks_catch_units_currency_and_package_price():
    d = _deal()
    d['facts'] = facts.derive(d, CTX)
    assert facts.number_checks(d) == []
    d['facts']['price']['value_rub'] = 1e15
    assert 'price_out_of_range' in facts.number_checks(d)
    d['facts']['price']['value_rub'] = 1e12  # «1 000 млн» не может быть триллионом
    assert 'unit_mismatch' in facts.number_checks(d)
    d = _deal(sum='$150 млн')
    d['facts'] = facts.derive(d, CTX)
    d['facts']['price']['value_rub'] = 1.5e10
    assert 'foreign_currency' in facts.number_checks(d)


# ---------- подтверждение чтением ----------

def test_reading_checks_value_against_quote():
    assert fc.stake_supported(100.0, 'Arenadata приобрела 100% долей ООО «Убик»')
    assert not fc.stake_supported(100.0, 'консолидировала 100% долей')
    assert fc.stake_supported(100.0, 'покупатель стал единственным владельцем компании')
    assert fc.price_supported(1.8e9, 'Сумма сделки составила 1,8 млрд руб.')
    assert not fc.price_supported(1.8e9, 'Сумма сделки составила 2 млрд руб.')
    assert fc.date_supported('2026-04-21', 'Сделка закрыта 21 апреля.')
    assert not fc.date_supported('2026-04-21', 'Сделка закрыта в мае.')
    assert fc.entity_supported('ООО «Убик»', 'разработчик ООО «Убик» продан')
    assert not fc.entity_supported('ООО «Убик»', 'разработчик продан')


def test_check_reading_flags_quote_not_in_source_and_bad_values():
    card = _deal(src=[['Интерфакс', 'https://x/1']])
    texts = {'https://x/1': 'X купил 100% долей ООО «Ромашка» за 1 млрд руб. Сделка закрыта 1 марта.'}
    good = {'id': 'd1', 'reader': 'A',
            'price': {'value_rub': 1e9, 'meaning': 'disclosed', 'scope': 'equity',
                      'quote': 'X купил 100% долей ООО «Ромашка» за 1 млрд руб.', 'source': 'https://x/1'},
            'date': {'value': '2024-03-01', 'meaning': 'closing', 'quote': 'Сделка закрыта 1 марта.', 'source': 'https://x/1'},
            'nature': {'control_change': True, 'quote': 'X купил 100% долей'},
            'stake': {'value': 100, 'object': 'ООО «Ромашка»', 'event': 'closing',
                      'quote': 'X купил 100% долей ООО «Ромашка»', 'source': 'https://x/1'},
            'perimeter': {'ok': True, 'entity': 'ООО «Ромашка»', 'quote': 'X купил 100% долей ООО «Ромашка»', 'source': 'https://x/1'}}
    norm, problems = fc.check_reading(good, card, texts)
    assert problems == [], problems
    assert norm['price']['quote_checked'] is True
    bad = dict(good, price=dict(good['price'], quote='X купил компанию за 1 млрд руб.'))
    _, problems = fc.check_reading(bad, card, texts)
    assert any('цитата не найдена' in p for p in problems)
    bad = dict(good, stake=dict(good['stake'], value=51))
    _, problems = fc.check_reading(bad, card, texts)
    assert any('не выводится из цитаты' in p for p in problems)
    # цена читателя расходится с суммой карточки — сначала правка карточки
    bad = dict(good, price=dict(good['price'], value_rub=2e9, quote='X купил 100% долей ООО «Ромашка» за 1 млрд руб.'))
    _, problems = fc.check_reading(bad, card, texts)
    assert problems


def test_two_readers_agree_verified_disagree_disputed():
    a = {'_key': 'stake', 'value': 100.0, 'event': 'closing', 'quote': 'X купил 100% долей ООО «Ромашка» у продавца за деньги',
         'quote_checked': True, 'source': 'https://example.com/a'}
    b = dict(a, reader='B')
    assert fc._basis_for([a, b])[0] == 'verified'
    assert fc._basis_for([a, dict(b, value=51.0)])[0] == 'disputed'
    assert fc._basis_for([a])[0] == 'read'
    # цитаты не сверены с текстом, но совпадают на восемь слов — verified; разные — read
    a2, b2 = dict(a, quote_checked=None), dict(b, quote_checked=None)
    # источника в кэше нет, цитата не сверена — одинаковые цитаты двух чтений
    # больше НЕ дают verified: статус не может быть сильнее основания
    assert fc._basis_for([a2, b2])[0] == 'read'
    assert fc._basis_for([a2, dict(b2, quote='совсем другая фраза о том же')])[0] == 'read'


def test_third_review_rules():
    """Третий разбор рецензента (6 сентября 2026): спорная дата блокирует
    денежные показатели; подозрение на дубль — тоже; смена контроля должна быть
    подтверждена сама по себе; периметр — привязан к конкретному отчёту; год
    мультипликатора берётся из подтверждённой даты закрытия."""
    import deal_multiples as dm
    d = _deal()
    v = _verified(d)
    assert v['admitted']['multiple_text'] and v['admitted']['purchase_sums']
    # спорная дата
    f = dict(v); f['date'] = dict(v['date'], basis='disputed')
    f = facts.derive(dict(d, facts=f), CTX)
    assert f['reasons']['purchase_sums'] == 'date_disputed' and f['reasons']['multiple_text'] == 'date_disputed'
    # смена контроля не подтверждена
    f = dict(v); f['nature'] = dict(v['nature'], control_change_basis='rule')
    f = facts.derive(dict(d, facts=f), CTX)
    assert f['reasons']['multiple_text'] == 'control_change_not_verified'
    assert f['nature']['basis'] == 'rule'  # флаги природы остаются правилом
    # периметр без отчёта
    f = dict(v); f['target'] = dict(v['target']); f['target'].pop('perimeter_report')
    f = facts.derive(dict(d, facts=f), CTX)
    assert f['reasons']['multiple_text'] == 'perimeter_report_missing'
    # год из подтверждённой даты закрытия
    f = dict(v); f['date'] = dict(v['date'], basis='verified', meaning='closing', value='2025-10-09')
    assert dm.multiple_year(dict(d, facts=f)) == (2025, 'подтверждённая дата закрытия')
    year, basis = dm.multiple_year(d)
    assert year == 2024 and basis.startswith('дата карточки') and 'предварительн' in basis
    # подписано в декабре, закрытие не прочитано — год предварительный по подписанию;
    # прочитали закрытие в январе — год сменился и больше не предварительный
    f = dict(v); f['date'] = dict(v['date'], basis='verified', meaning='signing', value='2024-12-20')
    year, basis = dm.multiple_year(dict(d, facts=f))
    assert year == 2024 and 'подписания' in basis and 'предварительн' in basis
    f = dict(v); f['date'] = dict(v['date'], basis='verified', meaning='closing', value='2025-01-15')
    assert dm.multiple_year(dict(d, facts=f)) == (2025, 'подтверждённая дата закрытия')
    # неполное основание чтения: без адреса «подтверждённым» не становится
    import pipeline.facts_confirm as fc
    r1 = {'_key': 'nature', 'control_change': True, 'quote': 'купил', 'quote_checked': True, 'source': 'https://x/1'}
    assert fc._basis_for([r1, dict(r1, reader='B')])[0] == 'verified'
    assert fc._basis_for([r1, dict(r1, reader='B', source=None)])[0] == 'read'
    assert fc._basis_for([r1, dict(r1, reader='B', quote_checked=None)])[0] == 'read'
    # ярлык стадии одной сделки — не спор: берётся сильнейший, разночтения видны
    m = fc.merged_fields('price', [{'value_rub': 1e9, 'meaning': 'disclosed', 'event': 'announcement', 'scope': 'equity', 'terms': 'fixed'},
                                   {'value_rub': 1e9, 'meaning': 'disclosed', 'event': 'closing', 'scope': 'equity', 'terms': 'fixed'}])
    assert m['event'] == 'closing' and m['event_variants'] == ['announcement', 'closing'] and m['terms'] == 'fixed'
    # но неразрешённый спор о событии — не допуск к деньгам
    f = dict(v); f['price'] = dict(v['price'], event='disputed')
    f = facts.derive(dict(d, facts=f), CTX)
    assert f['reasons']['purchase_sums'] == 'price_event_disputed'
    # передача внутри группы — не покупка на рынке
    f = dict(v); f['nature'] = dict(v['nature'], intragroup=True, control_change=False)
    f = facts.derive(dict(d, facts=f), CTX)
    assert f['reasons']['purchase_sums'] == 'intragroup'
    # автор числа неизвестен или слаб — цена не идёт в деньги, даже подтверждённая
    for who in (None, 'unknown', 'adviser', 'media_sources', 'analyst'):
        f = dict(v); f['price'] = dict(v['price'], attribution=who)
        f = facts.derive(dict(d, facts=f), CTX)
        assert f['reasons']['purchase_sums'] == 'price_author_unknown' and f['reasons']['multiple_text'] == 'price_author_unknown', who
    # точность: значение не точнее цитаты
    assert fc.price_precise_enough(50_800_000_000, 'сумма сделки — 50,8 млрд руб.')
    assert not fc.price_precise_enough(50_785_000_000, 'сумма сделки — 50,8 млрд руб.')
    assert fc.price_precise_enough(50_785_000_000, 'сумма сделки — 50,785 млрд руб.')
    assert not fc.price_precise_enough(66_132_908_002.5, 'за 66,1 млрд руб.')
    assert fc.price_precise_enough(66_132_908_002.5, 'цена продажи составила 66 132 908 002,5 руб.')
    # число, названное анонимными источниками, — не цена, названная сторонами
    assert dm.sum_basis({'sum': '38,2 млрд ₽', 'sum_basis': 'reported'}) == 'reported'
    f = dict(v); f['price'] = dict(v['price'], meaning='reported')
    f = facts.derive(dict(d, facts=f), CTX)
    assert f['reasons']['purchase_sums'] == 'price_not_disclosed'


def test_own_shares_are_not_a_purchase():
    """Buyback и выкуп у нерезидентов — сделка компании с собственными
    акциями: цена названа и прочитана («Магнит», 48,5 млрд ₽), а в покупки
    и мультипликаторы не идёт. «С правом обратного выкупа» — условие залога,
    а не выкуп."""
    for title in ('«Магнит» выкупил свои акции у иностранных инвесторов с дисконтом',
                  'Buyback ПАО «Полюс»: приобретение до 29,99% собственных обыкновенных акций',
                  'ЛУКОЙЛ выкупает до 25% акций у нерезидентов',
                  'X5 рассматривает продажу казначейского пакета акций (9,7%) инвесторам'):
        f = _verified(_deal(title=title))
        f = facts.derive(dict(_deal(title=title), facts=f), CTX)
        assert f['nature']['own_shares'] and not f['nature']['control_change'], title
        assert f['reasons']['purchase_sums'] == 'not_purchase' and f['reasons']['multiple_text'] == 'not_control_change', title
    f = facts.derive(_deal(title='Государство может получить пакет акций «Самолета» с правом обратного выкупа'), CTX)
    assert not f['nature']['own_shares']
    f = facts.derive(_deal(title='«Медскан» выкупил долю «Сбербанк Инвестиций» в KDL'), CTX)
    assert not f['nature']['own_shares'] and f['nature']['control_change']


def test_possible_duplicates_block_money_metrics():
    a = _verified(_deal(id='a1', title='«Магнит» покупает контрольный пакет «Азбуки вкуса»', sum='29,65 млрд ₽'))
    b = _verified(_deal(id='b1', title='«Тандер» покупает сеть «Азбука вкуса»', sum='29,6 млрд ₽', target='t2'))
    base = {'deals': [dict(_deal(id='a1', title='«Магнит» покупает контрольный пакет «Азбуки вкуса»', sum='29,65 млрд ₽'), facts=a),
                      dict(_deal(id='b1', title='«Тандер» покупает сеть «Азбука вкуса»', sum='29,6 млрд ₽', target='t2'), facts=b)],
            'companies': {}}
    facts.mark_possible_duplicates(base, CTX)
    for d in base['deals']:
        assert d['facts']['identity']['possible_duplicate'], d['id']
        assert d['facts']['reasons']['purchase_sums'] == 'possible_duplicate'
    # прочитанная пара не-дублей снимает подозрение
    facts.mark_possible_duplicates(base, dict(CTX, not_duplicates={frozenset(('a1', 'b1'))}))
    assert all('identity' not in d['facts'] for d in base['deals'])
    # общий покупатель и близкая сумма при разных предметах — не подозрение
    c = _verified(_deal(id='c1', title='Softline купила «МД Аудит»', sum='163 млн ₽', target='t1'))
    e = _verified(_deal(id='e1', title='Softline купила Visitech', sum='162 млн ₽', target='t2'))
    base2 = {'deals': [dict(_deal(id='c1', title='Softline купила «МД Аудит»', sum='163 млн ₽', target='t1'), facts=c),
                       dict(_deal(id='e1', title='Softline купила Visitech', sum='162 млн ₽', target='t2'), facts=e)], 'companies': {}}
    facts.mark_possible_duplicates(base2, CTX)
    assert all('identity' not in d['facts'] for d in base2['deals'])
