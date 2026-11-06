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


EMPTY = {'rows': [], 'cells': {'all': {'ps': [], 'pe': [], 'ev_op': []}}}

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
    # есть российские методы — мирового ориентира в сводке нет вовсе (владелец, 29 октября 2026)
    assert 'Дамодаран' not in text and s['global_methods'] == [] and s['range_kind'] == 'estimate'
    assert 'отраслевые ориентиры из открытых исследований (Б1)' in ' '.join(pe.template_text(s))
    # без отчетности и без записей по отрасли — ничего
    assert pe.external_methods('Агро', None, None, 80, ext) == ([], [{'metric': 'ev_ebitda', 'label': 'Farming', 'value': 10.6,
        'source': 'Дамодаран', 'name': 'NYU', 'url': 'https://x.edu', 'kind': 'global', 'year': 2026, 'note': None}], [])
    assert pe.external_methods('Уголь', rep, None, 80, ext) == ([], [], [])


def test_global_only_gives_upper_bound_and_equity_gives_floor():
    """Четыре случая (владелец, 29 октября 2026). Российских методов нет:
    Дамодаран по EV/EBIT — верхняя граница «до X»; без него и без прибыли —
    балансовый капитал как нижняя граница «не ниже X»; без всего — can_estimate
    False, кнопки на карточке нет."""
    ext = {'sources': {'dam': {'short': 'Дамодаран', 'name': 'NYU', 'url': 'https://x.edu', 'kind': 'global'}},
           'industries': {'Агро': [{'metric': 'ev_ebit', 'value': 12.0, 'year': 2026, 'source': 'dam', 'label': 'Farming'},
                                   {'metric': 'ev_ebitda', 'value': 10.6, 'year': 2026, 'source': 'dam', 'label': 'Farming'}]}}
    rep = {'year': 2024, 'revenue_rub': 500e6, 'assets_rub': 1e9, 'borrowings_rub': 0, 'cash_rub': 0,
           'operating_profit_rub': 50e6, 'equity_rub': 300e6, 'lines': {}}
    s = pe.build(DEAL, rep, EMPTY, {}, 'Агро', external=ext)
    assert s['methods'] == [] and [m['metric'] for m in s['global_methods']] == ['ev_ebit']
    assert s['range_kind'] == 'upper' and s['range_text'].startswith('до ') and 'верхняя граница' in s['range_text']
    assert s['floor']['equity_rub'] == 300e6 and s['floor']['stake_rub'] == 300e6 * 0.8
    facts = pe.facts_text(s)
    assert 'Мировой ориентир, Дамодаран' in facts and 'EV/EBIT' in facts and 'Балансовый капитал' in facts
    assert 'Верхняя граница по мировому ориентиру' in facts
    tpl = ' '.join(pe.template_text(s))
    assert 'Российских ориентиров по этой отрасли нет' in tpl and 'верхнюю границу' in tpl
    assert pe.can_estimate(s) and 'ё' not in facts + tpl
    # прибыли нет — остается только баланс
    rep2 = dict(rep, operating_profit_rub=-5e6, net_profit_rub=-5e6)
    s2 = pe.build(DEAL, rep2, EMPTY, {}, 'Агро', external=ext)
    assert s2['global_methods'] == [] and s2['range_kind'] == 'floor'
    assert s2['range_text'] == f'не ниже {pe.money(300e6 * 0.8)} за 80%'
    assert 'нижняя граница' in ' '.join(pe.template_text(s2)) and pe.can_estimate(s2)
    # ни отчетности, ни сделок — считать нечем
    s3 = pe.build(DEAL, None, EMPTY, {}, 'Агро', external=ext)
    assert not pe.can_estimate(s3) and s3['range_text'] is None
    assert pe.template_text(s3) == ['Исходя из публичных данных, достоверно определить сумму сделки невозможно.']


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


