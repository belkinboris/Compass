# -*- coding: utf-8 -*-
"""Показать один блок бэклога или последние записи журнала — вместо чтения
PRODUCT_ROADMAP.md целиком (68 тыс. токенов на 28 октября 2026).

    python3 pipeline/roadmap_block.py G          # блок G бэклога
    python3 pipeline/roadmap_block.py --journal 5  # пять последних записей журнала
    python3 pipeline/roadmap_block.py --list      # какие блоки есть и их размер
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


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
