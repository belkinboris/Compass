# -*- coding: utf-8 -*-
"""Пересказ карточки — по статье, а не по самой карточке (1 ноября 2026).

ВТБ/«Деметра» (ga7232033): «Продажа шла сложной сделкой, и один из ее этапов —
допэмиссия холдинга» три месяца стояла в карточке. С 14 по 26 октября 2026
2906 полей у 1169 карточек переписали «по тому, что у нас написано»: цитата
подтверждалась самой карточкой, и ошибка возвращалась с «доказательством».
Здесь — то, что мешает повторению: источник, осторожность, время, допэмиссия.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "pipeline", ROOT / "pipeline" / "ingest"):
    sys.path.insert(0, str(p))

import accept_card      # noqa: E402
import prose_gate       # noqa: E402
import second_reading   # noqa: E402
import write_card       # noqa: E402

FORECAST = ('Есть и тактическая задача: ожидаемая дополнительная эмиссия, посредством которой будет '
            'продаваться доля, позволит российским собственникам сохранить ведущую роль.')


def test_a_forecast_does_not_turn_into_a_fact():
    # Прогон 1 ноября: «будет продаваться» → «Продажа шла сложной сделкой» — осторожность пропала.
    assert prose_gate.hedge_lost([FORECAST], 'Продажа шла сложной сделкой, и один из её этапов — допэмиссия холдинга.')
    # Осторожность или автор сохранены — текст проходит.
    assert not prose_gate.hedge_lost([FORECAST], 'По данным «Ведомостей», допэмиссия должна была помочь собственникам.')
    assert not prose_gate.hedge_lost([FORECAST], 'Продавцы ожидали сохранить влияние за счет допэмиссии.')
    # Нет осторожности в цитате — нечего терять.
    assert not prose_gate.hedge_lost(['ВТБ продал 45% в июле 2023 года.'], 'Банк вышел из капитала холдинга.')


def test_write_card_refuses_a_text_that_dropped_the_hedge():
    card = {'id': 'gtest0001', 'law': {'struct': 'старый текст'}}
    ev = [{'field': 'law.struct', 'fact': 'допэмиссия, продажа доли', 'quote': FORECAST}]
    fixes, notes = write_card.build_fixes('gtest0001', card, ev, {
        'law.struct': {'text': 'Продажа шла сложной сделкой, и один из её этапов — допэмиссия холдинга.', 'facts': [1]}})
    assert not fixes and any('осторожность' in n for n in notes)
    # Явная причина пишущего снимает отказ.
    fixes, _ = write_card.build_fixes('gtest0001', card, ev, {
        'law.struct': {'text': 'Продажа шла сложной сделкой, и один из её этапов — допэмиссия холдинга.',
                       'facts': [1], 'hedge_ok': 'раскрытие эмитента от 12 июля подтверждает'}})
    assert len(fixes) == 1


def test_a_quote_that_lies_only_in_the_card_does_not_confirm_a_rewrite(monkeypatch):
    own_text = 'Долю продали через сложноструктурированную сделку, одним из этапов которой была допэмиссия холдинга.'
    card = {'id': 'gtest0002', 'type': 'M&A', 'status': 'Закрыта', 'law': {'struct': own_text}}
    fix = {'id': 'gtest0002', 'field': 'law.struct', 'old': own_text,
           'new': 'Банк продал пакет, а холдинг отдельно выпускал новые доли.',
           'quote': 'одним из этапов которой была допэмиссия холдинга', 'why': 'тест'}
    monkeypatch.setattr(write_card.review, 'source_texts', lambda: ['Совсем другая статья про другую сделку и ее цену.'])
    data = {'companies': {}}
    found, _ = write_card.check_fixes([fix], card, data)
    assert 'law.struct' in found and any('цитаты нет в тексте источника' in b for b in found['law.struct'])
    # Статья на диске (save_source) — цитата настоящая, отказа по источнику нет.
    monkeypatch.setattr(write_card.review, 'source_texts',
                        lambda: ['В сделке участвовали три стороны, и одним из этапов которой была допэмиссия холдинга, сообщил источник.'])
    found, _ = write_card.check_fixes([fix], card, data)
    assert not any('цитаты нет в тексте источника' in b for b in found.get('law.struct', []))
    # Явный ключ для правки слов без смысла: цитата может лежать и в тексте карточки.
    monkeypatch.setattr(write_card.review, 'source_texts', lambda: ['Совсем другая статья.'])
    found, _ = write_card.check_fixes([fix], card, data, card_text_ok=True)
    assert not any('цитаты нет в тексте источника' in b for b in found.get('law.struct', []))


def test_save_source_text_is_seen_by_the_checks(tmp_path, monkeypatch):
    import review
    import save_source
    path = save_source.save('https://example.org/a', 'Заголовок', 'Текст статьи. ' * 30, day='2026-11-01', folder=str(tmp_path))
    store = json.load(open(path, encoding='utf-8'))
    assert store['items'][0]['url'] == 'https://example.org/a'
    save_source.save('https://example.org/a', 'Заголовок 2', 'Новый текст статьи. ' * 30, day='2026-11-01', folder=str(tmp_path))
    assert len(json.load(open(path, encoding='utf-8'))['items']) == 1      # повтор заменяет, не дублирует
    monkeypatch.setattr(review, 'TRIAGE', str(tmp_path))
    assert 'https://example.org/a' in review.source_urls()
    assert any('Новый текст статьи' in t for t in review.source_texts())


def test_acceptance_catches_intent_left_in_a_closed_deal_and_cash_in_as_a_stage():
    base = {'deals': [], 'companies': {}}
    src = [['РБК', 'https://example.org/1']]
    closed = {'id': 'gtest0003', 'title': 'x', 'type': 'M&A', 'status': 'Закрыта', 'src': src,
              'eco': {'rationale': 'Продать долю планируют в этом году.'}}
    assert any(c == 'stale_statement:eco.rationale' for c, _ in accept_card.findings(closed, base))
    staged = {'id': 'gtest0004', 'title': 'x', 'type': 'M&A', 'status': 'Закрыта', 'src': src,
              'law': {'struct': 'Продажа шла сложной сделкой, и один из её этапов — допэмиссия холдинга.'}}
    assert any(c == 'stale_statement:law.struct' for c, _ in accept_card.findings(staged, base))
    invest = dict(staged, id='gtest0005', type='Инвестиция')       # допэмиссия и есть сделка
    assert not any(c == 'stale_statement:law.struct' for c, _ in accept_card.findings(invest, base))
    history = {'id': 'gtest0006', 'title': 'x', 'type': 'M&A', 'status': 'Закрыта', 'src': src,
               'eco': {'rationale': 'Покупатель давно собирался выкупить актив, но торги сорвались.'}}
    assert not any(c.startswith('stale_statement:') for c, _ in accept_card.findings(history, base))


def test_second_reading_asks_about_language_and_modality():
    assert {'language', 'modality'} <= set(second_reading.GENERAL_QUESTIONS)
    assert 'вслух' in second_reading.GENERAL_QUESTIONS['language']
    assert 'ожидается' in second_reading.GENERAL_QUESTIONS['modality']


def test_risk_queue_puts_cards_with_a_channel_post_first():
    import prose_risk_scan
    base = {'deals': [
        {'id': 'ga', 'status': 'Закрыта', 'type': 'M&A', 'title': 'a',
         'eco': {'rationale': 'Продать долю планируют в этом году.'}},
        {'id': 'gb', 'status': 'Закрыта', 'type': 'M&A', 'title': 'b',
         'eco': {'rationale': 'Продать долю планируют в этом году.'}},
        {'id': 'gc', 'status': 'Закрыта', 'type': 'M&A', 'title': 'c', 'second_read': '2026-11-02',
         'eco': {'rationale': 'Продать долю планируют в этом году.'}}],
        'telegram_posts': {'gb': 77}, 'companies': {}}
    queue = prose_risk_scan.scan(base)
    assert [q['id'] for q in queue] == ['gb', 'ga']          # пост впереди; перечитанная с 1 ноября выпала