# «Медскан» (владелец, 6 ноября 2026): «по оценке написано где-то 30 миллиардов, а
# если нажать "рассчитать", то там получается чуть ли не 1 млрд… ориентируйся на
# оценочное число тоже». Отчетность — холдингового АО: выручка 341 млн ₽, капитал
# 8,1 млрд ₽; выручка группы в карточке — 28 млрд ₽; оценка BGP Capital 31–36 млрд ₽.
MEDSCAN = {'id': 'gm', 'title': 'Газпромбанк может стать акционером сети клиник «Медскан»', 'date': '2025-09-01',
           'type': 'Инвестиция', 'ind': 'Здравоохранение', 'sum': '31–36 млрд ₽ (по оценке)',
           'eco': {'val': 'Иван Пешков оценивает справедливую стоимость компании в 31–36 млрд ₽ (8xEBITDA).',
                   'target_fin': 'Выручка группы «Медскан» вместе с лабораториями за 2024 год — 28 млрд ₽.'},
           'facts': {'price': {'meaning': 'range'}}}
MEDSCAN_REPORT = {'year': 2024, 'revenue_rub': 341e6, 'net_profit_rub': -250e6, 'equity_rub': 8.1e9,
                  'assets_rub': 20e9, 'borrowings_rub': 0, 'cash_rub': 0, 'lines': {}}


def test_range_is_never_below_the_equity_floor():
    """Правило 1: метод, который дает за 100% меньше балансового капитала, в
    итог не входит (база не та); нижний конец диапазона не ниже капитала;
    диапазон целиком ниже капитала не показывается — остается «не ниже»."""
    rep = {'year': 2024, 'revenue_rub': 500e6, 'equity_rub': 900e6, 'lines': {}}
    s = pe.build(DEAL, rep, _table([1.0, 2.0, 3.0]), {}, 'ИТ и интернет', external={})
    # P/S 2× дает 1 млрд ₽ за 100% — выше капитала 900 млн ₽, метод в итоге;
    # нижний квартиль 1,5× дал бы 600 млн ₽ за 80% — меньше капитала на долю
    # (720 млн ₽), нижний конец поднят до него
    assert not s['methods'][0].get('unreliable') and s['floor_cut']
    assert s['range'][0] == pe._round2(900e6 * 0.8) and s['range'][0] >= s['floor']['stake_rub']
    assert 'Нижний конец диапазона поднят до балансового капитала' in pe.facts_text(s)
    low = pe.build(DEAL, dict(rep, equity_rub=5e9), _table([1.0, 2.0, 3.0]), {}, 'ИТ и интернет', external={})
    assert low['methods'][0]['unreliable'] == 'below_floor' and low['range'] is None
    assert low['range_kind'] == 'floor' and low['range_text'].startswith('не ниже ')
    facts, tpl = pe.facts_text(low), ' '.join(pe.template_text(low))
    assert 'в итог не входит: дает меньше балансового капитала' in facts
    assert 'дают меньше балансового капитала' in tpl and 'нет российских ориентиров' not in tpl
    assert pe.numbers_ok(tpl, facts) and 'ё' not in facts + tpl


def test_holding_report_is_not_the_business_and_card_revenue_takes_over():
    """Правило 3 на «Медскане»: холдинг по ОКВЭД и выручка группы из карточки в
    82 раза больше выручки юрлица — методы по отчетности не в итоге; P/S
    считается по выручке группы; похожие сделки — по ее размеру."""
    deals = {'small': {'title': 'Клиника', 'type': 'M&A', 'ind': 'Здравоохранение', 'date': '2025-01-01',
                       'facts': {'price': {'meaning': 'disclosed', 'value_rub': 300e6}, 'nature': {}}},
             'big': {'title': 'Сеть клиник', 'type': 'M&A', 'ind': 'Здравоохранение', 'date': '2025-01-01',
                     'facts': {'price': {'meaning': 'disclosed', 'value_rub': 30e9}, 'nature': {}}}}
    rep = dict(MEDSCAN_REPORT, okved_code='64.20')
    s = pe.build(MEDSCAN, rep, _table([0.5, 0.6, 1.75, 3.2, 4.0], 'Здравоохранение'), deals, 'Здравоохранение')
    assert s['report_mismatch']['signals'] == ['holding', 'card_revenue']
    by_base = {m['base_rub']: m for m in s['methods']}
    assert by_base[341e6]['unreliable'] == 'report_scale' and not by_base[28e9].get('unreliable')
    assert s['range_kind'] == 'estimate' and s['range'][0] >= 8.1e9
    assert s['range'][0] <= 31e9 and s['range'][1] >= 36e9  # оценка источников внутри
    assert not s['source_value']['divergent'] and s['source_value']['ratio'] == 1.0
    assert [c['id'] for c in s['comparables']] == ['big']
    facts, tpl = pe.facts_text(s), pe.template_text(s)
    assert 'холдинговая компания' in facts and 'в 82 раза больше' in facts
    assert '31–36 млрд ₽, в пределах расчета Компаса' in tpl[0]
    assert 'выручку бизнеса по данным источника — 28 млрд ₽' in tpl[1]
    assert pe.numbers_ok(' '.join(tpl), facts) and 'ё' not in facts + ' '.join(tpl)
    # без ОКВЭД холдинга хватает одной выручки группы
    assert pe.build(MEDSCAN, MEDSCAN_REPORT, _table([0.5, 0.6, 1.75, 3.2, 4.0], 'Здравоохранение'), {}, 'Здравоохранение'
                    )['report_mismatch']['signals'] == ['card_revenue']


