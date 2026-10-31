# -*- coding: utf-8 -*-
"""Проверка текста карточки, написанного по цитате: не копия, не скелет.

Вызывается из `review.check` для полей `PROSE_WRITTEN`. Мера дословности —
одна на всех (`verbatim_check.py`, политика 31 октября 2026): ее же берут
приемка (`accept_card.verbatim_runs`), вычитка (`proofread.check`) и очередь
рутины качества (`pipeline/verbatim_check.py`). Вынесено из review.py, чтобы
тот не разбухал (`test_fix_batches_live_in_separate_files`).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.dirname(os.path.dirname(HERE))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ТЕКСТ КАРТОЧКИ ПИШЕТСЯ, А НЕ ПЕРЕНОСИТСЯ (14 октября 2026). До этого дня
# последняя ветка `check` требовала и от прозы того же, что от имени стороны:
# «значение лежит в цитате дословно». 4097 правок текстовых полей из 5862 —
# цитаты источника слово в слово; пересказ оставлялся вычитке, а вычитка
# правила поверх, меняя два-три слова («придется учесть» → «придется
# считаться»). Владелец и партнер об «Азимуте» в Ярославле: «он не
# переписывает, тупо забирает куски». Теперь для текстовых полей наоборот:
# цитата — доказательство (одна или несколько, через « … »), текст — свой.
# Что считать списанным и как относиться к прямой речи — ОДНА политика
# `verbatim_check.py` (решение владельца 31 октября 2026, H10); здесь к ней
# добавлены проверки, которым нужна именно цитата записи: каждое число
# текста стоит в цитатах, нет пресс-пометок и казенных оборотов.
# Как писать текст — `WRITING_BRIEF.md` (пишущий видит факты, а не статьи).
from pipeline import verbatim_check  # noqa: E402
from pipeline.verbatim_check import (PROSE_FIELDS as PROSE_WRITTEN, MIN_WORDS as PROSE_MAX_RUN,  # noqa: E402,F401
                                     SPEAKER_RE, plain_words, speech_fragments)
QUOTE_SEP = re.compile(r'\s+…\s+|\s*\|\|\s*')
_NUM_RX = re.compile(r'\d[\d\s\u00a0]*(?:[.,]\d+)?')


def _numbers(text):
    out = set()
    for m in _NUM_RX.finditer(str(text or '')):
        if re.match(r'\s*[A-Za-z]', str(text)[m.end():]):
            continue                     # «800 Degrees» — название, не число
        n = re.sub(r'[\s\u00a0]', '', m.group(0)).replace(',', '.').rstrip('.')
        if n:
            out.add(n)
    return out


def prose_problems(new, quote, field='extra'):
    """Причины не принимать текст поля, написанный по цитате (см. выше)."""
    import proofread
    bad = []
    # Дословность и прямая речь — политика: цепочка обычных слов от
    # MIN_WORDS с одной заменой, скелет предложения, цитата без автора;
    # слова в кавычках обязаны лежать в цитате буква в букву
    # (владелец, 14 октября 2026: чужую речь не правят).
    for f in verbatim_check.check_text(field, new, [quote], quotes_in_texts=True):
        bad.append(verbatim_check.describe(f) + (' — см. WRITING_BRIEF.md' if f.kind == 'verbatim_run' else ''))
    q_nums = _numbers(quote)
    extra = sorted(n for n in _numbers(new) if n not in q_nums)
    if extra:
        bad.append('в тексте числа, которых нет в цитатах: %s' % ', '.join(extra))
    for rule, frag in proofread.source_note(new):
        bad.append('пометка об источнике в тексте («%s») — %s' % (frag, rule))
    # Правила, которым не нужна статья, — общие для любого пути записи
    # (pipeline/text_rules.py, 22 октября 2026): казенные обороты, служебные
    # пометки, «собеседник издания», желтый тон, жаргон, «(Коммерсантъ)».
    from pipeline import text_rules
    for _code, why in text_rules.problems(new):
        if why not in bad:
            bad.append(why)
    if re.search(r'не\s+раскры', new, re.I) and len(new) < 120 and not re.search(r'\d', new):
        bad.append('в поле только «не раскрыто» — оставьте поле пустым («—»)')
    return bad


def known_texts(fix, card, fixes, get_field):
    """Чем еще подтверждается цитата ПЕРЕПИСАННОГО текста: прежними цитатами
    той же карточки и ее нынешним текстом. Статьи старых карточек с диска уже
    убраны, а владелец 14.10.2026 велел переписывать «то, что у нас
    написано», не ходя к первоисточникам. Только для текстовых полей:
    имя, сумма и дата по-прежнему сверяются со статьей."""
    if fix.get('field') not in PROSE_WRITTEN or not card:
        return []
    out = [f['quote'] for f in fixes
           if f.get('id') == fix.get('id') and f is not fix and isinstance(f.get('quote'), str)]
    out += [v for fld in PROSE_WRITTEN for v in [get_field(card, fld)]
            if isinstance(v, str) and v not in ('', '—')]
    return out


def absorb_earlier(fix, card, fixes, fingerprint):
    """Пересказ заменил текст, который внесли прежние правки того же поля:
    их факты в нем остались, слова — нет. Отпечатки прежних правок уходят в
    `proofread_absorbed` (как у вычитки, docs/card_editing.md), иначе
    `test_review_table_is_applied_and_not_pending` сочтет их непримененными."""
    if fix.get('field') not in PROSE_WRITTEN:
        return
    seen = card.setdefault('proofread_absorbed', {}).setdefault(fix['field'], [])
    for f in fixes:
        if f is fix or f.get('id') != fix.get('id') or f.get('field') != fix.get('field') \
                or f.get('new') in (None, fix.get('new')):
            continue
        fp = fingerprint(f['new'])
        if fp not in seen:
            seen.append(fp)


def self_check(quote_is_real):
    """Вызывается из `review._self_check`."""
    verbatim_check.self_check()
    # Текстовое поле пишется своими словами: копия цитаты и ее скелет с
    # заменой слов — отказ, свой пересказ по тем же фактам — проходит.
    q_prose = ('Продажа состоялась по минимальной цене, поскольку других '
               'претендентов на актив не нашлось, сообщили в министерстве.')
    assert prose_problems(q_prose, q_prose)
    assert prose_problems('Продажа состоялась по самой минимальной цене, так как '
                          'других претендентов на этот актив не нашлось.', q_prose)
    assert not prose_problems('Других покупателей не было, поэтому объект ушел '
                              'по нижнему порогу цены.', q_prose)
    assert prose_problems('Объект ушел за 400 млн ₽.', q_prose)   # число не из цитаты
    # Несколько цитат через « … » — настоящей обязана быть каждая.
    assert quote_is_real('альфа бета … гамма дельта', ['альфа бета и гамма дельта'])
    assert not quote_is_real('альфа бета … эпсилон', ['альфа бета и гамма дельта'])
    # Прямая речь: дословно и с автором — можно; измененная — нельзя.
    q_sp = 'Мы рассчитываем удвоить выпуск сыров в течение двух лет, сказал гендиректор Иванов.'
    assert not prose_problems('«Мы рассчитываем удвоить выпуск сыров в течение двух лет», '
                              '— сказал гендиректор Иванов.', q_sp)
    assert prose_problems('«Мы надеемся удвоить выпуск сыров в течение двух лет», '
                          '— сказал гендиректор Иванов.', q_sp)
    assert prose_problems('Компания: «мы рассчитываем удвоить выпуск сыров в течение двух лет».', q_sp)


def title_problems(new, quote, card, same_word):
    """Заголовок — СВОЯ конструкция, не цитата (владелец, 28 октября 2026:
    «мы же пересказываем и переделываем, чтобы не обвинили в краже»; 29
    октября о заголовке Фонтанки, взятом целиком: «так не говорят»). До
    29 октября 2026 `check` требовал заголовок дословно в цитате — и
    единственным способом пройти проверку было взять заголовок издания, то
    есть ровно то, что запрещено. Проверяется не фраза, а имена в ней:
    каждое название в кавычках, латинское слово и слово с заглавной буквы
    (кроме первого) обязано лечь — с точностью до окончания — на слово
    цитаты или уже записанных сторон и предмета карточки (они прошли свою
    дословную проверку). Так «Андрей Павлов» проходит по `seller`, «Антону
    Петрову» — по цитате, а выдуманный «Иванов» — нет."""
    if not new.strip():
        return ['пустой заголовок']
    backing = ' '.join([str(quote or '')] + [str(card.get(k) or '') for k in ('seller', 'buyer_name', 'asset', 'target')])
    backing_words = [w for w in re.split(r'[^\wа-яё]+', backing, flags=re.I) if w]
    words = [w for w in re.split(r'[^\wа-яё]+', new, flags=re.I) if w]
    quoted = ' '.join(re.findall(r'«([^«»]+)»', new))
    quoted_words = set(re.split(r'[^\wа-яё]+', quoted, flags=re.I)) - {''}
    out = []
    for i, w in enumerate(words):
        proper = (w in quoted_words or re.fullmatch(r'[A-Za-z][A-Za-z\-]{2,}', w)
                  or (i > 0 and w[0].isupper() and len(w) > 2))
        if proper and not any(same_word(w, q) for q in backing_words):
            out.append('в заголовке «%s», которого нет ни в цитате, ни в сторонах и предмете карточки' % w)
    return out
