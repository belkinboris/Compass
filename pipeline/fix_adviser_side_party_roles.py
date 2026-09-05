# -*- coding: utf-8 -*-
"""Пять карточек, у которых сторона сделки записана не в ту роль (или не
записана вовсе) — нашлись не чтением карточек, а замером «за кого выступала
фирма» на странице консультанта (5 сентября 2026, вопрос владельца о Nextons:
«неужели из контекста не понятно, с какой стороны они были?»).

ПОЧЕМУ ЭТО ВИДНО ИМЕННО ТАМ. Новый `advSide` в static/index.html узнаёт
сторону консультанта ещё и по ИМЕНИ стороны в тексте роли или заметки
(«консультировала Ingka…», «на стороне Группы Сбер»). Имя ищется среди
полей `buyer`/`seller`/`target` самой карточки — и если сторона записана в
чужую роль, консультант получает чужую сторону: ALUMNI Partners у Softline
показывалась «за саму компанию», потому что покупатель «Вертикаль
Инвестиции» стоял в `target`. Замер по всем 229 парам фирма-сделка нашёл
пять таких карточек; остальные — верные.

ЧТО ЧИНИТСЯ (по заголовку и `eco.share` самой карточки, без новых фактов):
- ge9937266 «Покупка Sk Capital (холдинг «Вертикаль Инвестиции») более 10%
  акций ПАО «Софтлайн»»: в `target` стоял ПОКУПАТЕЛЬ (профиль «Вертикаль
  Инвестиции»), предмет — Softline — не был привязан вовсе. Теперь
  buyer → «Вертикаль Инвестиции», target → Softline (профиль gda7d982b).
- g92107ce6 «Приобретение Cosmos Hotel Group (АФК «Система») 100% долей в
  компаниях-владельцах 10 отелей»: в `target` стоял покупатель АФК «Система».
  Теперь buyer → АФК «Система», target снимается: у компаний-владельцев
  отелей профиля нет, предмет назван заголовком и `eco.share`.
- gedc48d89 «Приобретение Группой Сбер 41,9% акций ПАО «Элемент»»:
  покупатель не был записан вовсе — buyer → Сбербанк (g28ff15bb).
- g2d525daa «Продажа российского шинного бизнеса Nokian Tyres компании
  «Татнефть»»: продавец не записан; `target` — профиль российского бизнеса
  Nokian. Продавец — Nokian Tyres plc, текстом (у материнской компании
  своего профиля нет, и плодить его ради одной сделки не стоит).
- ga46c5b15 «ВТБ и АФК «Система»: структурная инвестиционная сделка на
  320 млрд ₽ под залог акций Ozon» (тип «Финансирование»): в `target` стоял
  ВТБ — тот, кто даёт деньги. У сделок этого типа плашка сторон читает
  `buyer` как инвестора, а `target` — как получателя средств: buyer → ВТБ,
  target → АФК «Система».

Запуск: python3 pipeline/fix_adviser_side_party_roles.py
        python3 pipeline/fix_adviser_side_party_roles.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

FIXES = {
    'ge9937266': {'assert': {'target': 'g8487ae57', 'buyer': None, 'buyer_name': None},
                  'set': {'buyer': 'g8487ae57', 'target': 'gda7d982b'}},
    'g92107ce6': {'assert': {'target': 'gc2792a44', 'buyer': None, 'buyer_name': None},
                  'set': {'buyer': 'gc2792a44', 'target': None}},
    'gedc48d89': {'assert': {'buyer': None, 'buyer_name': None, 'target': 'g075196ef'},
                  'set': {'buyer': 'g28ff15bb'}},
    'g2d525daa': {'assert': {'seller': None, 'seller_id': None, 'buyer': 'g98105961', 'target': 'g42a4ea0b'},
                  'set': {'seller': 'Nokian Tyres plc'}},
    'ga46c5b15': {'assert': {'target': 'gcafc31dc', 'buyer': None, 'buyer_name': None},
                  'set': {'buyer': 'gcafc31dc', 'target': 'gc2792a44'}},
}
NAMES = {'g8487ae57': 'Вертикаль Инвестиции', 'gda7d982b': 'Softline', 'gc2792a44': 'АФК «Система»',
         'g28ff15bb': 'Сбербанк', 'g42a4ea0b': 'Nokian Tyres', 'gcafc31dc': 'ВТБ'}


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    co = data['companies']
    for cid, name in NAMES.items():
        assert co[cid]['name'] == name, (cid, co[cid]['name'])
    by_id = {d['id']: d for d in data['deals']}
    for did, fx in FIXES.items():
        deal = by_id[did]
        for k, v in fx['assert'].items():
            assert deal.get(k) == v, (did, k, deal.get(k))
        print(did, deal['title'][:70])
        for k, v in fx['set'].items():
            print('  %s: %r -> %r' % (k, deal.get(k), v))
            if write:
                if v is None:
                    deal.pop(k, None)
                else:
                    deal[k] = v
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
