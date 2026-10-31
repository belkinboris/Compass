# -*- coding: utf-8 -*-
"""Карточка `gd937c845` (OTP Group/Luminor) — `eco.target_fin` дополнен
более свежей разбивкой кредитного портфеля (конец июня 2026), которой не
было в уже стоящих апрельских данных ЦБ. Источник — телеграм-канал
«Сделки M&A», принятый тип источника в этой базе (используется и в
других карточках). Разовый скрипт — другой источник, чем уже стоящий в
поле текст.

Источник: https://t.me/dealsma/7437

    python3 pipeline/fix_gd937c845_otp_loan_portfolio.py           # показать
    python3 pipeline/fix_gd937c845_otp_loan_portfolio.py --write   # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep, 1)[0]
sys.path.insert(0, ROOT)
import source_names

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DEAL = 'gd937c845'

OLD_TARGET_FIN = (
    'По форме 806 Банка России на 1 апреля 2026 года активы АО «ОТП Банк» '
    '— 794,1 млрд ₽ (годом ранее 758,5 млрд ₽), собственные средства — '
    '95,7 млрд ₽ (84,4 млрд ₽).'
)

ADDED = (
    'С 2022 года банк прекратил выдачу корпоративных кредитов: '
    'корпоративный кредитный портфель сократился с 28 млрд ₽ в 2021 г. до '
    '400 млн ₽ в 2026 г. На конец июня 2026 г. розничный кредитный '
    'портфель составлял 411 млрд ₽, в том числе автокредиты — 182 млрд ₽ '
    '(44,3%), POS-кредиты — 165,7 млрд ₽ (40,3%), остальные — 63,3 млрд ₽ '
    '(15,4%).'
)


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))   # перечитано прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == DEAL)
    assert deal['eco']['target_fin'] == OLD_TARGET_FIN, deal['eco']['target_fin']
    deal['eco']['target_fin'] = OLD_TARGET_FIN + ' ' + ADDED
    deal['src'] = list(deal.get('src') or [])
    url = 'https://t.me/dealsma/7437'
    if not any(len(s) > 1 and s[1] == url for s in deal['src']):
        deal['src'].append(['Телеграм-канал: Сделки M&A', url])
    source_names.settle_sources(deal)   # агрегатор — в discovery_src, не рядом с первоисточником
    print('eco.target_fin дополнен разбивкой кредитного портфеля на июнь 2026')
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