def test_source_estimate_alone_flags_the_wrong_company():
    """Выручки группы в карточке нет, но оценка 31–36 млрд ₽ при верхнем
    квартиле P/S 3,2 требует выручки от 9,7 млрд ₽ — в 28 раз больше 341 млн ₽.
    Расчет по такой отчетности не годится; итог — оценка источников, баланс
    рядом."""
    deal = dict(MEDSCAN, eco={'val': MEDSCAN['eco']['val']})
    s = pe.build(deal, MEDSCAN_REPORT, _table([0.5, 0.6, 1.75, 3.2, 4.0], 'Здравоохранение'), {}, 'Здравоохранение')
    assert s['report_mismatch']['signals'] == ['source_scale']
    assert all(m.get('unreliable') for m in s['methods']) and s['range'] is None
    assert s['range_kind'] == 'sources' and s['range_text'] == '≈ 31–36 млрд ₽ по оценке источников'
    tpl = pe.template_text(s)
    assert tpl[0].startswith('Опираемся на оценку из открытых источников: 31–36 млрд ₽')
    assert 'одной компании, а не всего бизнеса' in tpl[0] and '8,1 млрд ₽' in tpl[1]
    facts = pe.facts_text(s)
    assert 'Итог — оценка из открытых источников' in facts
    assert pe.numbers_ok(' '.join(tpl), facts) and pe.can_estimate(s)


def test_source_estimate_far_from_the_range_is_named_first_with_a_reason():
    """Правило 2: оценка источников и расчет расходятся больше чем в 3 раза —
    шаблон начинает с оценки источников, говорит, во сколько раз, и вероятную
    причину; модели то же велит сводка. Число раз есть в сводке —
    numbers_ok его пропускает, выдуманное — нет."""
    deal = dict(DEAL, sum='Не раскрыта', eco={'val': 'Аналитик оценивает компанию в 10 млрд ₽.'})
    rep = {'year': 2024, 'revenue_rub': 500e6, 'lines': {}}
    s = pe.build(deal, rep, _table([1.0, 2.0, 3.0]), {}, 'ИТ и интернет', external={})
    src = s['source_value']
    assert src['divergent'] and src['direction'] == 'higher' and src['text'] == '10 млрд ₽'
    # доля 80%: ближняя база — пересчет диапазона на 100%
    assert round(src['ratio'], 6) == round(10e9 / (s['range'][1] / 0.8), 6)
    tpl = pe.template_text(s)
    assert tpl[0].startswith('Оценка из открытых источников — 10 млрд ₽, а расчет Компаса дает')
    assert 'Вероятная причина:' in tpl[0]
    facts = pe.facts_text(s)
    assert 'Расхождение с оценкой источников' in facts and pe.times(src['ratio']) in facts
    assert pe.numbers_ok(' '.join(tpl), facts)
    assert not pe.numbers_ok('Оценка расходится с расчетом в 40 раз.', facts)
    assert 'Расхождение с оценкой источников' in pe.SYSTEM
    assert pe.source_line(s).startswith('10 млрд ₽, ' + pe.times(src['ratio']) + ' выше')


