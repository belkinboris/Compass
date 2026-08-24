# -*- coding: utf-8 -*-
"""Месячная очередь, карточка gb4fad654 (КСЭ/BXB — международное
направление Boxberry): продавец не был назван вовсе. Дельта-поиск нашёл
прямого владельца предмета на момент сделки: с августа 2025 года 100%
BXB принадлежало АО «Инвестсервис» (гендиректор Сергей Сотник, он же
возглавил саму BXB) — это не «Яндекс» и не «Boxberry» как бренд, а
отдельное юрлицо-держатель. Профиля компании под него заводить не
стали: у АО «Инвестсервис» нет других сделок в базе, только эта роль.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://www.cnews.ru/news/top/2025-09-25_mezhdunarodnaya_chast_kuplennoj

Запуск: python3 pipeline/fix_kse_bxb_seller.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gb4fad654'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert 'seller' not in deal, f"seller уже проставлен: {deal.get('seller')!r}"

    print(f"{CARD_ID}: seller = «АО «Инвестсервис» (Сергей Сотник)» — "
          f"поле было не заполнено вовсе")
    deal['seller'] = 'АО «Инвестсервис» (Сергей Сотник)'
    deal['seller_src'] = 'text'

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
