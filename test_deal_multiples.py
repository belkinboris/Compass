# -*- coding: utf-8 -*-
"""Тесты на мультипликаторы сделок (deal_multiples.py) — каждый тест ловит
конкретную ловушку, найденную пилотом (pipeline/measure_deal_multiples_pilot.py,
Этап 15) или встречающуюся в реальной базе. Не happy-path ради галочки:
цель — чтобы регрессия в фильтре была не тише, чем сам баг, который он чинит."""
import deal_multiples as dm


def _deal(**kw):
    base = dict(type='M&A', date='2024-06-01', sum='1 000 млн ₽',
                target='target1', buyer='buyer1', seller='Иван Иванов',
                eco={'share': None}, asset=None)
    base.update(kw)
    return base


# ---------- parse_rub_sum ----------

def test_parse_rub_sum_simple():
    assert dm.parse_rub_sum('500 млн ₽') == 500_000_000


def test_parse_rub_sum_range_averages():
    assert dm.parse_rub_sum('36–45 млн ₽') == 40_500_000


def test_parse_rub_sum_rejects_dollars():
    assert dm.parse_rub_sum('$150 млн') is None


def test_parse_rub_sum_rejects_euros():
    assert dm.parse_rub_sum('€200 млн') is None


def test_parse_rub_sum_rejects_undisclosed():
    assert dm.parse_rub_sum('Не раскрыта') is None
    assert dm.parse_rub_sum(None) is None


def test_parse_rub_sum_billions_and_trillions():
    assert dm.parse_rub_sum('1,2 трлн ₽') == 1_200_000_000_000
    assert dm.parse_rub_sum('850 тыс ₽') == 850_000


# ---------- is_estimate ----------

def test_is_estimate_detects_marker():
    assert dm.is_estimate('500 млн ₽ (по оценке)')
    assert not dm.is_estimate('500 млн ₽')
    assert not dm.is_estimate(None)


# ---------- stake_percent ----------

def test_stake_percent_from_eco_share():
    d = _deal(eco={'share': 'Приобретено 30% доли компании'})
    assert dm.stake_percent(d) == 30.0


def test_stake_percent_from_asset():
    d = _deal(asset='49,9% акций ООО «Ромашка»')
    assert dm.stake_percent(d) == 49.9


def test_stake_percent_none_when_not_mentioned():
    d = _deal()
    assert dm.stake_percent(d) is None


# ---------- find_candidates: текстовый фильтр ----------

CONFIRMED = {'target1'}
BANKS = set()


def test_candidate_requires_ma_type():
    d = _deal(type='Инвестиция')
    assert dm.find_candidates({'d1': d}, CONFIRMED, BANKS) == []


def test_candidate_requires_both_buyer_and_seller():
    # Точь-в-точь класс Segezha-допэмиссии и SPO «Эталона»: type=M&A,
    # но ни покупателя, ни продавца нет — деньги идут в компанию, а не от
    # одного акционера другому.
    d = _deal(buyer=None, buyer_name=None, seller=None, seller_id=None)
    assert dm.find_candidates({'d1': d}, CONFIRMED, BANKS) == []


def test_candidate_requires_seller_even_with_buyer_name():
    d = _deal(buyer=None, buyer_name='Некий фонд', seller=None, seller_id=None)
    assert dm.find_candidates({'d1': d}, CONFIRMED, BANKS) == []


def test_candidate_accepts_seller_id_without_seller_text():
    d = _deal(seller=None, seller_id='sellerprofile1')
    out = dm.find_candidates({'d1': d}, CONFIRMED, BANKS)
    assert len(out) == 1


def test_candidate_rejects_deal_before_2022():
    d = _deal(date='2021-01-01')
    assert dm.find_candidates({'d1': d}, CONFIRMED, BANKS) == []


def test_candidate_requires_target_in_confirmed_registry():
    d = _deal(target='unknown_company')
    assert dm.find_candidates({'d1': d}, CONFIRMED, BANKS) == []


def test_candidate_rejects_bank_target():
    d = _deal(target='target1')
    out = dm.find_candidates({'d1': d}, CONFIRMED, {'target1'})
    assert out == []


def test_candidate_uses_asset_id_when_target_missing():
    d = _deal(target=None, asset_id='target1')
    out = dm.find_candidates({'d1': d}, CONFIRMED, BANKS)
    assert len(out) == 1
    assert out[0].target_id == 'target1'


