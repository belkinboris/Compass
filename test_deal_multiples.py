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
