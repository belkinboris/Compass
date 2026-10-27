"""Буква «ё» → «е» во всех текстах для людей (владелец, 26–27 октября 2026:
«забудь, что в русском алфавите есть буква ё», «да, замени везде на е»).

Что правится:
  * код с текстами интерфейса, ответов ассистента, постов и консоли
    (`CODE_FILES`), целиком — комментарии тоже, вреда от этого нет;
    строки, где «ё» нужна самому коду (нормализация `replace("ё", "е")`,
    классы символов `[а-яё]`, таблица транслита), не трогаются;
  * тесты — чтобы пины строк совпали с кодом и данными;
  * данные витрины: `deals` и `companies` в deals_promoted.json, карточки
    pending.json, signals.json — только строковые значения; `match_keys`,
    ссылки и служебные таблицы не трогаются (это не тексты для людей, а
    ключи сопоставления: вход с «ё» должен находить профиль как раньше).

    python3 pipeline/strip_yo.py            # сухой прогон: что и сколько
    python3 pipeline/strip_yo.py --write
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Весь код: верхний уровень, pipeline целиком (включая FIXES — они сверяют старые
# значения с базой, где «ё» больше нет), статика сайта и тесты. Сам этот скрипт —
# нет: его таблица замены и регулярные выражения должны остаться с «ё».
# Таблица правок (pipeline/ingest/fixes/) не переписывается: ее значения — как
# записаны, их отпечатки в proofread_absorbed считались с «ё» (review.already_applied
# складывает «ё» при сравнении).
CODE_FILES = sorted(f for f in set(glob.glob('*.py') + glob.glob('pipeline/**/*.py', recursive=True)
                                   + glob.glob('static/**/*.html', recursive=True) + glob.glob('static/**/*.js', recursive=True))
                    if f != 'pipeline/strip_yo.py' and not f.startswith('pipeline/ingest/fixes/'))
DATA_PROSE = ['static/data/deals_promoted.json', 'static/data/pending.json', 'static/data/signals.json']
YO = str.maketrans({'ё': 'е', 'Ё': 'Е'})
# Строки, где «ё» — часть механики, а не текста: нормализация, классы символов, транслит.
KEEP = re.compile(r'replace\((["\'/])[ёЁ]|[а-яА-Я]-[яЯ][ёЁ]|[ЁёЕе]{2}0-9|["\'][ёЁ]["\']\s*[:,]|/[ёЁ]/|\[[^\]\n]*[ёЁ][^\]\n]*\]')


def strip_text(s):
    return '\n'.join(line if KEEP.search(line) else line.translate(YO) for line in s.split('\n'))


def strip_values(obj):
    if isinstance(obj, str):
        return obj.translate(YO)
    if isinstance(obj, list):
        return [strip_values(x) for x in obj]
    if isinstance(obj, dict):
        return {k: strip_values(v) for k, v in obj.items()}
    return obj


def strip_data(path, base):
    name = os.path.basename(path)
    if name == 'deals_promoted.json':
        base['deals'] = strip_values(base['deals'])
        base['companies'] = strip_values(base['companies'])
    elif name == 'pending.json':
        base['cards'] = strip_values(base.get('cards') or [])
    else:
        base = strip_values(base)
    return base


def count(s):
    return len(re.findall('[ёЁ]', s))


def main(argv):
    write = '--write' in argv
    total = 0
    for rel in CODE_FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        s = open(p, encoding='utf-8').read()
        new = strip_text(s)
        n = count(s) - count(new)
        if n:
            print('%6d  %s' % (n, rel))
            total += n
            if write:
                open(p, 'w', encoding='utf-8').write(new)
    for rel in DATA_PROSE:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        base = json.load(open(p, encoding='utf-8'))
        before = count(json.dumps(base, ensure_ascii=False))
        new = strip_data(p, base)
        n = before - count(json.dumps(new, ensure_ascii=False))
        print('%6d  %s' % (n, rel))
        total += n
        if write and n:
            fresh = json.load(open(p, encoding='utf-8'))            # перечитать прямо перед записью
            assert count(json.dumps(fresh, ensure_ascii=False)) == before, 'файл изменился между прогоном и записью — повторите'
            json.dump(strip_data(p, fresh), open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Всего замен: %d.%s' % (total, '' if write else ' Сухой прогон — запись с ключом --write.'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
