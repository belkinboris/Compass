# -*- coding: utf-8 -*-
"""«Европлан» (g78986e22): в «Финансах предмета» прибыль за первое полугодие
2025 года стояла «19 млрд ₽» — в десять раз больше настоящей.

Что сломано: компания отчиталась о 1,9 млрд ₽ (−78% к первому полугодию
2024-го); в той же строке карточки рядом стоит прибыль за первое полугодие
2026 года — 4,3 млрд ₽, «+129%» — база 19 млрд ₽ противоречит и ей. Нашёл
внешний рецензент (четвёртый разбор, 6 сентября 2026), не мы: слой фактов
защищает агрегаты, а прозу карточки читатель и ассистент берут как есть.

Источник: finance.mail.ru, 20 августа 2026 — «В аналогичном периоде
прошлого года этот показатель был более чем в два раза ниже и находился на
уровне 1,9 млрд ₽» (о первом полугодии 2025 года, рядом с 4,3 млрд ₽ за
первое полугодие 2026-го).

Запуск: python3 pipeline/fix_europlan_h1_2025_profit_typo.py [--write]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'
SRC = ['Финансы Mail.ru', 'https://finance.mail.ru/article/chistaya-pribyil-evroplana-uvelichilas-v-dva-raza-po-itogam-pervogo-polugodiya-69223620/']
OLD = 'упала на 78% по сравнению с годом ранее, до 19 млрд ₽.'
NEW = 'упала на 78% по сравнению с годом ранее, до 1,9 млрд ₽.'


def main(write=False):
    base = json.load(open(DATA, encoding='utf-8'))
    d = next(x for x in base['deals'] if x['id'] == 'g78986e22')
    text = d['eco'].get('target_fin') or ''
    if NEW in text and OLD not in text:
        print('Уже исправлено.')
        return 0
    assert OLD in text, 'исходный текст изменился — проверьте карточку руками'
    d['eco']['target_fin'] = text.replace(OLD, NEW)
    if SRC[1] not in [s[1] for s in d.get('src', []) if isinstance(s, list) and len(s) > 1]:
        d.setdefault('src', []).append(SRC)
    print('eco.target_fin: «19 млрд ₽» → «1,9 млрд ₽»; источник добавлен.')
    if write:
        json.dump(base, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
