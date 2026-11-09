# -*- coding: utf-8 -*-
"""Заголовок «Чемодан Про» снова называет Samsonite (9 ноября 2026).

Короткая проверка переписала заголовок по стандарту («X купил N% Y у Z») и
потеряла узнаваемое имя: «Чемодан Про» — бывшее российское юрлицо Samsonite,
и на вопрос «Что стало с российским бизнесом Samsonite?» ассистент перестал
находить сделку (публикация встала на test_ordinary_words_are_not_company_names).
Стандарт велит узнаваемые имена — бренд, а не юрлицо. Запись FIXES в
reread_2026_11_09_sj.py обновлена тем же текстом; отметка вычитки
переставляется на новый отпечаток.

    python3 pipeline/archive/2026-11/fix_samsonite_title_2026_11_09.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import readiness  # noqa: E402
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OLD = '«Робинзон Логистикс» купил у Андрея Языкова 30% «Чемодан Про»'
NEW = OLD + ', бывшего российского бизнеса Samsonite'


def _apply(data):
    card = next(d for d in data['deals'] if d['id'] == 'g83ad1f72')
    assert card['title'] == OLD, card['title']
    card['title'] = NEW
    if card.get('reread'):
        card['reread_hash'] = readiness.fingerprint(card, data['companies'])


def main(argv):
    _apply(json.load(open(BASE, encoding='utf-8')))
    if '--write' not in argv:
        print('Сухой прогон: %s → %s' % (OLD, NEW))
        return 0
    fresh = json.load(open(BASE, encoding='utf-8'))
    _apply(fresh)
    json.dump(fresh, open(BASE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
