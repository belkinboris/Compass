# -*- coding: utf-8 -*-
"""Сохранить текст статьи, который прочитали, туда, где его видят проверки.

ЗАЧЕМ. Пересказ карточки обязан опираться на статью (docs/card_editing.md,
«Пересказ — по статье, не по карточке», 1 ноября 2026): `write_card.py`
сверяет цитаты с текстами из `data/inbox/raw` и `data/inbox/triage`. Старых
статей на диске нет (папка живет только на машине рутины и в git не лежит),
поэтому читающий сначала открывает статью, кладет ее текст сюда, и только
потом собирает факты. Адрес из этого файла `review.py` тоже считает
«забранным»: источник можно приложить к карточке.

    python3 pipeline/ingest/save_source.py --url <адрес> --title "<заголовок>" --file article.txt

Файл с текстом — то, что вернул WebFetch/браузер; сохраняется как есть (в
git эта папка не попадает: чужие тексты целиком в репозитории не храним —
docs/sources_legal.md).
"""
import argparse
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TRIAGE = os.path.join(ROOT, 'data', 'inbox', 'triage')


def save(url, title, text, day=None, folder=None):
    folder = folder or TRIAGE
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, 'sources_%s.json' % (day or date.today().isoformat()))
    store = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {'made': 'save_source.py', 'items': []}
    store['items'] = [i for i in store['items'] if i.get('url') != url]      # повторный ввод заменяет
    store['items'].append({'title': title, 'summary': text, 'url': url})
    json.dump(store, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--url', required=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--file', required=True, help='файл с текстом статьи')
    a = ap.parse_args(argv)
    text = open(a.file, encoding='utf-8').read().strip()
    if len(text) < 200:
        print('Текст короче 200 знаков — похоже на «Captcha»/«Loading…», а не на статью. Не сохраняю.')
        return 1
    print('Сохранено: %s (%d знаков)' % (os.path.relpath(save(a.url, a.title, text), ROOT), len(text)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
