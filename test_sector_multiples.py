# -*- coding: utf-8 -*-
"""Таблица «Мультипликаторы по отраслям» (19 октября 2026): расчет по одной
сделке, ячейки «отрасль × год», строка профиля «Операционная прибыль (оценка
по ФНС)» и маршрут ассистента «какой мультипликатор в …».

Запуск: python3 -m pytest test_sector_multiples.py -q
"""
import pytest

import assistant_retrieval as ar
import company_finance as cf
import deal_multiples as dm


def _report(**kw):
    """Отчет ФНС купленной компании за 2024 год, рубли."""
    base = {'year': 2024, 'revenue_rub': 10e9, 'operating_profit_rub': 2e9, 'net_profit_rub': 1e9,
            'equity_rub': 5e9, 'borrowings_rub': 3e9, 'cash_rub': 1e9, 'assets_rub': 20e9, 'lines': {}}
    base.update(kw)
    return base


def test_sector_values_units_and_net_debt():
    """Цена за 100% 10 млрд ₽: EV = цена + чистый долг (3 − 1 = 2 млрд ₽)."""
    v = dm.sector_values(10e9, 'package', _report(), 2025)
    assert v['ev_op']['value'] == 6.0 and v['ev_op']['status'] == 'ok'     # (10 + 2) / 2
    assert v['pe']['value'] == 10.0 and v['ps']['value'] == 1.0 and v['pbv']['value'] == 2.0
    assert all(x['denominator_year'] == 2024 and x['source'] == 'ФНС' for x in v.values())
    # цена «с учетом долга» уже EV: долг к ней не прибавляется, а для P/E вычитается
    ev = dm.sector_values(12e9, 'ev', _report(), 2025)
    assert ev['ev_op']['value'] == 6.0 and ev['pe']['value'] == 10.0


def test_sector_values_loss_is_not_applicable_and_outlier_is_flagged_not_hidden():
    v = dm.sector_values(10e9, 'package', _report(operating_profit_rub=-5e8, net_profit_rub=0.0), 2025)
    assert v['ev_op']['status'] == 'not_applicable' and v['ev_op']['value'] is None
    assert v['pe']['status'] == 'not_applicable'
    big = dm.sector_values(10e9, 'package', _report(operating_profit_rub=2e6), 2025)
    assert big['ev_op']['status'] == 'outlier' and big['ev_op']['value'] == 6000.0


def test_sector_values_need_the_last_full_year_before_the_deal():
    same_year = dm.sector_values(10e9, 'package', _report(year=2025), 2025)
    assert all(x['status'] == 'no_data' for x in same_year.values())
    too_old = dm.sector_values(10e9, 'package', _report(year=2021), 2025)
    assert all(x['status'] == 'no_data' for x in too_old.values())
    assert dm.sector_values(10e9, 'package', _report(year=2023), 2025)['ps']['status'] == 'ok'


def test_operating_profit_is_computed_from_lines_when_2200_is_missing():
    """Упрощенная форма: строки 2200 нет — выручка минус расходы."""
    lines = {'2110': 1e9, '2120': 7e8, '2220': 1e8}
    v = dm.sector_values(1e9, 'package', _report(operating_profit_rub=None, borrowings_rub=None,
                                                  cash_rub=None, lines=lines), 2025)
    assert v['ev_op']['op_basis'] == 'computed' and v['ev_op']['denominator_rub'] == 2e8
    assert v['ev_op']['value'] == 5.0     # займов в балансе нет — EV равен цене


def _sector_deal(**facts_kw):
    f = {'price': {'value_rub': 4.9e9, 'basis': 'verified', 'scope': 'package', 'meaning': 'disclosed'},
         'stake': {'value': 49.0, 'basis': 'verified'},
         'target': {'company_id': 't1', 'confirmed': True}}
    f.update(facts_kw)
    return {'id': 'd1', 'title': 'Сделка', 'date': '2025-03-01', 'target': 't1', 'facts': f}


def test_sector_row_scales_the_stake_and_keeps_the_fx_note():
    """Цена пакета 49% пересчитывается на 100%; цена в долларах уже в рублях
    по курсу ЦБ (facts), а исходная сумма и курс едут в строку."""
    d = _sector_deal(price={'value_rub': 4.9e9, 'basis': 'verified', 'scope': 'package', 'currency': 'USD',
                            'amount': 50e6, 'fx_rate': 98.0, 'fx_date': '2025-03-01', 'fx_method': 'day'})
    r = dm.sector_row(d, 'verified', _report(), 'ООО Т', None, 'ИТ и интернет')
    assert r['price_full_rub'] == pytest.approx(10e9) and r['price_basis'] == 'scaled'
    assert r['metrics']['ps']['value'] == 1.0
    assert r['price_fx']['currency'] == 'USD' and r['price_fx']['fx_rate'] == 98.0


