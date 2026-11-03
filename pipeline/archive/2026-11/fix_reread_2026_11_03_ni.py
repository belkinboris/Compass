# -*- coding: utf-8 -*-
"""Вычитка базы, партия ni (3 ноября 2026, ночь): то, что таблица FIXES не умеет.
Пара к pipeline/ingest/fixes/reread_2026_11_03_ni.py.

- gccd50095 (VEON/Djezzy), extra. Находка приемки plain_words («а сам VEON…»); «около 96,57% акций
  Djezzy» — наш расчет (51% + 45,57%), RCR Wireless пишет «nearly all of the shares»; «продажа
  контрольного пакета в 2015 году за $2,6 млрд» — в 2015 году FNI заплатил $2,6 млрд за 51%
  (RCR: «The national investment fund purchased a 51% stake in Omnium Telecom Algérie in 2015 for
  $2.6 billion following a decade-long battle between the then-owner and the government»); итог
  $3,3 млрд — RCR («Veon has received a total of $3.3 billion for its whole interest in Djezzy»);
  деньги и депозиты $3,1 млрд на 4 августа 2022 года — релиз VEON. Независимая оценка цены
  перенесена в law.struct (таблица FIXES). Через таблицу не прошло: проверка чисел prose_gate
  не видит чисел перед латинским словом («$2.6 billion», «4 August»), а русского источника с этими
  числами нет.
- g7cb5d8f8 («Альфа-Групп»/«Боржоми»): сумма «$100 млн» → «Не раскрыта». Передача безвозмездная
  (Голос Америки: «Это безвозмездная сделка. Мы получим акции бесплатно»), $100 млн — оценка доли
  премьер-министром Грузии в мае 2022 года (VC.ru); она теперь в eco.val (docs/card_money.md, «Что
  не цена»). Снятое — в retracted.sum, sum_basis «estimate» снимается вместе с суммой.
- g66cb145a («Северсталь»/«Воркутауголь»): юрист покупателя — ALRUD (alrud.com: «ALRUD specialists
  advised Russkaya Energia on the acquisition of Vorkutaugol from Severstal», команда Андрея
  Жарского); прежняя строка «Не раскрывались» — ложное отрицание. Описание профиля покупателя
  ООО «Группа Русская энергия» говорило «ранее принадлежала АО «Антрацит»» — по ЕГРЮЛ наоборот:
  АО «Антрацит» вошло в участники 05.06.2024 (85%), с 03.03.2026 — 100%; на момент сделки
  участники — Роман Троценко (70%) и Андрей Тясто (30%).

    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_ni.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

VEON_EXTRA_OLD = (
    'После закрытия сделки алжирское государство сосредоточило в своих руках около 96,57% акций Djezzy, '
    'а сам VEON за всю историю отношений с Djezzy, включая продажу контрольного пакета в 2015 году за '
    '$2,6 млрд, получил в общей сложности около $3,3 млрд. Цену сделки определила независимая третья '
    'сторона на основе оценки справедливой стоимости актива. Полученные средства направлены на '
    'укрепление ликвидности группы: на 4 августа 2022 года денежные средства и депозиты VEON составили '
    '$3,1 млрд.')
VEON_EXTRA_NEW = (
    'Алжирский фонд FNI купил 51% Omnium Telecom Algérie еще в 2015 году за $2,6 млрд, после '
    'десятилетнего спора прежнего владельца с властями; теперь почти все акции компании у государства. '
    'Всего за свою долю в Djezzy VEON получил $3,3 млрд.\n\n'
    'Деньги от продажи пополнили запас ликвидности группы: на 4 августа 2022 года у VEON было $3,1 млрд '
    'денег и депозитов.')

ADV_PLACEHOLDER = [['Стороны сделки', 'Не раскрывались',
                    'Юридические консультанты в публичных источниках не раскрывались']]
ADV_ALRUD = [['Юридический консультант покупателя (ООО «Русская энергия»)', 'ALRUD',
              'Команду возглавил партнер, руководитель отраслевой группы энергетики, природных ресурсов и '
              'инфраструктуры Андрей Жарский; в нее вошли Олег Ежов, Ксения Ерохина, Александр Шипилов и '
              'Роман Шпунтенко']]

RE_DESC_OLD = ('Холдинговая компания, владеющая угледобывающим АО «Воркутауголь»; ранее принадлежала АО '
               '«Антрацит».')
RE_DESC_NEW = ('Угольный холдинг, купивший в 2022 году АО «Воркутауголь» у «Северстали». На момент сделки '
               'его участники — Роман Троценко (70%) и Андрей Тясто (30%); по ЕГРЮЛ с 2024 года основной '
               'участник — АО «Антрацит», с марта 2026 года — единственный.')


def set_val(obj, key, old, new):
    assert obj.get(key) == old, (key, obj.get(key), old)
    obj[key] = new


def retract(card, field, value):
    lst = card.setdefault('retracted', {}).setdefault(field, [])
    if value not in lst:
        lst.append(value)


def apply(data):
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']

    v = deals['gccd50095']
    set_val(v, 'extra', VEON_EXTRA_OLD, VEON_EXTRA_NEW)

    b = deals['g7cb5d8f8']
    set_val(b, 'sum', '$100 млн', 'Не раскрыта')
    set_val(b['eco'], 'sum', '$100 млн', 'Не раскрыта')
    assert b.get('sum_basis') == 'estimate', b.get('sum_basis')
    b.pop('sum_basis')
    retract(b, 'sum', '$100 млн')

    w = deals['g66cb145a']
    set_val(w['law'], 'adv', ADV_PLACEHOLDER, ADV_ALRUD)
    p = comps['g5d22aa06']
    assert p['name'] == 'ООО «Группа Русская энергия»'
    set_val(p, 'desc', RE_DESC_OLD, RE_DESC_NEW)


def main(argv):
    apply(json.load(open(BASE, encoding='utf-8')))          # сухая проверка assert'ов
    print('gccd50095 extra: «сам VEON», «около 96,57%» → факты RCR и релиза VEON')
    print('g7cb5d8f8 sum: $100 млн → Не раскрыта (retracted.sum)')
    print('g66cb145a law.adv: «Не раскрывались» → ALRUD (покупатель); профиль g5d22aa06: desc')
    if '--write' not in argv:
        print('Сухой прогон; запись — с ключом --write.')
        return 0
    raw = open(BASE, encoding='utf-8').read()                  # перечитываем прямо перед записью
    data = json.loads(raw)
    apply(data)
    out = json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
    with open(BASE, 'w', encoding='utf-8') as f:
        f.write(out)
    print('Записано. Дальше: python3 pipeline/facts_derive.py --write')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
