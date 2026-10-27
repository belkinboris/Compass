# -*- coding: utf-8 -*-
"""Снимает из таблиц `pipeline/ingest/fixes/*.py` все записи `dict(id=<ID>,
...)` для карточки, которая только что удалена/слита с другой (см. CLAUDE.md:
«слияние дублей обязано снять правки к удалённой карточке вместе с ней» —
иначе test_review_table_is_applied_and_not_pending падает с «карточки нет
ни в базе, ни в очереди предпросмотра»).

Ищет вхождения `id='<ID>'` (или `id="<ID>"`) построчно, находит начало
объемлющего `dict(` слева на той же логической записи и конец —
балансировкой скобок с учётом строковых литералов, — затем вырезает
найденный диапазон вместе с последующей запятой и переводом строки.
Обрабатывает совпадения с конца файла к началу, чтобы смещения не
съезжали. Каждый файл проверяется компиляцией после правки.

Запуск:
    python3 pipeline/remove_fixes_for_id.py <id> [<id> ...] [--write]
"""
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FIXES_DIR = os.path.join(ROOT, 'ingest', 'fixes')


def _balance(text, start, open_ch, close_ch):
    """Индекс символа сразу ПОСЛЕ закрывающей `close_ch`, парной открывающей
    в позиции `start` (там стоит `open_ch`), с учётом строк в кавычках."""
    i = start + 1
    depth = 1
    n = len(text)
    quote = None
    while i < n and depth > 0:
        c = text[i]
        if quote:
            if c == '\\':
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in ('"', "'"):
            quote = c
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
        i += 1
    return i


def find_dict_spans(text, target_id):
    """Индексы (start, end) каждой записи правки для `target_id` в тексте,
    end указывает на символ СРАЗУ ПОСЛЕ закрывающей скобки. Запись написана
    либо вызовом `dict(id='<id>', ...)`, либо литералом `{'id': '<id>', ...}`
    — в этой базе оба стиля встречаются (литерал — чаще), `id` всегда первый
    ключ записи."""
    spans = []
    seen_starts = set()
    call_pat = re.compile(r"id\s*=\s*['\"]%s['\"]" % re.escape(target_id))
    literal_pat = re.compile(r"['\"]id['\"]\s*:\s*['\"]%s['\"]" % re.escape(target_id))
    for m in call_pat.finditer(text):
        dict_start = text.rfind('dict(', 0, m.start())
        if dict_start == -1 or dict_start in seen_starts:
            continue
        seen_starts.add(dict_start)
        end = _balance(text, dict_start + len('dict') , '(', ')')
        spans.append((dict_start, end))
    for m in literal_pat.finditer(text):
        brace_start = text.rfind('{', 0, m.start())
        if brace_start == -1 or brace_start in seen_starts:
            continue
        seen_starts.add(brace_start)
        end = _balance(text, brace_start, '{', '}')
        spans.append((brace_start, end))
    spans.sort()
    return spans


def strip_entry(text, start, end):
    """Расширяет диапазон вырезания на висящую запятую и перевод строки."""
    j = end
    while j < len(text) and text[j] in ' \t':
        j += 1
    if j < len(text) and text[j] == ',':
        j += 1
    while j < len(text) and text[j] in ' \t':
        j += 1
    if j < len(text) and text[j] == '\n':
        j += 1
    # Начало — включая ведущий отступ этой же строки.
    i = start
    while i > 0 and text[i - 1] in ' \t':
        i -= 1
    return text[:i] + text[j:]


def main(argv):
    write = '--write' in argv
    ids = [a for a in argv if a != '--write']
    assert ids, 'нужен хотя бы один id'
    total = 0
    for name in sorted(os.listdir(FIXES_DIR)):
        if not name.endswith('.py'):
            continue
        path = os.path.join(FIXES_DIR, name)
        text = open(path, encoding='utf-8').read()
        changed = False
        for target_id in ids:
            while True:
                spans = find_dict_spans(text, target_id)
                if not spans:
                    break
                start, end = spans[-1]
                text = strip_entry(text, start, end)
                changed = True
                total += 1
        if changed:
            ast.parse(text)  # падает, если сами себя сломали
            print('%s: снято записей для %s' % (name, ', '.join(ids)))
            if write:
                open(path, 'w', encoding='utf-8').write(text)
    print('Всего снято: %d.' % total)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main(sys.argv[1:])
