# -*- coding: utf-8 -*-
"""Оценка нераскрытой цены (valuation_estimate.py, прототип 24 октября 2026)."""
import valuation_estimate as ve


def _rows(industry, n, ps=1.0, ev_op=5.0, pe=8.0):
    return [{'id': 'r%d' % i, 'title': 'сделка %d' % i, 'industry': industry,
             'metrics': {'ps': {'status': 'ok', 'value': ps + i * 0.1},
                         'ev_op': {'status': 'ok', 'value': ev_op + i},
                         'pe': {'status': 'ok', 'value': pe + i}}} for i in range(n)]


def test_revenue_multiple_needs_own_industry():
    """Выручка туроператора × медиана всех отраслей дала 375 млрд ₽ — цена к
    выручке берётся только по сделкам своей отрасли."""
    comps = ve.comparables(_rows('Ритейл', 6), 'Туризм')
    report = {'year': 2025, 'revenue_rub': 1e10, 'operating_profit_rub': 5e8, 'net_profit_rub': 3e8,
              'borrowings_rub': 0, 'cash_rub': 0}
    est = ve.estimate({'ind': 'Туризм'}, report, comps, None)
    ps = [m for m in est['methods'] if m['metric'] == 'ps'][0]
    assert 'skipped' in ps and est['ok'] and est['confidence'] == 'низкая'


def test_no_button_without_target_or_report_or_for_banks():
    rep = {'year': 2025, 'revenue_rub': 1e9}
    assert ve.eligibility({'type': 'M&A'}, None, rep)
    assert ve.eligibility({'type': 'M&A'}, {'okved': '47.11'}, None)
    assert ve.eligibility({'type': 'M&A', 'ind': 'Банки'}, {'okved': '64.19'}, rep)
    assert ve.eligibility({'type': 'Временное управление'}, {'okved': '47.11'}, rep)
    assert ve.eligibility({'type': 'M&A'}, {'okved': '47.11'}, {'year': 2025, 'revenue_rub': 1e6})
    assert ve.eligibility({'type': 'M&A'}, {'okved': '47.11'}, rep) is None


def test_report_is_the_last_full_year_before_the_deal():
    reps = [{'year': 2024, 'revenue_rub': 1}, {'year': 2025, 'revenue_rub': 2}, {'year': 2026, 'revenue_rub': 3}]
    assert ve.report_before(reps, 2026)['year'] == 2025
    assert ve.report_before(reps, 2024) is None
