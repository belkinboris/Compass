"""«Анализ Компаса» — оценка сделки без раскрытой цены (price_estimate.py).
Владелец 26 октября 2026: «если не раскрыта, пусть включается компас и
анализирует, сколько могла бы стоить эта доля»."""
import json
import pathlib

from fastapi.testclient import TestClient

import price_estimate as pe

ROOT = pathlib.Path(__file__).resolve().parent


def _table(ps_values, industry='ИТ и интернет'):
    rows = [{'id': f'r{i}', 'industry': industry, 'year': 2024,
             'metrics': {'ps': {'status': 'ok', 'value': v}, 'pe': {'status': 'no_data'},
                         'ev_op': {'status': 'no_data'}, 'pbv': {'status': 'no_data'}}}
            for i, v in enumerate(ps_values)]
    med = sorted(ps_values)[len(ps_values) // 2]
    cell = {'industry': industry, 'year': 'all', 'count': len(ps_values), 'median': med,
            'ids': [r['id'] for r in rows], 'outlier_ids': []}
    allc = dict(cell, industry='Все отрасли')
    return {'rows': rows, 'cells': {'all': {'ps': [cell, allc], 'pe': [], 'ev_op': []}}}


DEAL = {'id': 'gx', 'title': 'Покупатель приобрёл 80% компании', 'date': '2025-05-01', 'type': 'M&A',
        'ind': 'ИТ и интернет', 'sum': 'Не раскрыта', 'eco': {'val': '—'},
        'facts': {'price': {'meaning': 'undisclosed'}}}


def test_estimate_multiplies_revenue_by_the_sector_median_and_the_stake():
    s = pe.build(DEAL, {'year': 2024, 'revenue_rub': 500e6, 'lines': {}}, _table([1.0, 2.0, 3.0]), {}, 'ИТ и интернет')
    m = s['methods'][0]
    assert m['metric'] == 'ps' and m['full_rub'] == 1e9 and m['stake_rub'] == 800e6
    assert s['stake'] == 80
    assert s['range_text'].endswith('за 80%')


def test_no_report_means_no_range_and_says_why():
    s = pe.build(DEAL, None, _table([1.0, 2.0, 3.0]), {}, 'ИТ и интернет')
    assert s['range'] is None and s['methods'] == []
    assert 'Для оценки не хватает данных' in ' '.join(pe.template_text(s))


def test_disclosed_price_and_auctions_get_no_button():
    assert pe.needs_estimate(DEAL)
    assert not pe.needs_estimate(dict(DEAL, facts={'price': {'meaning': 'disclosed'}}))
    assert not pe.needs_estimate(dict(DEAL, type='Продажа с торгов'))


def test_model_answer_with_a_number_not_in_the_summary_is_rejected():
    facts = 'Итоговый диапазон Компаса: ≈ 0,8–1,2 млрд ₽ за 80%; выручка 500 млн ₽ × 2×'
    assert pe.numbers_ok('Около 0,8–1,2 млрд ₽ за 80% по выручке 500 млн ₽ в 2024 году.', facts)
    assert not pe.numbers_ok('Компания стоит 3,5 млрд ₽.', facts)


def test_comparables_are_purchases_not_rounds():
    deals = {
        'a': {'title': 'Покупка', 'type': 'M&A', 'ind': 'ИТ и интернет', 'date': '2024-01-01',
              'facts': {'price': {'meaning': 'disclosed', 'value_rub': 1e9}, 'nature': {}}},
        'b': {'title': 'Раунд', 'type': 'Инвестиция', 'ind': 'ИТ и интернет', 'date': '2024-01-01',
              'facts': {'price': {'meaning': 'disclosed', 'value_rub': 1e9}, 'nature': {'cash_in': True}}},
    }
    s = pe.build(DEAL, None, _table([1.0, 2.0, 3.0]), deals, 'ИТ и интернет')
    assert [c['id'] for c in s['comparables']] == ['a']


def test_money_has_two_significant_digits():
    assert pe.money(1_234_567_890) == '1,2 млрд ₽'
    assert pe.money(77_000_000) == '77 млн ₽'
    assert pe.deals_word(4) == '4 сделки' and pe.deals_word(29) == '29 сделок' and pe.deals_word(21) == '21 сделка'


def test_endpoint_answers_without_the_model(monkeypatch):
    import main
    monkeypatch.delenv('YANDEX_API_KEY', raising=False)
    base = json.loads((ROOT / 'static' / 'data' / 'deals_promoted.json').read_text(encoding='utf-8'))
    undisclosed = next(d for d in base['deals'] if pe.needs_estimate(d))
    disclosed = next(d for d in base['deals'] if not pe.needs_estimate(d) and d.get('type') == 'M&A')
    with TestClient(main.app) as client:
        r = client.get(f"/api/deals/{undisclosed['id']}/price-estimate").json()
        assert r['available'] and r['paragraphs'] and r['by'] == 'template'
        assert client.get(f"/api/deals/{disclosed['id']}/price-estimate").json() == {
            'available': False, 'reason': 'price_known'}
        assert client.get('/api/deals/нет-такой/price-estimate').status_code == 404


def test_context_summary_lists_the_buyers_other_deals():
    """«Анализ ассистента» у «Контекста» видит другие сделки сторон из базы."""
    import context_analysis as ca
    deal = {'id': 'd1', 'title': 'Покупатель купил завод', 'buyer': 'b', 'eco': {'context': 'Завод в Дмитрове.'}}
    deals = {'d1': deal, 'd2': {'title': 'Покупатель купил склад', 'buyer': 'b', 'date': '2024-04-01'},
             'd3': {'title': 'Чужая сделка', 'buyer': 'x'}}
    text = ca.facts_text(deal, deals, lambda cid: 'Покупатель' if cid == 'b' else None)
    assert 'Покупатель купил склад' in text and 'Чужая сделка' not in text
    assert ca.split_answer('Что это значит. Раз.\n\nМасштаб. Два.')[1] == {'lead': 'Масштаб.', 'text': 'Два.'}


def test_context_analysis_without_the_model_says_so(monkeypatch):
    import main
    monkeypatch.delenv('YANDEX_API_KEY', raising=False)
    base = json.loads((ROOT / 'static' / 'data' / 'deals_promoted.json').read_text(encoding='utf-8'))
    d = next(d for d in base['deals'] if str((d.get('eco') or {}).get('context') or '').strip() not in ('', '—'))
    with TestClient(main.app) as client:
        assert client.get(f"/api/deals/{d['id']}/context-analysis").json() == {
            'available': False, 'reason': 'model_unavailable'}