def test_candidate_rejects_estimate_marker():
    d = _deal(sum='500 млн ₽ (по оценке)')
    assert dm.find_candidates({'d1': d}, CONFIRMED, BANKS) == []


def test_candidate_rejects_small_stake():
    d = _deal(eco={'share': 'Приобретено 30% доли'})
    assert dm.find_candidates({'d1': d}, CONFIRMED, BANKS) == []


def test_candidate_accepts_large_stake():
    d = _deal(eco={'share': 'Приобретено 100% доли'})
    out = dm.find_candidates({'d1': d}, CONFIRMED, BANKS)
    assert len(out) == 1


def test_candidate_accepts_unspecified_stake():
    # Доля не названа вовсе — трактуется как потенциально 100%, не
    # отбрасывается заранее (в отличие от явно названной маленькой доли).
    d = _deal(eco={'share': None}, asset=None)
    out = dm.find_candidates({'d1': d}, CONFIRMED, BANKS)
    assert len(out) == 1


def test_candidate_rejects_non_ruble_sum():
    d = _deal(sum='$150 млн')
    assert dm.find_candidates({'d1': d}, CONFIRMED, BANKS) == []


# ---------- multiple_for_candidate: санитарная граница ----------

def _cand(**kw):
    base = dict(deal_id='d1', title='т', target_id='target1', year=2024,
                sum_rub=1_000_000_000, stake_percent=None)
    base.update(kw)
    return dm.MultipleCandidate(**base)


def test_multiple_computed_for_reasonable_case():
    c = _cand()
    r = dm.multiple_for_candidate(c, revenue_rub=500_000_000, revenue_year=2023, target_name='ООО Т')
    assert r is not None
    assert r.multiple == 2.0


def test_multiple_none_when_no_revenue():
    c = _cand()
    assert dm.multiple_for_candidate(c, None, None, None) is None


def test_multiple_none_when_revenue_year_after_deal_year():
    # Выручка из БУДУЩЕГО относительно сделки — не должна использоваться.
    c = _cand(year=2022)
    r = dm.multiple_for_candidate(c, revenue_rub=500_000_000, revenue_year=2023, target_name='ООО Т')
    assert r is None


def test_multiple_none_when_year_gap_too_large():
    c = _cand(year=2024)
    r = dm.multiple_for_candidate(c, revenue_rub=500_000_000, revenue_year=2021, target_name='ООО Т')
    assert r is None


def test_multiple_ok_when_year_gap_is_one():
    c = _cand(year=2024)
    r = dm.multiple_for_candidate(c, revenue_rub=500_000_000, revenue_year=2023, target_name='ООО Т')
    assert r is not None


def test_multiple_rejects_absurdly_high_ratio():
    # Ровно класс g5eb6ff22 из пилота: сумма 75,5 млрд ₽, revenue юрлица-
    # прослойки 17,4 млн ₽ -> 4336x. Это не редкая сделка, это не то юрлицо.
    c = _cand(sum_rub=75_500_000_000)
    r = dm.multiple_for_candidate(c, revenue_rub=17_400_000, revenue_year=2023, target_name='ООО Т')
    assert r is None


def test_multiple_rejects_near_zero_ratio():
    # Класс g4cd1fa52: revenue огромного холдинга при небольшой доле-сумме.
    c = _cand(sum_rub=8_100_000_000)
    r = dm.multiple_for_candidate(c, revenue_rub=7_979_026_900_000, revenue_year=2023, target_name='ООО Т')
    assert r is None


def test_multiple_boundary_values_are_inclusive():
    c = _cand(sum_rub=1_000_000_000)
    lo = dm.multiple_for_candidate(c, revenue_rub=10_000_000_000, revenue_year=2023, target_name='X')
    assert lo is not None and lo.multiple == 0.1
    hi = dm.multiple_for_candidate(c, revenue_rub=1_000_000_000 / 15, revenue_year=2023, target_name='X')
    assert hi is not None and hi.multiple == 15.0


# ---------- multiple_for_candidate_op: тот же санитарный шаг, знаменатель —
# операционная прибыль, а не выручка ----------

def test_op_multiple_computed_for_reasonable_case():
    c = _cand()
    r = dm.multiple_for_candidate_op(c, operating_profit_rub=200_000_000,
                                      operating_profit_year=2023, target_name='ООО Т')
    assert r is not None
    assert r.multiple == 5.0
    assert r.operating_profit_rub == 200_000_000
    assert r.operating_profit_year == 2023


