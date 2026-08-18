# -*- coding: utf-8 -*-
"""Убирает захардкоженный `HOLDINGS` из static/index.html как источник данных
о группах компаний: у `company.holding.id` теперь ОДИН смысл — id профиля в
`COMPANIES`, а не ключ отдельного, невидимого проверкам объекта.

Почему это дефект, а не стиль: `renderCompany()` резолвит группу через
`HOLDINGS[c.holding.id]`, а не через `co(c.holding.id)`. У профиля
«УГМК-Инвест» (ugmkinvest) `holding.id` уже указывал на реальный профиль
«УГМК» (g3a8fb04f) — так и было задумано в `fix_petropavlovsk_buyer_and_
asset_case.py` («Новый профиль связан с УГМК через `holding`, чтобы это не
потерялось») — но `HOLDINGS['g3a8fb04f']` не существует, и вся ссылка молча
не рендерилась: ни бейджа «Входит в группу» у УГМК-Инвест, ни списка
дочерних компаний на странице самой УГМК. Тот же класс дефекта, что и
«текстовое поле стороны может быть невидимым» (BM-банк/RWB): факт записан в
данных, правильно связан, и не виден на экране.

Второй, более тонкий случай — дубль сущности. `HOLDINGS.vamin_tatarstan`
(«Группа «Вамин Татарстан»») существовал ОТДЕЛЬНО от уже имеющегося профиля
`g896e444d` («Вамин Татарстан») — та же компания оказалась представлена
дважды: один раз как настоящий профиль (без единой сделки, без ссылки), один
раз как текст в чужом объекте. Правка: `g2cbdb3e8` («Вамин Р», покупатель
актива Danone) указывает на существующий `g896e444d`, а не на новый профиль.

`HOLDINGS.arnest` дубля не имеет — ни один профиль «Арнест» (не «Арнест
Юнирусь») в базе не заведён. Здесь миграция — не слияние, а перенос:
`HOLDINGS['arnest']` становится профилем `COMPANIES['arnest']` с тем же id,
именем и описанием, так что `gb700e4d9.holding.id == 'arnest'` продолжает
резолвиться без изменений.

После этой правки `HOLDINGS` в `static/index.html` пуст и удаляется отдельной
правкой интерфейса (не этим скриптом — он трогает только JSON).

Запуск: python3 pipeline/migrate_holdings_to_company_profiles.py           # проверка
        python3 pipeline/migrate_holdings_to_company_profiles.py --write   # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

ARNEST_ID = 'arnest'
ARNEST_MEMBER = 'gb700e4d9'
ARNEST_NAME = '«Арнест»'
ARNEST_DESC = ('Российский производитель товаров личной гигиены и бытовой '
               'химии (аэрозоли, косметика); контролируется Алексеем '
               'Сагалом.')

VAMIN_MEMBER = 'g2cbdb3e8'
VAMIN_OLD_HOLDING_ID = 'vamin_tatarstan'
VAMIN_REAL_PROFILE = 'g896e444d'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    companies = data['companies']
    cards = {d['id']: d for d in data['deals']}

    assert ARNEST_ID not in companies, (
        'профиль %r уже существует — не перезаписываем' % ARNEST_ID)
    arnest_member = companies[ARNEST_MEMBER]
    assert arnest_member.get('holding', {}).get('id') == ARNEST_ID, (
        'ожидался holding.id=%r у %s, сейчас %r — состояние изменилось'
        % (ARNEST_ID, ARNEST_MEMBER, arnest_member.get('holding')))

    assert VAMIN_REAL_PROFILE in companies, (
        'ожидался существующий профиль %r — состояние изменилось'
        % VAMIN_REAL_PROFILE)
    vamin_member = companies[VAMIN_MEMBER]
    assert vamin_member.get('holding', {}).get('id') == VAMIN_OLD_HOLDING_ID, (
        'ожидался holding.id=%r у %s, сейчас %r — состояние изменилось'
        % (VAMIN_OLD_HOLDING_ID, VAMIN_MEMBER, vamin_member.get('holding')))

    print('ПРАВИМ:')
    print('  + новый профиль %r («Арнест») — перенос из HOLDINGS' % ARNEST_ID)
    print('  ~ %s: holding.id %r -> %r (существующий профиль «Вамин Татарстан»)'
          % (VAMIN_MEMBER, VAMIN_OLD_HOLDING_ID, VAMIN_REAL_PROFILE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    companies[ARNEST_ID] = {
        'name': ARNEST_NAME,
        # Та же отрасль, что уже стоит у дочернего профиля (gb700e4d9) —
        # не вводим новое суждение о классификации, только переносим старое.
        'ind': arnest_member['ind'],
        'desc': ARNEST_DESC,
    }
    vamin_member['holding']['id'] = VAMIN_REAL_PROFILE

    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