def test_source_value_reads_estimates_not_debts_or_damages():
    """Оценка — из суммы «X (по оценке)», иначе из предложения, где кто-то
    оценивает бизнес; ущерб, долг, кадастр, капитализация, активы, цена акции —
    не оценка цены."""
    assert pe.source_value({'sum': '31–36 млрд ₽ (по оценке)'})['lo'] == 31e9
    assert pe.source_value({'sum': 'Не раскрыта', 'eco': {'val': 'Эксперты оценили сделку в 1 млрд ₽.'}})['hi'] == 1e9
    for val in ('Ущерб по оценке прокуратуры — 17,4 млрд ₽.', 'Кадастровая стоимость оценена в 1 млрд ₽.',
                'Капитализация после IPO оценивается в 69,9 млрд ₽.', 'Активы компании оценены в 135 млрд ₽.',
                'Долг комбината оценивают в 5 млрд ₽.', 'Сделка позволила банку переоценить долю в 9 млрд ₽.',
                'Выручка — 2 млрд ₽.'):
        assert pe.source_value({'sum': 'Не раскрыта', 'eco': {'val': val}}) is None, val
    assert pe.times(3) == 'в 3 раза' and pe.times(30) == 'в 30 раз' and pe.times(22) == 'в 22 раза'
    assert pe.times(12) == 'в 12 раз'
    # «900 млн – 2 млрд ₽» — диапазон целиком, а не «2 млрд ₽» (элеватор gafc80ee1)
    assert pe.source_value({'sum': 'Экспертная оценка; 900 млн – 2 млрд ₽ (по оценке)'})['text'] == '900 млн ₽ – 2 млрд ₽'


def test_card_revenue_of_the_buyer_is_not_the_target_size():
    """«Гранд Премьер» (gd66af0f7, 6 ноября 2026): «рост выручки… до 8,48 млрд ₽…
    относится к покупателю Nelt» — не выручка покупаемой компании; берется
    выручка холдинга 1,22 млрд ₽, отчетность юрлица (425 млн ₽) — не «не та»."""
    deal = dict(DEAL, eco={'target_fin': 'По данным СПАРК, совокупная выручка всех компаний холдинга Moloko Group '
                                         'по итогам 2024 года сократилась примерно на 3,7%, до 1,22 млрд ₽. Рост выручки '
                                         'на 36,25%, до 8,48 млрд ₽, относится к покупателю Nelt.'})
    assert pe.revenue_from_card(deal) == 1.22e9
    s = pe.build(deal, {'year': 2024, 'revenue_rub': 425e6, 'lines': {}}, _table([1.0, 2.0, 3.0]), {}, 'ИТ и интернет',
                 external={})
    assert s['report_mismatch'] is None and not s['card_base']
    # элеватор: оценка 2 млрд ₽ при выручке 11 млн ₽ — отчетность «не та», но
    # карточка называет ту же выручку — подставлять ее вместо отчетности нечего
    elev = dict(DEAL, sum='900 млн – 2 млрд ₽ (по оценке)', eco={'target_fin': 'Выручка выросла до 11,4 млн ₽.'})
    s2 = pe.build(elev, {'year': 2024, 'revenue_rub': 11.4e6, 'lines': {}}, _table([1.0, 2.0, 3.0]), {},
                  'ИТ и интернет', external={})
    assert s2['report_mismatch']['signals'] == ['source_scale'] and not s2['card_base']
    assert s2['range_kind'] == 'sources' and s2['range_text'] == '≈ 900 млн ₽ – 2 млрд ₽ по оценке источников'


def test_estimate_panel_has_no_tag_and_shows_the_source_estimate():
    """Подпись «расчет, а не цена сделки» убрана (владелец, 6 ноября 2026: «это
    и так понятно»), стили .pe-tag — тоже; оценка источников — сразу под итогом."""
    html = (ROOT / 'static' / 'index.html').read_text(encoding='utf-8')
    assert 'pe-tag' not in html and 'расчет, а не цена сделки' not in html
    fill = html[html.index('async function fillPriceEst'):html.index('function bindPriceEstimate')]
    assert fill.index('pe-range') < fill.index('${srcLine}') < fill.index('pe-text')