def test_op_multiple_none_when_operating_loss():
    # Операционный убыток — не ноль и не маленькое число, а отсутствие
    # осмысленного мультипликатора: делить на отрицательное нельзя.
    c = _cand()
    r = dm.multiple_for_candidate_op(c, operating_profit_rub=-50_000_000,
                                      operating_profit_year=2023, target_name='ООО Т')
    assert r is None


def test_op_multiple_none_when_missing():
    c = _cand()
    assert dm.multiple_for_candidate_op(c, None, None, None) is None


def test_op_multiple_respects_same_year_gap_rule():
    c = _cand(year=2024)
    assert dm.multiple_for_candidate_op(
        c, operating_profit_rub=200_000_000, operating_profit_year=2021,
        target_name='ООО Т') is None


def test_op_multiple_respects_same_absurd_ratio_rule():
    c = _cand(sum_rub=75_500_000_000)
    assert dm.multiple_for_candidate_op(
        c, operating_profit_rub=17_400_000, operating_profit_year=2023,
        target_name='ООО Т') is None


def test_op_multiple_independent_from_revenue_multiple():
    # Одна и та же сделка: выручка даёт честный мультипликатор, операционная
    # прибыль (например, компания на грани нуля) — нет. Функции не должны
    # зависеть друг от друга или делить общее состояние.
    c = _cand()
    revenue_side = dm.multiple_for_candidate(c, revenue_rub=500_000_000,
                                              revenue_year=2023, target_name='ООО Т')
    op_side = dm.multiple_for_candidate_op(c, operating_profit_rub=1_000_000,
                                            operating_profit_year=2023, target_name='ООО Т')
    assert revenue_side is not None and revenue_side.multiple == 2.0
    assert op_side is None  # 1000x — за границей MAX_MULTIPLE


# ---------- industry_medians ----------

def _dm_row(multiple, target_id='t1', deal_id=None):
    return dm.DealMultiple(deal_id=deal_id or ('d_%s' % multiple), title='т',
                            target_id=target_id, target_name='Т', year=2024,
                            sum_rub=1, revenue_rub=1, revenue_year=2023, multiple=multiple)


def test_industry_medians_requires_minimum_sample():
    industry_of = {'t1': 'ИТ', 't2': 'ИТ'}
    rows = [_dm_row(1.0, 't1', 'd1'), _dm_row(2.0, 't2', 'd2')]
    assert dm.industry_medians(rows, industry_of) == []


def test_industry_medians_with_enough_samples():
    industry_of = {'t1': 'ИТ', 't2': 'ИТ', 't3': 'ИТ'}
    rows = [_dm_row(1.0, 't1', 'd1'), _dm_row(2.0, 't2', 'd2'), _dm_row(3.0, 't3', 'd3')]
    out = dm.industry_medians(rows, industry_of)
    assert len(out) == 1
    assert out[0]['industry'] == 'ИТ'
    assert out[0]['count'] == 3
    assert out[0]['median'] == 2.0


def test_industry_medians_unknown_industry_bucketed_honestly():
    industry_of = {}
    rows = [_dm_row(1.0, 't1', 'd1'), _dm_row(2.0, 't2', 'd2'), _dm_row(3.0, 't3', 'd3')]
    out = dm.industry_medians(rows, industry_of)
    assert out[0]['industry'] == 'Не определена'


def test_overall_median_empty_list():
    assert dm.overall_median([]) is None


def test_overall_median_even_count_averages_middle_two():
    rows = [_dm_row(1.0, deal_id='d1'), _dm_row(3.0, deal_id='d2')]
    assert dm.overall_median(rows) == 2.0


def test_generic_helpers_work_on_op_profit_rows_too():
    # industry_medians/overall_median читают только .multiple/.target_id —
    # тот же код обязан честно работать и на OpProfitMultiple, без
    # отдельной копии ради операционной прибыли.
    op_rows = [
        dm.OpProfitMultiple(deal_id='d1', title='т', target_id='t1', target_name='Т',
                             year=2024, sum_rub=1, operating_profit_rub=1,
                             operating_profit_year=2023, multiple=1.0),
        dm.OpProfitMultiple(deal_id='d2', title='т', target_id='t2', target_name='Т',
                             year=2024, sum_rub=1, operating_profit_rub=1,
                             operating_profit_year=2023, multiple=2.0),
        dm.OpProfitMultiple(deal_id='d3', title='т', target_id='t3', target_name='Т',
                             year=2024, sum_rub=1, operating_profit_rub=1,
                             operating_profit_year=2023, multiple=3.0),
    ]
    assert dm.overall_median(op_rows) == 2.0
    industry_of = {'t1': 'ИТ', 't2': 'ИТ', 't3': 'ИТ'}
    out = dm.industry_medians(op_rows, industry_of)
    assert out == [{'industry': 'ИТ', 'count': 3, 'median': 2.0, 'min': 1.0, 'max': 3.0}]


