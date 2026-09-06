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
    f['target']['perimeter'] = 'verified'
    return facts.derive(dict(d, facts=f), CTX)


def test_rules_only_propose_and_multiple_needs_verified():
    f = facts.derive(_deal(), CTX)
    assert f['stake'] == dict(f['stake'], value=100.0, basis='rule')
    assert f['price']['meaning'] == 'disclosed' and f['price']['basis'] == 'rule' and f['price']['value_rub'] == 1e9
    assert f['admitted']['purchase_sums'] is True and f['admitted']['count'] is True
    assert f['admitted']['top_purchases'] is False and f['reasons']['top_purchases'] == 'price_not_read'
    assert f['admitted']['multiple_text'] is False and f['reasons']['multiple_text'] == 'price_not_verified'
    v = _verified(_deal())
    assert v['admitted']['multiple_text'] is True and v['admitted']['top_purchases'] is True


def test_metrics_admit_independently():
    # цена не названа — число сделок и отрасль считаются, суммы нет
    f = facts.derive(_deal(sum='Не раскрыта'), CTX)
    assert f['admitted']['count'] and f['admitted']['industry'] and not f['admitted']['purchase_sums']
    assert f['reasons']['purchase_sums'] == 'price_not_disclosed'
    # доля не названа — суммы считаются, мультипликатор нет
    f = facts.derive(_deal(eco={'share': '—'}, title='X купил ООО «Ромашка»'), CTX)
    assert f['admitted']['purchase_sums'] and f['reasons']['multiple_text'] in ('price_not_verified', 'stake_not_verified')
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
    a = {'_key': 'stake', 'value': 100.0, 'event': 'closing', 'quote': 'X купил 100% долей ООО «Ромашка» у продавца за деньги', 'quote_checked': True}
    b = dict(a, reader='B')
    assert fc._basis_for([a, b])[0] == 'verified'
    assert fc._basis_for([a, dict(b, value=51.0)])[0] == 'disputed'
    assert fc._basis_for([a])[0] == 'read'
    # цитаты не сверены с текстом, но совпадают на восемь слов — verified; разные — read
    a2, b2 = dict(a, quote_checked=None), dict(b, quote_checked=None)
    assert fc._basis_for([a2, b2])[0] == 'verified'
    assert fc._basis_for([a2, dict(b2, quote='совсем другая фраза о том же')])[0] == 'read'
