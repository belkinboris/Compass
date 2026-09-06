# -*- coding: utf-8 -*-
"""Печатает текст источника из кэша притока (data/inbox/raw/*-articles.jsonl)
по адресу — читателям фактов (pipeline/FACTS_READING_BRIEF.md), чтобы цитаты
брались из того же текста, по которому их потом проверяет facts_confirm.py.

Запуск:
    python3 pipeline/facts_source_text.py https://www.interfax.ru/business/1022482
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.facts_confirm import source_texts  # noqa: E402


def main(urls):
    texts = source_texts()
    for u in urls:
        t = texts.get(u)
        print(f'=== {u}')
        print(t if t else '(нет в кэше — откройте WebFetch)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
