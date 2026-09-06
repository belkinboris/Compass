# -*- coding: utf-8 -*-
"""Контрольная выборка (pipeline/gold/analytics_gold.json) против кода.

Правило приёмки с 6 сентября 2026 (разбор второго аудита): ожидаемый
результат для сделки фиксируется ЧТЕНИЕМ карточки и источников — независимо
от кода, который потом его считает. Иначе один и тот же ошибочный алгоритм
одновременно даёт результат и подтверждает его: так «доля 95% и выше»
пропустила 30% Guess и 49% «Полиматики», а тест на синтетических примерах
был зелёным.

Здесь проверяется ТЕКСТОВЫЙ допуск (без обращения к отчётности): смысл
суммы, установленная доля, попадёт ли сделка в мультипликатор и в «Только
покупки». Клиентские копии тех же правил проверяются на тех же строках в
test_ui.py (test_gold_rows_agree_with_client_rules).
"""
import json
from pathlib import Path

import pytest

import deal_multiples as dm
from pipeline import fns_registry

ROOT = Path(__file__).resolve().parent
GOLD = json.loads((ROOT / 'pipeline' / 'gold' / 'analytics_gold.json').read_text(encoding='utf-8'))
BASE = json.loads((ROOT / 'static' / 'data' / 'deals_promoted.json').read_text(encoding='utf-8'))
DEALS = {d['id']: d for d in BASE['deals']}
COMPANIES = BASE['companies']
REGISTRY = {r['company_id']: r for r in fns_registry.REGISTRY}
CONFIRMED = {c for c, r in REGISTRY.items() if r['decision'] == 'confirmed'}
BANKS = {c for c, r in REGISTRY.items() if r['decision'] == 'bank'}
LOTS = {c for c, p in COMPANIES.items() if p.get('lot')}
PURCHASE_TYPES = ('M&A', 'Продажа с торгов')


def counts_in_top_purchases(d: dict) -> bool:
    """Python-двойник countsAsPrice && !isSoftSum && ₽ из static/index.html:
    только покупки, только цена, названная сторонами, только рубли."""
    if d.get('status') == 'Не состоялась':
        return False
    if d.get('type') == 'Продажа с торгов' and d.get('status') != 'Закрыта':
        return False
    if d.get('type') not in PURCHASE_TYPES:
        return False
    return dm.sum_basis(d) == 'disclosed'


def _rows():
    return [pytest.param(row, id=row['id']) for row in GOLD['deals']]


@pytest.mark.parametrize('row', _rows())
def test_gold_deal_exists(row):
    assert row['id'] in DEALS, f"{row['id']} нет в базе — строку выборки надо обновить, а не удалять молча"


@pytest.mark.parametrize('row', _rows())
def test_gold_sum_basis(row):
    d = DEALS[row['id']]
    assert dm.sum_basis(d) == row['sum_basis'], (row['id'], d.get('sum'), dm.sum_basis(d), row['why'])


def _pending(row):
    # Строка выборки говорит правду, которой карточка пока не соответствует
    # (например, 100% названы только в extra). Такая строка обязана падать —
    # strict xfail: когда данные починят, тест покраснеет и потребует снять pending.
    if row.get('pending'):
        pytest.xfail(f"{row['id']}: {row['pending']}")


@pytest.mark.parametrize('row', _rows())
def test_gold_share(row):
    _pending(row)
    d = DEALS[row['id']]
    if d.get('type') not in PURCHASE_TYPES:
        pytest.skip('доля ПОКУПКИ определена только для покупок; у допэмиссии/IPO/финансирования проценты в тексте — про другое')
    got = dm.stake_established(d)
    assert got == row['share'], (row['id'], got, row['why'])


@pytest.mark.parametrize('row', _rows())
def test_gold_multiples_admission(row):
    _pending(row)
    d = DEALS[row['id']]
    cand, reason = dm.admission(dict(d, id=row['id']), CONFIRMED, BANKS, LOTS)
    assert (cand is not None) == row['in_multiples'], (row['id'], reason, row['why'])


@pytest.mark.parametrize('row', _rows())
def test_gold_top_purchases(row):
    d = DEALS[row['id']]
    assert counts_in_top_purchases(d) == row['in_top_purchases'], (row['id'], d.get('type'), d.get('sum'), row['why'])


def test_gold_positives_exist():
    """Выборка обязана содержать и допущенные сделки: правило, которое
    отбрасывает всё, тоже прошло бы тест из одних отказов."""
    assert any(r['in_multiples'] for r in GOLD['deals'])
    assert any(r['in_top_purchases'] for r in GOLD['deals'])
    assert any(not r['in_top_purchases'] for r in GOLD['deals'])


def test_gold_duplicates_are_merged():
    merged = BASE.get('merged', {})
    for pair in GOLD['duplicates']:
        assert pair['drop'] not in DEALS, pair
        assert merged.get(pair['drop']) == pair['keep'], pair
        assert pair['keep'] in DEALS, pair


def test_gold_non_duplicates_are_not_flagged_as_candidates():
    from pipeline import find_duplicate_deal_candidates as scanner
    found = scanner.candidates(list(DEALS.values()))
    for item in GOLD['not_duplicates']:
        pair = frozenset(item['pair'])
        assert all(i in DEALS for i in pair), item
        assert pair not in found or pair in scanner.NOT_DUPLICATES, item


@pytest.fixture(scope='module')
def idx():
    import assistant_retrieval as ar
    return ar.get_index(force=True)


@pytest.mark.parametrize('chain', [pytest.param(c, id=c['must_mention']) for c in GOLD['assistant']])
def test_gold_assistant_chain_keeps_the_deal(chain, idx):
    """Цепочка из двух-трёх вопросов: каждый ответ обязан оставаться на той
    же сделке — уточняющий вопрос без имени сущности не превращается в
    «в Компасе нет сделки» (аудит, раунд 2)."""
    import assistant_retrieval as ar
    previous = None
    for question in chain['chain']:
        r = ar.retrieve(question, None, None, idx, previous=previous)
        mentioned = chain['must_mention'] in (r.answer or '') or any(d.id == chain['must_mention'] for d in r.docs)
        assert mentioned, (question, r.answer[:200] if r.answer else r.answer, chain['why'])
        previous = question
