# -*- coding: utf-8 -*-
"""Этап 8, П4-8: заполняет `holding`/`ownership` из ЕГРЮЛ-состава участников
(тех самых снапшотов ФНС, которые уже собраны для 323 подтверждённых
компаний реестра, — `sync_entity()` в `pipeline/sync_fns.py` пишет их живьём
в боевую базу на каждом синке). Партнёры прямо сказали: главная жила для
групп компаний — ЕГРЮЛ, а не ручная desc-кампания (П4-7 — вторична).

КАК НАЙДЕНЫ КАНДИДАТЫ. Живой прогон (25 августа 2026, читает только —
GET `https://projectcompass.ru/api/companies/<id>/fns`) прошёл все 323
подтверждённые компании реестра (`fns_registry.confirmed_inns()`), у каждой
взял `ownership.current` (текущий состав участников по ЕГРЮЛ) и оставил
только тех учредителей, чей ИНН СОВПАДАЕТ с ИНН другой уже подтверждённой
компании нашей же базы — это и есть «юрлицо-учредитель с долей, у которого
есть профиль в базе», как просили партнёры. Из 9 таких совпадений:

- 4 отброшены МЕХАНИЧЕСКИ: `is_ao=true` — ЕГРЮЛ хранит для АО не текущих
  акционеров, а учредителей на момент регистрации (реестр акционеров ведёт
  не ФНС, а регистратор/депозитарий), и переносить это в `holding` как
  «входит в группу СЕЙЧАС» значило бы утверждать то, чего данные не говорят
  (правило из брифа, П4-8: «для АО-форм ЕГРЮЛ-учредителей в ownership НЕ
  переносить»). Кандидаты: Северсталь/[дочка АО], Ростелеком/[дочка АО]×2,
  Норникель/[дочка АО] — все со снапшотом 2003–2006 года, что и подтверждает
  диагноз («исторический артефакт»).
- 5 прочитаны вручную (карточка компании, `desc`, при необходимости — уже
  записанная в нашей базе сделка) и разделены по СМЫСЛУ доли, а не по
  формальному факту совпадения ИНН:
    * 100% и majority (>50%) — это `holding` (контроль, «входит в группу»):
      «Абсолют Страхование» ← ЦАНЦ (100%, ровно та сделка, которую наша же
      база уже знает — `absolut-strah`/merge 16 августа); «Энгельс
      Электроинструменты» ← «Е1 Групп» (100%, наш же `desc` у Е1 Групп
      говорит «в 2026 году купила завод Энгельс Электроинструменты» —
      дословное подтверждение); БИК ← МТС (50,1%, наша же карточка сделки
      `mts-bik` говорит «МТС сохраняет 50,1% и совместный контроль» — не
      противоречие с `desc` «до сделки — актив группы МТС», а точное
      совпадение: часть проданно, контроль удержан).
    * <50% — это НЕ `holding` (доля без контроля, значит не «входит в
      группу»), а `ownership` на профиле ВЛАДЕЛЬЦА (портфель, тот же
      механизм, что уже показывает «АФК Система — МТС» на сайте): «АБ
      Холдинг» (головная структура Альфа-банка) владеет 22% «Кассир.ру» —
      наш собственный `desc` у «АБ Холдинг» уже называет это текстом
      («инвестирует в… Kassir.ru»), здесь факт просто переносится в
      структурное поле; «БФТ-Холдинг» владеет 49% «Полиматика Рус» — доля
      чуть меньше половины, `desc` компании об этом молчит, но сама доля
      (не большинство) решает: это НЕ контроль.

Источник — сам API `/api/companies/<id>/fns` (публичный, без токена),
поэтому `source` для каждой записи — прямая ссылка на него: читатель может
открыть тот же JSON и увидеть исходный снапшот ЕГРЮЛ своими глазами, а не
верить подписи на слово.

Запуск: python3 pipeline/link_egrul_founders_to_holding.py           # проверка
        python3 pipeline/link_egrul_founders_to_holding.py --write   # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

API = 'https://projectcompass.ru/api/companies/%s/fns'

# --- контроль (>=50%) -> company.holding + group:true у владельца ---------
HOLDING = [
    # (дочка, владелец, доля, дата среза ЕГРЮЛ)
    ('absolutstrah', 'canc', '100%', '2026-07-06'),
    ('ge788d903', 'g417388ed', '100%', '2026-02-25'),
    ('bik', 'g69c88bc7', '50,1%', '2026-07-03'),
]

# --- доля без контроля (<50%) -> company.ownership у владельца ------------
OWNERSHIP = [
    # (владелец, дочка, доля, дата среза ЕГРЮЛ)
    ('g67e6a0e1', 'g030deb34', '22%', '2022-08-30'),
    ('ged6b4e16', 'g04181f17', '49%', '2026-01-14'),
]


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    companies = data['companies']

    print('HOLDING (контроль, "Входит в группу"):')
    for child_id, parent_id, share, as_of in HOLDING:
        assert child_id in companies, 'нет профиля %r — состояние изменилось' % child_id
        assert parent_id in companies, 'нет профиля %r — состояние изменилось' % parent_id
        child = companies[child_id]
        assert not child.get('holding'), (
            '%s уже несёт holding=%r — состояние изменилось, разбирать вручную'
            % (child_id, child['holding']))
        print('  %s (%s) -> %s (%s), доля %s, ЕГРЮЛ на %s'
              % (child_id, child['name'], parent_id, companies[parent_id]['name'], share, as_of))

    print('OWNERSHIP (доля без контроля, портфель):')
    for parent_id, child_id, share, as_of in OWNERSHIP:
        assert parent_id in companies, 'нет профиля %r — состояние изменилось' % parent_id
        assert child_id in companies, 'нет профиля %r — состояние изменилось' % child_id
        parent = companies[parent_id]
        existing = [o for o in (parent.get('ownership') or []) if o.get('id') == child_id]
        assert not existing, (
            '%s уже несёт долю в %r — состояние изменилось, разбирать вручную'
            % (parent_id, child_id))
        print('  %s (%s) владеет %s -> %s (%s), ЕГРЮЛ на %s'
              % (parent_id, parent['name'], share, child_id, companies[child_id]['name'], as_of))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    for child_id, parent_id, share, as_of in HOLDING:
        child = companies[child_id]
        parent = companies[parent_id]
        child['holding'] = {
            'id': parent_id,
            'confidence': 'disclosed',
            'source': ['ЕГРЮЛ (данные ФНС), доля %s на %s' % (share, as_of), API % child_id],
        }
        parent['group'] = True

    for parent_id, child_id, share, as_of in OWNERSHIP:
        parent = companies[parent_id]
        child = companies[child_id]
        parent.setdefault('ownership', []).append({
            'name': child['name'],
            'id': child_id,
            'share': share,
            'as_of': as_of,
            'source': ['ЕГРЮЛ (данные ФНС)', API % child_id],
        })

    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
