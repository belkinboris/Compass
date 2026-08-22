# -*- coding: utf-8 -*-
"""П4 (COMPANY_FINANCE_BRIEF.md): проставляет `holding` профилям, чей `desc`
уже прямо называет группу — и группа уже есть отдельным профилем в базе.

ПОЧЕМУ ЭТО МОЖНО СДЕЛАТЬ БЕЗ НОВОГО ЧТЕНИЯ. Факт («Tele2… входит в группу
«Ростелеком»», «ВТБ Капитал» — «Инвестиционно-банковское подразделение
группы ВТБ») уже утверждён в собственном описании профиля — оно писалось
раньше, отдельной работой (`pipeline/write_company_descriptions*.py`), и не
трогается здесь. Это ПЕРЕНОС уже принятого факта в структурное поле, а не
новое суждение — тот же принцип, что уже применён в
`migrate_holdings_to_company_profiles.py`.

ГРАНИЦА ВЫБОРКИ. Из 67 профилей, чей `desc` вообще упоминает группу/
подразделение, сюда взяты только 16 — где родитель ОДНОЗНАЧНО называется
своим именем И у этого имени уже есть отдельный профиль в COMPANIES. Не
взято намеренно:
  - иностранные материнские структуры без профиля в базе (OBI, Avon,
    Volkswagen Group, BNP Paribas, Zurich, ING, HSBC, BASF, STADA и т. д.) —
    заводить им профиль или нет решается по каждому случаю отдельно
    (CLAUDE.md, «Отдельный справочник для «группы компаний»…»), не пачкой;
  - факты вида «в 2024 году продана X» — это ОДНА сделка (M&A), а не
    постоянная корпоративная структура; `holding` — про второе. CLAUDE.md
    уже различает эти два механизма («Контроль у X» по закрытым сделкам —
    отдельно от `holding`), путать их — значит задвоить один и тот же факт
    двумя разными способами.

ИСТОЧНИК. `desc` самого профиля — не внешняя ссылка на статью, поэтому
`holding.source` НЕ проставляется (в отличие от трёх уже существующих
записей с `source`, добавленных по конкретной статье): выдумывать URL,
которого не открывали, хуже, чем оставить поле пустым — `renderCompany()`
в static/index.html уже умеет показывать бейдж «Входит в группу» без
ссылки (`c.holding.source?...:""`, необязательное поле).
`confidence: "disclosed"` — не «слух», факт уже стоит в опубликованном
описании компании, не помечен как непроверенный.

Запуск: python3 pipeline/link_group_membership_from_descriptions.py
        python3 pipeline/link_group_membership_from_descriptions.py --write
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (id профиля-участника, id профиля-группы, короткое имя группы для лога)
LINKS = [
    ('g107770ca', 'g00f14033', 'Ростелеком'),       # Tele2
    ('g30eba34f', 'g00f14033', 'Ростелеком'),       # Центральный телеграф
    ('g9fe6ac51', 'g7802e51e', 'Ростех'),           # РТ-Капитал
    ('gba4833c4', 'g5c8c6494', 'ЛУКОЙЛ'),           # ЛУКОЙЛ-Коми
    ('g39d25517', 'gcafc31dc', 'ВТБ'),              # ВТБ Капитал
    ('g6d96c661', 'gda7d982b', 'Softline'),         # Софтлайн Проекты
    ('g7814a42a', 'g4e694234', 'VK'),               # My.Games
    ('g592a5a2b', 'g4e694234', 'VK'),               # VK Tech
    ('ge0a3081f', 'gda7d982b', 'Softline'),         # SL Soft
    ('g9cb5f756', 'g69c88bc7', 'МТС'),              # МТС Entertainment
    ('g28add31b', 'g69c88bc7', 'МТС'),              # МТС AI
    ('gac30cf97', 'g28ff15bb', 'Сбербанк'),         # СберИнвест
    ('gf9a640d2', 'g300b9ead', 'Роснефть'),         # Башнефть
    ('gbc5149c2', 'gc0f11fd7', 'Газпром'),          # Группа Газпромбанка
    ('g9492707f', 'gf1f56e08', 'Газпромбанк'),      # ААА Управление Капиталом
    ('gf0ac5fc7', 'gf1f56e08', 'Газпромбанк'),      # Газпромбанк-инвест
]


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    companies = data['companies']

    for member_id, group_id, _label in LINKS:
        assert member_id in companies, 'нет профиля %r' % member_id
        assert group_id in companies, 'нет профиля %r' % group_id
        existing = companies[member_id].get('holding')
        assert not existing, (
            '%s уже несёт holding=%r — состояние изменилось, проверьте вручную'
            % (member_id, existing))

    print('ПРАВИМ (%d профилей):' % len(LINKS))
    for member_id, group_id, label in LINKS:
        print('  %s (%s) -> holding %s (%s)'
              % (member_id, companies[member_id]['name'], group_id, label))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    for member_id, group_id, _label in LINKS:
        companies[member_id]['holding'] = {'id': group_id, 'confidence': 'disclosed'}

    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
