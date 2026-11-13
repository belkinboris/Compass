"""Firm.One — юридический консультант KAMA FLOW в сделке с «Рапид Био» (13 ноября 2026).

Владелец: «Firm.one сопровождала Kama flow». Источник — сообщение фирмы
https://ru.firm.one/news/kama-flow-rapid-bio/ (7 октября 2026). Других сделок
на сайте фирмы нет: просмотрены все 125 новостей и 3 кейса.
Без ключа — сухой прогон, запись по --write.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
ROW = ['Юридический консультант инвестора (KAMA FLOW)', 'Firm.One',
       'Проверка компании, подготовка документов сделки и участие в переговорах. Проект возглавили '
       'управляющий партнер Сергей Клименко и партнер Александр Ковалев; в сопровождении участвовали '
       'советник Александра Черномырдина, старшие юристы Виктория Викторова и Хосе Тобар, юрист Юрий Пыльнев. '
       'Источник: https://ru.firm.one/news/kama-flow-rapid-bio/']


def main(write):
    base = json.load(open(BASE, encoding='utf-8'))
    d = next(x for x in base['deals'] if x['id'] == 'gf66151c1')
    assert d['law'].get('adv') == [], d['law'].get('adv')
    d['law']['adv'] = [ROW]
    print(d['title'], '→', ROW[0], ROW[1])
    if write:
        json.dump(base, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