def test_bank_gets_only_pbv_from_the_bank_of_russia_capital():
    entry = {'as_of_balance': '2025-07-01', 'equity_rub': 9e9, 'equity_rub_prior_year': 8e9, 'legal_name': 'Банк'}
    d = _sector_deal(target={'company_id': 't1', 'bank': True}, stake={'value': 100.0, 'basis': 'verified'})
    r = dm.sector_row(d, 'computed', None, None, entry, 'Банки')
    assert r['metrics']['pbv']['value'] == round(4.9e9 / 8e9, 2)
    assert r['metrics']['pbv']['source'] == 'Банк России'
    assert r['metrics']['pbv']['denominator_date'] == '2025-01-01'
    assert all(r['metrics'][m]['status'] == 'no_data' for m in ('ev_op', 'pe', 'ps'))
    # капитала на начало года сделки в файле нет — нет и P/BV
    assert dm.bank_equity_for_year(entry, 2024) is None


def test_bank_target_passes_the_same_admission_except_the_bank_check():
    """Для P/BV «предмет — банк» не отказ; остальные правила те же."""
    d = _sector_deal(target={'company_id': 't1', 'bank': True},
                     nature={'control_change': True, 'control_change_basis': 'rule'},
                     date={'value': '2025-03-01', 'basis': 'rule'})
    d.update(type='M&A', status='Закрыта')
    assert dm.sector_admission(d)[0] == 'computed'
    d['status'] = 'Не состоялась'
    assert dm.sector_admission(d) == (None, 'failed')


def _row(i, ps, status='ok', ind='Ритейл', year=2024, conf='verified'):
    m = {k: {'status': 'no_data', 'value': None} for k in dm.SECTOR_METRICS}
    m['ps'] = {'status': status, 'value': ps, 'denominator_year': year - 1}
    return {'id': f'd{i}', 'title': f'Сделка {i}', 'year': year, 'industry': ind, 'confidence': conf,
            'metrics': m}


def _table():
    rows = [_row(1, 1.0), _row(2, 2.0), _row(3, 3.0, conf='computed'), _row(4, 99.0, 'outlier'),
            _row(5, 5.0, ind='ИТ и интернет', year=2025)]
    return dm.sector_table(rows, 100)


def test_sector_cells_need_three_deals_and_leave_outliers_out_of_the_median():
    t = _table()
    cell = dm.find_cell(t, 'ps', 'Ритейл', 2024)
    assert cell['count'] == 3 and cell['median'] == 2.0 and cell['outlier_ids'] == ['d4']
    assert dm.find_cell(t, 'ps', 'ИТ и интернет', 2025)['median'] is None   # одна сделка — прочерк
    assert dm.find_cell(t, 'ps', None, None)['count'] == 4                    # «Все отрасли, все годы»
    assert dm.find_cell(t, 'ps', 'Ритейл', 2024, only_verified=True)['median'] is None
    assert t['with_multiple_total'] == 5 and t['by_metric']['ps'] == 5


def test_operating_profit_estimate_row_names_its_basis():
    """Строка профиля: готовая 2200, без нее — выручка минус расходы."""
    base = {"revenue_rub": 1e10, "operating_profit_rub": 2e9, "full_lines": []}
    m = {x["key"]: x for x in cf.derive(base)["metrics"]}["operating_profit_estimate"]
    assert m["value_rub"] == 2e9 and m["primary"] and "не EBITDA" in m["how"]
    simplified = {"revenue_rub": 1e9, "full_lines": [{"title": "ОФР", "rows": [
        {"code": "2110", "value_rub": 1_000_000_000}, {"code": "2120", "value_rub": 800_000_000}]}]}
    m2 = {x["key"]: x for x in cf.derive(simplified)["metrics"]}["operating_profit_estimate"]
    assert m2["value_rub"] == 2e8 and "из строк отчета" in m2["how"]
    assert cf.operating_profit_estimate(None, {"2110": 1e9}) == (None, None)   # без расходов не считаем


@pytest.fixture
def provider(monkeypatch):
    table = _table()
    monkeypatch.setattr(ar, "SECTOR_MULTIPLES_PROVIDER", lambda: table)
    return table


def test_assistant_answers_a_typical_multiple_from_the_table(provider):
    idx = ar.get_index()
    r = ar.retrieve("Какой P/S в ритейле за 2024?", idx=idx)
    assert r.intent == "sector_multiple"
    assert "медиана ×2" in r.answer and "по 3 сделкам" in r.answer and "оценка" in r.answer
    assert "выброс" in r.answer and "#/analytics" in r.answer
    r = ar.retrieve("средний EV/EBIT в ИТ за 2025", idx=idx)
    assert r.intent == "sector_multiple" and "EV / операционная прибыль" in r.answer
    assert "не EV/EBITDA" in r.answer
    # список мультипликаторов из текста карточек — прежний маршрут
    assert ar.retrieve("Какие мультипликаторы были в сделках с ресторанами и кофейнями?", idx=idx).intent != "sector_multiple"


def test_assistant_metric_words(monkeypatch):
    monkeypatch.setattr(ar, "SECTOR_MULTIPLES_PROVIDER", None)   # main.py, если импортирован, ставит свое
    assert ar.sector_metric("средний P/E в ИТ") == "pe"
    assert ar.sector_metric("какой P/BV у банков") == "pbv"
    assert ar.sector_metric("мультипликатор к выручке в ритейле") == "ps"
    assert ar.sector_metric("какой мультипликатор в ритейле") == "ev_op"
    assert ar.route("Какой мультипликатор в ритейле?").kind != "sector_multiple"   # без таблицы — прежний путь
