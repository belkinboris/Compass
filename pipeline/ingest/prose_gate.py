# -*- coding: utf-8 -*-
"""Проверка текста карточки, написанного по цитате: не копия, не скелет.

Вызывается из `review.check` для полей `PROSE_WRITTEN`; та же мера — у
приёмки (`accept_card.near_copy_sentences`) и у очереди рутины качества
(`verbatim_check.py --from-fixes`). Вынесено из review.py, чтобы тот не
разбухал (`test_fix_batches_live_in_separate_files`).
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
# правила поверх, меняя два-три слова («придется учесть» → «придётся
# считаться»). Владелец и партнёр об «Азимуте» в Ярославле: «он не
# переписывает, тупо забирает куски». Теперь для текстовых полей наоборот:
# цитата — доказательство (одна или несколько, через « … »), текст — свой.
# Проверяется: каждая цитата настоящая; в тексте нет цепочки от
# PROSE_MAX_RUN слов из цитаты и нет скелета её предложения с заменой слов;
# каждое число текста стоит в цитатах; нет пресс-пометок и казённых оборотов.
# Как писать текст — `WRITING_BRIEF.md` (пишущий видит факты, а не статьи).
PROSE_WRITTEN = frozenset(('extra', 'eco.share', 'eco.val', 'eco.target_fin', 'eco.fin',
                           'eco.rationale', 'eco.context', 'law.struct', 'law.terms', 'law.appr'))
PROSE_MAX_RUN = 8
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


# Имена, названия в кавычках, латиница и числа с единицами — это факты, их
# пересказать нельзя: «владелец с декабря 2024 года — ЗПИФ „Формула доверия“
# через ООО „Карат Инвестиции“» неизбежно совпадёт с цитатой. Списанное
# предложение узнаётся по ОБЫЧНЫМ словам — их и сравниваем (проба на
# «Карате», 14 октября 2026: без этого отказ получали честные пересказы).
_QUOTED = re.compile(r'«[^«»]*(?:«[^«»]*»[^«»]*)*»|„[^“]*“|"[^"]*"')
_UNIT = re.compile(r'(?i)\b(?:млн|млрд|трлн|тыс|руб|т|кг|га|кв|м|км|г|гг|год[ау]?|лет)\b\.?|[%₽$€]')
_TOKEN = re.compile(r'[^\s]+')


def plain_words(text):
    """Текст без имён, названий и чисел; границы предложений сохраняются."""
    text = _QUOTED.sub(' ', str(text or ''))
    text = re.sub(r'\d[\d\s\u00a0.,–-]*', ' ', text)
    text = _UNIT.sub(' ', text)
    out, start = [], True
    for tok in _TOKEN.findall(text):
        core = tok.strip('()«»„“"—–-:,;')
        if core and re.match(r'[A-Za-z]', core):
            pass                                   # латиница — имя
        elif core and core[0].isupper() and not start:
            pass                                   # заглавная внутри предложения — имя
        else:
            out.append(tok)
        if tok:
            start = tok.endswith(('.', '!', '?', ';')) or (start and not core)
    return ' '.join(out)


SPEECH_MIN_WORDS = 5
SPEAKER_RE = re.compile(r'(?i)\b(?:сказал|сказала|заявил|заявила|отметил|отметила|пояснил|пояснила|'
                        r'считает|говорит|по\s+словам|рассказал|рассказала|добавил|добавила|'
                        r'подчеркнул|подчеркнула|написал|написала|уточнил|уточнила)\b')


def _flat(s):
    return re.sub(r'[^0-9a-zа-я]+', ' ', str(s or '').lower().replace('ё', 'е')).strip()


def speech_fragments(text):
    """Куски в «ёлочках» от SPEECH_MIN_WORDS слов — чужие слова, не названия."""
    out = []
    for m in re.finditer(r'«((?:[^«»]|«[^«»]*»)*)»', str(text or '')):
        frag = m.group(1)
        if len(_flat(frag).split()) >= SPEECH_MIN_WORDS:
            out.append(frag)
    return out


def prose_problems(new, quote):
    """Причины не принимать текст поля, написанный по цитате (см. выше)."""
    from pipeline import verbatim_check as vc
    import proofread
    bad = []
    orig_new, orig_quote = new, quote
    new, quote = plain_words(new), plain_words(quote)
    q_words = vc.words(quote)
    run, snippet = vc.longest_common_run(vc.words(new), q_words, PROSE_MAX_RUN)
    if run >= PROSE_MAX_RUN:
        bad.append('текст повторяет цитату %d словами подряд («%s…») — напишите своими словами '
                   'по фактам, см. WRITING_BRIEF.md' % (run, snippet[:60]))
    q_stems = [w[:5] for w in q_words if len(w) >= 3 and w not in vc._STOP]
    for share, sent in vc.near_copies(new, q_stems):
        bad.append('предложение повторяет построение цитаты с заменой отдельных слов (%d%%): «%s» — '
                   'перескажите по-своему' % (round(100 * share), sent[:70]))
    q_nums = _numbers(orig_quote)
    extra = sorted(n for n in _numbers(orig_new) if n not in q_nums)
    if extra:
        bad.append('в тексте числа, которых нет в цитатах: %s' % ', '.join(extra))
    for rule, frag in proofread.source_note(orig_new):
        bad.append('пометка об источнике в тексте («%s») — %s' % (frag, rule))
    # ПРЯМУЮ РЕЧЬ НЕ ПЕРЕСКАЗЫВАЮТ И НЕ ПРАВЯТ (владелец, 14 октября 2026):
    # чужие слова в кавычках — только дословно и с тем, кто их сказал.
    # Названия в кавычках короткие, поэтому проверяются кавычки от 5 слов.
    for frag in speech_fragments(orig_new):
        if _flat(frag) not in _flat(orig_quote):
            bad.append('в кавычках не дословные слова источника («%s…») — цитату нельзя менять: '
                       'дословно или пересказом без кавычек' % frag[:60])
        elif not SPEAKER_RE.search(orig_new):
            bad.append('у цитаты («%s…») не назван тот, кто это сказал' % frag[:60])
    if re.search(r'на\s+момент\s+(?:записи|написания|подготовки)|\bэто\s+и\s+привело\b', orig_new, re.I):
        bad.append('казённый оборот — скажите, как сказал бы человек')
    return bad


def known_texts(fix, card, fixes, get_field):
    """Чем ещё подтверждается цитата ПЕРЕПИСАННОГО текста: прежними цитатами
    той же карточки и её нынешним текстом. Статьи старых карточек с диска уже
    убраны, а владелец 14.10.2026 велел переписывать «то, что у нас
    написано», не ходя к первоисточникам. Только для текстовых полей:
    имя, сумма и дата по-прежнему сверяются со статьёй."""
    if fix.get('field') not in PROSE_WRITTEN or not card:
        return []
    out = [f['quote'] for f in fixes
           if f.get('id') == fix.get('id') and f is not fix and isinstance(f.get('quote'), str)]
    out += [v for fld in PROSE_WRITTEN for v in [get_field(card, fld)]
            if isinstance(v, str) and v not in ('', '—')]
    return out


def absorb_earlier(fix, card, fixes, fingerprint):
    """Пересказ заменил текст, который внесли прежние правки того же поля:
    их факты в нём остались, слова — нет. Отпечатки прежних правок уходят в
    `proofread_absorbed` (как у вычитки, docs/card_editing.md), иначе
    `test_review_table_is_applied_and_not_pending` сочтёт их неприменёнными."""
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
    # Текстовое поле пишется своими словами: копия цитаты и её скелет с
    # заменой слов — отказ, свой пересказ по тем же фактам — проходит.
    q_prose = ('Продажа состоялась по минимальной цене, поскольку других '
               'претендентов на актив не нашлось, сообщили в министерстве.')
    assert prose_problems(q_prose, q_prose)
    assert prose_problems('Продажа состоялась по самой минимальной цене, так как '
                          'других претендентов на этот актив не нашлось.', q_prose)
    assert not prose_problems('Других покупателей не было, поэтому объект ушёл '
                              'по нижнему порогу цены.', q_prose)
    assert prose_problems('Объект ушёл за 400 млн ₽.', q_prose)   # число не из цитаты
    # Несколько цитат через « … » — настоящей обязана быть каждая.
    assert quote_is_real('альфа бета … гамма дельта', ['альфа бета и гамма дельта'])
    assert not quote_is_real('альфа бета … эпсилон', ['альфа бета и гамма дельта'])
    # Прямая речь: дословно и с автором — можно; изменённая — нельзя.
    q_sp = 'Мы рассчитываем удвоить выпуск сыров в течение двух лет, сказал гендиректор Иванов.'
    assert not prose_problems('«Мы рассчитываем удвоить выпуск сыров в течение двух лет», '
                              '— сказал гендиректор Иванов.', q_sp)
    assert prose_problems('«Мы надеемся удвоить выпуск сыров в течение двух лет», '
                          '— сказал гендиректор Иванов.', q_sp)
    assert prose_problems('Компания: «мы рассчитываем удвоить выпуск сыров в течение двух лет».', q_sp)
