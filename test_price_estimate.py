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


DEAL = {'id': 'gx', 'title': 'Покупатель приобрел 80% компании', 'date': '2025-05-01', 'type': 'M&A',
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
    assert 'достоверно определить сумму сделки невозможно' in ' '.join(pe.template_text(s))
    assert not pe.can_estimate(s)


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
    sized = dict(DEAL, eco={'target_fin': 'Выручка за 2024 год — 500 млн ₽.'})  # без размера похожих нет (29.10.2026)
    s = pe.build(sized, None, _table([1.0, 2.0, 3.0]), deals, 'ИТ и интернет')
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
        # Считать нечем — честный отказ без кнопки (29 октября 2026); есть чем — шаблон.
        assert (r == {'available': False, 'reason': 'no_data'}) or (r['available'] and r['paragraphs'] and r['by'] == 'template')
        probe = client.get(f"/api/deals/{undisclosed['id']}/price-estimate", params={'probe': '1'}).json()
        assert probe == {'available': r['available']} or probe == {'available': False, 'reason': 'no_data'}
        assert client.get(f"/api/deals/{disclosed['id']}/price-estimate").json() == {
            'available': False, 'reason': 'price_known'}
        assert client.get('/api/deals/нет-такой/price-estimate').status_code == 404


def test_endpoint_says_no_data_when_nothing_can_be_computed(monkeypatch):
    """Velle, 29 октября 2026: четыре абзаца о том, почему оценку дать нельзя.
    Владелец: «где мы знаем, что оценку дать нельзя — вообще не будем даже
    кнопку добавлять». Пустая сводка — {available: False, reason: no_data},
    и то же на ?probe=1, которым страница решает, ставить ли кнопку."""
    import main
    base = json.loads((ROOT / 'static' / 'data' / 'deals_promoted.json').read_text(encoding='utf-8'))
    undisclosed = next(d for d in base['deals'] if pe.needs_estimate(d))
    empty = {'methods': [], 'comparables': [], 'experts': None, 'range_text': None, 'benchmarks': [],
             'stake': None, 'size_unknown': True, 'hidden_for_size': 0, 'title': 'x', 'year': 2026,
             'report_year': None, 'card_revenue_rub': None}
    monkeypatch.setattr(main.price_estimate, 'build', lambda *a, **k: empty)
    with TestClient(main.app) as client:
        assert client.get(f"/api/deals/{undisclosed['id']}/price-estimate").json() == {'available': False, 'reason': 'no_data'}
        assert client.get(f"/api/deals/{undisclosed['id']}/price-estimate", params={'probe': '1'}).json() == {'available': False, 'reason': 'no_data'}


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


def test_answer_drops_sentences_with_spelled_or_unknown_numbers():
    """Боевой сайт, 26 октября 2026: «от примерно трехсот миллионов до полтора с
    половиной миллиарда» вместо 1,6 млрд — числа словами проверку обходили."""
    facts = 'Итоговый диапазон: ≈ 300 млн ₽ – 1,6 млрд ₽ за 80%; выручка 562 млн ₽'
    text = ('Оценка — от примерно трехсот миллионов до полтора с половиной миллиарда рублей. '
            'Это 300 млн ₽ – 1,6 млрд ₽ за 80%.\n\nВыручка 562 млн ₽. Доля составит 14% рынка.')
    assert pe.clean_answer(text, facts) == ['Это 300 млн ₽ – 1,6 млрд ₽ за 80%.', 'Выручка 562 млн ₽.']
    assert pe.clean_answer('Компания стоит 9 млрд ₽.\n\nИ еще 7 млрд ₽.', facts) is None


def test_full_analysis_summary_separates_card_and_base():
    """«Разбор сделки»: модель видит карточку (не пересказывать) и базу (на ней разбор)."""
    import deal_analysis as da
    deal = {'id': 'd1', 'title': 'Покупатель купил завод', 'buyer': 'b', 'ind': 'Агро', 'date': '2026-05-01',
            'law': {'adv': [['Юрист покупателя', 'АЛРУД', '']]}}
    deals = {'d1': deal, 'd2': {'title': 'Покупатель купил склад', 'buyer': 'b', 'date': '2025-04-01', 'ind': 'Агро'}}
    text = da.facts_text(deal, deals, lambda cid: 'Покупатель' if cid == 'b' else None)
    card, base = text.split('ИЗ БАЗЫ КОМПАСА')
    assert 'АЛРУД' in card and 'АЛРУД' not in base
    assert 'Покупатель купил склад' in base and 'отрасли «Агро»' in base
    assert da.split_answer('Для покупателя. Раз.\n\nЧто может быть дальше. Два.')[1]['lead'] == 'Что может быть дальше.'


def test_full_analysis_without_the_model_says_so(monkeypatch):
    import main
    monkeypatch.delenv('YANDEX_API_KEY', raising=False)
    with TestClient(main.app) as client:
        assert client.get('/api/deals/g0b187624/analysis').json() == {'available': False, 'reason': 'model_unavailable'}


def test_full_analysis_drops_numbers_taken_from_the_card():
    """Цифра из карточки (доля продавца) в разборе — пересказ: предложение выпадает."""
    import deal_analysis as da, price_estimate as pe
    facts = 'КАРТОЧКА (читатель это уже видит):\nДоля продавца 12,3%\n\nИЗ БАЗЫ КОМПАСА (на карточке этого нет):\nВ отрасли 41 сделка'
    out = pe.clean_answer('Для продавца. Сохраняет 12,3%.\n\nРынок вокруг. В отрасли 41 сделка.', da.base_part(facts), 1)
    assert out == ['Рынок вокруг. В отрасли 41 сделка.']


def test_full_analysis_reads_the_internet_too():
    """Партнер, 28 октября 2026: «обязательно делать анализ во всем интернете».
    Выдача поиска идет в сводку отдельной частью после базы: числа из нее
    проходят проверку, издание называется по ссылке, абзац «В интернете.»
    — отдельный, источники — списком без повторов по сайту."""
    import deal_analysis as da, price_estimate as pe
    from yandex_search import SearchResult
    from datetime import datetime
    hits = [SearchResult('Завод продан', 'https://www.kommersant.ru/doc/1', 'Сумма 2 млрд ₽', datetime(2026, 10, 27)),
            SearchResult('Еще', 'https://kommersant.ru/doc/2', 'повтор', None)]
    block = da.web_block(hits)
    assert block.startswith('\n\nИЗ ИНТЕРНЕТА') and '(2026-10-27)' in block and 'Источник: https://www.kommersant.ru/doc/1' in block
    assert da.web_block([]) == ''
    assert da.sources(hits) == [{'title': 'Завод продан', 'url': 'https://www.kommersant.ru/doc/1', 'host': 'kommersant.ru'}]
    facts = 'КАРТОЧКА (читатель это уже видит):\nДоля 12,3%\n\nИЗ БАЗЫ КОМПАСА (на карточке этого нет):\nВ отрасли 41 сделка' + block
    assert 'Сумма 2 млрд ₽' in da.base_part(facts)
    out = pe.clean_answer('В интернете. Сумма 2 млрд ₽ (Коммерсантъ).\n\nЧто может быть дальше. Доля 12,3% уйдет.', da.base_part(facts), 1)
    assert out == ['В интернете. Сумма 2 млрд ₽ (Коммерсантъ).']
    assert [p['lead'] for p in da.split_answer('Для покупателя. Раз.\n\nВ интернете. Два.')] == ['Для покупателя.', 'В интернете.']


def test_external_multiples_file_names_a_source_and_a_year_for_every_number():
    """Владелец, 28 октября 2026 («давай делать»): внешние мультипликаторы —
    только с источником, сектором источника и годом; отрасли — из справочника
    сайта; мировой ориентир не входит в диапазон."""
    import re
    data = json.loads(pathlib.Path('static/data/sector_multiples_external.json').read_text(encoding='utf-8'))
    html = pathlib.Path('static/index.html').read_text(encoding='utf-8')
    industries = set(json.loads(re.search(r'const INDUSTRIES = (\[.*?\]);', html).group(1)))
    for key, src in data['sources'].items():
        assert src['kind'] in ('deals', 'exchange', 'global') and src['url'].startswith('https://') and src['short'], key
    assert 'deals' in {s['kind'] for s in data['sources'].values()}
    for ind, recs in data['industries'].items():
        assert ind in industries, ind
        for r in recs:
            assert r['source'] in data['sources'] and r['metric'] in pe.EXT_BASE, (ind, r)
            assert float(r['value']) > 0 and 2022 <= int(r['year']) <= 2030 and r['label'], (ind, r)
    assert 'ё' not in json.dumps(data, ensure_ascii=False)


def test_external_multiples_join_the_range_and_global_stays_a_benchmark():
    ext = {'sources': {'b1': {'short': 'Б1', 'name': 'Б1', 'url': 'https://b1.ru/x', 'kind': 'deals'},
                       'dam': {'short': 'Дамодаран', 'name': 'NYU', 'url': 'https://x.edu', 'kind': 'global'}},
           'industries': {'Агро': [{'metric': 'ev_sales', 'value': 2.0, 'year': 2024, 'source': 'b1', 'label': 'Сельское хозяйство'},
                                   {'metric': 'ev_ebitda', 'value': 10.6, 'year': 2026, 'source': 'dam', 'label': 'Farming'}]}}
    rep = {'year': 2024, 'revenue_rub': 500e6, 'assets_rub': 1e9, 'borrowings_rub': 100e6, 'cash_rub': 0, 'lines': {}}
    s = pe.build(DEAL, rep, _table([1.0, 1.0, 1.0], 'Агро'), {}, 'Агро', external=ext)
    labels = [(m['label'], m.get('external', {}).get('source')) for m in s['methods']]
    assert ('P/S', None) in labels and ('EV/Sales', 'Б1') in labels
    ev = next(m for m in s['methods'] if m.get('external'))
    assert ev['full_rub'] == 500e6 * 2.0 - 100e6  # EV минус чистый долг
    assert s['range'] == (pe._round2(500e6 * 0.8), pe._round2(ev['stake_rub']))  # биржевой и сделочный — в диапазоне
    assert s['benchmarks'][0]['value'] == 10.6 and all(not m.get('external') or m['external']['kind'] != 'global' for m in s['methods'])
    text = pe.facts_text(s)
    assert 'по данным Б1 (цены сделок, сектор «Сельское хозяйство», 2024 год)' in text
    assert 'Мировой ориентир, Дамодаран' in text and 'в диапазон не входит' in text
    assert 'отраслевые ориентиры из открытых исследований (Б1)' in ' '.join(pe.template_text(s))
    # без отчетности и без записей по отрасли — ничего
    assert pe.external_methods('Агро', None, None, 80, ext) == ([], [{'metric': 'ev_ebitda', 'label': 'Farming', 'value': 10.6,
        'source': 'Дамодаран', 'name': 'NYU', 'url': 'https://x.edu', 'kind': 'global', 'year': 2026, 'note': None}])
    assert pe.external_methods('Уголь', rep, None, 80, ext) == ([], [])


def test_card_revenue_feeds_ps_and_comparables_keep_the_scale():
    """5Yes! (27.10.2026): отчетности нет, но карточка называет выручку 521 млн ₽ —
    P/S считается по ней; Росспиртпром за 8,3 млрд ₽ в «похожие» не попадает
    («они вообще несопоставимы»), а без размера сравнивать не с чем."""
    deals = {
        'small': {'title': 'Кофейни', 'type': 'M&A', 'ind': 'Пищепром и напитки', 'date': '2025-01-01',
                  'facts': {'price': {'meaning': 'disclosed', 'value_rub': 200e6}, 'nature': {}}},
        'huge': {'title': 'Росспиртпром', 'type': 'M&A', 'ind': 'Пищепром и напитки', 'date': '2024-01-01',
                 'facts': {'price': {'meaning': 'disclosed', 'value_rub': 8.3e9}, 'nature': {}}},
    }
    deal = dict(DEAL, ind='Пищепром и напитки', eco={'target_fin': 'По данным Mergers.ru, выручка за 2025 год — 521 млн ₽.'})
    s = pe.build(deal, None, _table([1.0, 2.0, 3.0]), deals, 'Пищепром и напитки')
    assert s['card_revenue_rub'] == 521e6 and s['methods'][0]['base_rub'] == 521e6 and s['range_text']
    assert [c['id'] for c in s['comparables']] == ['small']
    assert 'по данным источника' in pe.facts_text(s)
    blind = pe.build(dict(DEAL, ind='Пищепром и напитки'), None, _table([1.0, 2.0, 3.0]), deals, 'Пищепром и напитки')
    # 29 октября 2026 (Velle): без размера похожих сделок нет вовсе — «нефтебаза с
    # двумя заправками рядом с Роснефтью… смешно и глупо для разбирающихся людей».
    assert blind['size_unknown'] and blind['comparables'] == [] and not blind['range_text']
    assert any('не приводим' in t for t in pe.template_text(blind)) and 'не приводить' in pe.facts_text(blind)