# ---------- аудит 5 сентября 2026: доля из заголовка, мягкие суммы, год отчётности ----------

def test_stake_is_read_from_the_title_too():
    # g85883f11: «Ростех приобрел 25% в разработчике платформы OneCell…» — доля
    # только в заголовке, eco.share пуст; сумму за пакет делили на выручку всей
    # компании (×0,55 при честных ×2,2 даже без поправки на долг).
    deal = {'title': 'Ростех приобрел 25% в разработчике платформы OneCell', 'eco': {'share': '—'}}
    assert dm.stake_percent(deal) == 25.0
    deal = {'title': 'Софтлайн купил 51% К2-9b, ИБ-компанию', 'eco': {}}
    assert dm.stake_percent(deal) == 51.0
    assert dm.stake_percent({'title': 'Купил завод', 'eco': {}}) is None


def test_soft_prices_are_not_prices():
    for text in ('~100 млн ₽ (или EV ~1 млрд ₽)', '400 млн ₽ (первый этап)', 'около 10 млрд ₽',
                 'до 6 млрд ₽', '≈20 млрд ₽', '35–40 млрд ₽ (неофициально)', '~3 млрд ₽ (без учета долга)',
                 'около 500 млрд ₽ (допэмиссия ВТБ)',
                 # диапазон без пометки — тоже оценка: цену, названную сторонами, не пишут «от и до»
                 # (аудит, раунд 2: «30–40 млрд ₽» за Sokolov стояло в «Крупнейших покупках»)
                 '15–20 млрд ₽', '30-40 млрд ₽'):
        assert dm.is_estimate(text), text
    for text in ('1,5 млрд ₽', '754 млн ₽ (плюс условное возмещение до 478 млн ₽)', '41 500 млн ₽'):
        assert not dm.is_estimate(text), text


def test_multiple_none_when_report_is_for_the_deal_year():
    # На дату сделки результата за тот же год ещё нет: февраль 2025 нельзя
    # делить на выручку за весь 2025 год (аудит 5 сентября 2026).
    c = _cand(year=2025)
    assert dm.multiple_for_candidate(c, revenue_rub=500_000_000, revenue_year=2025, target_name='X') is None
    assert dm.multiple_for_candidate_op(c, operating_profit_rub=200_000_000,
                                        operating_profit_year=2025, target_name='X') is None


def test_multiple_ok_when_report_is_two_years_old():
    # Сделка в начале года, отчёт за прошлый год ещё не сдан — берётся позапрошлый.
    c = _cand(year=2025)
    r = dm.multiple_for_candidate(c, revenue_rub=500_000_000, revenue_year=2023, target_name='X')
    assert r is not None and r.revenue_year == 2023


def test_stake_is_the_smallest_named_share_not_the_largest():
    # Аудит, раунд 2 (6 сентября 2026): Guess «консолидировали 100% …, выкупив
    # 30%» и БФТ «приобрёл 49% …, партнёр сохранил 51%» проходили порог 95%,
    # потому что бралась наибольшая доля из текста.
    guess = {'title': 'Guess выкупил 30% долю российского партнера',
             'eco': {'share': 'Структуры Guess консолидировали 100% ООО «Гесс», выкупив 30% в компании'}}
    assert dm.stake_percent(guess) == 30.0
    bft = {'title': 'БФТ-Холдинг приобрел 49% в ООО «Полиматика Рус»', 'asset': '49% ООО «Полиматика Рус»',
           'eco': {'share': 'приобрёл 49%; партнёр сохранил 51% доли; 100% другого ООО осталось у него'}}
    assert dm.stake_percent(bft) == 49.0
    whole = {'title': 'Купил 100% акций', 'eco': {'share': 'Приобретено 100% уставного капитала'}}
    assert dm.stake_percent(whole) == 100.0
