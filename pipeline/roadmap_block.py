# -*- coding: utf-8 -*-
"""Показать один блок бэклога или последние записи журнала — вместо чтения
PRODUCT_ROADMAP.md целиком (68 тыс. токенов на 28 октября 2026).

    python3 pipeline/roadmap_block.py G          # блок G бэклога
    python3 pipeline/roadmap_block.py --journal 5  # пять последних записей журнала
    python3 pipeline/roadmap_block.py --list      # какие блоки есть и их размер
    python3 pipeline/roadmap_block.py --add D "текст пункта"  # новый пункт в конец блока

«Сделаю потом» из чата следующая сессия не видит — --add пишет его в бэклог
сразу (29 октября 2026, docs/documents.md).
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROADMAP = os.path.join(ROOT, 'PRODUCT_ROADMAP.md')


def main(argv):
    text = io.open(ROADMAP, encoding='utf-8').read()
    backlog = text[text.index('## 4. Бэклог'):text.index('## 5. Журнал работ')]
    journal = text[text.index('## 5. Журнал работ'):]
    if not argv or argv[0] == '--list':
        for m in re.finditer(r'^### ([A-Z])\. (.+)$', backlog, re.M):
            nxt = backlog.find('\n### ', m.end())
            size = (nxt if nxt > 0 else len(backlog)) - m.start()
            print('%s  %6d знаков  %s' % (m.group(1), size, m.group(2)))
        print('журнал: %d знаков, записей %d' % (len(journal), len(re.findall(r'^### \d{4}', journal, re.M))))
        return 0
    if argv[0] == '--add':
        if len(argv) < 3 or not argv[2].strip():
            print('Нужно: --add <блок> "<текст пункта>"')
            return 2
        return add_item(argv[1].upper(), argv[2].strip())
    if argv[0] == '--journal':
        n = int(argv[1]) if len(argv) > 1 else 3
        parts = re.split(r'\n(?=### \d{4}-\d{2}-\d{2})', journal)
        print('\n'.join(parts[1:1 + n]))
        return 0
    letter = argv[0].upper()
    m = re.search(r'^### %s\. .+$' % re.escape(letter), backlog, re.M)
    if not m:
        print('Блока %s нет. Какие есть — --list.' % letter)
        return 1
    nxt = backlog.find('\n### ', m.end())
    print(backlog[m.start():nxt if nxt > 0 else len(backlog)].rstrip())
    return 0


def add_item(letter, text, path=ROADMAP):
    """Дописать пункт в конец блока бэклога с очередным номером; вернуть код выхода."""
    full = io.open(path, encoding='utf-8').read()
    start = full.index('## 4. Бэклог')
    end = full.index('## 5. Журнал работ')
    backlog = full[start:end]
    m = re.search(r'^### %s\. .+$' % re.escape(letter), backlog, re.M)
    if not m:
        print('Блока %s нет. Какие есть — --list.' % letter)
        return 1
    nxt = backlog.find('\n### ', m.end())
    if nxt < 0:
        nxt = len(backlog)
    body = backlog[m.start():nxt]
    nums = [int(n) for n in re.findall(r'\*\*%s(\d+)\.' % letter, body)]
    item = '- **%s%d. %s**' % (letter, max(nums, default=0) + 1, text.rstrip('.'))
    core = body.rstrip('\n')
    new_body = core + '\n' + item + body[len(core):]
    backlog = backlog[:m.start()] + new_body + backlog[nxt:]
    io.open(path, 'w', encoding='utf-8').write(full[:start] + backlog + full[end:])
    print('Записано в блок %s: %s' % (letter, item))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
