# -*- coding: utf-8 -*-
"""«АртАйТи» в карточке gc3750bdb: профиль с ИНН и стороны по реестру (9 ноября 2026).

Владелец: «по артайти посмотри ООО «Артайти групп» ИНН 7810877579». В карточке
предмет был текстом с заметкой «ИНН не нашли». ЕГРЮЛ (api-fns, 9 ноября 2026):
ООО «АРТАЙТИ ГРУПП», ОГРН 1127847397413, Санкт-Петербург, с 2012 года. Участники:
Виталий Мальцев — 90% с 22.10.2026 (75% с 2019 года; 21.10.2026 вышел Алексей
Мальцев с 15%), Андрей Сурков — 10% с 2019 года. ГК «Ультиматек» среди участников
на эту дату нет: переход 50% в реестре еще не записан. Продавцом остается текст —
кто из совладельцев продал долю, ни статья, ни реестр не говорят; заметка
приемки переписана по реестру.

    python3 pipeline/archive/2026-11/add_artity_profile_2026_11_09.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
REG = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
CID = 'gartaitigroup'
PROFILE = {'name': 'АртАйТи', 'ind': 'ИТ и интернет', 'legal_short': 'ООО «Артайти групп»',
           'desc': 'Петербургский интегратор «1С»: переводит промышленные предприятия с SAP на «1С». '
                   'Основан в 2012 году Виталием Мальцевым.',
           'kpi': ['Профиль', 'Автоматический']}
REG_ROW = {'company_id': CID, 'decision': 'confirmed', 'inn': '7810877579', 'date': '2026-11-09',
           'reason': 'Владелец 9 ноября 2026 назвал ИНН; ЕГРЮЛ (api-fns): ООО «АРТАЙТИ ГРУПП», ОГРН 1127847397413, '
                     'Санкт-Петербург, основатель и участник с 2012 года — Виталий Мальцев, основатель «АртАйТи» по CNews.'}
OLD_SELLER = 'Прежние совладельцы «АртАйТи» (источник имя не называет)'
NEW_SELLER = 'Совладельцы «АртАйТи» (по ЕГРЮЛ — Виталий Мальцев и Андрей Сурков; кто продал долю, не сообщается)'


def apply_base(data):
    assert CID not in data['companies']
    data['companies'][CID] = PROFILE


def apply_pending(data):
    card = next(c for c in data['cards'] if c['id'] == 'gc3750bdb')
    assert card.get('seller') == OLD_SELLER and not card.get('target')
    card['target'] = CID
    card['seller'] = NEW_SELLER
    notes = card.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    notes.pop('target', None)
    notes['seller'] = ('CNews продавцов не называет; по ЕГРЮЛ на 9 ноября 2026 участники ООО «Артайти групп» — '
                       'Виталий Мальцев (90%) и Андрей Сурков (10%), переход 50% к «Ультиматеку» в реестре еще не записан')


def apply_reg(rows):
    assert not any(r.get('company_id') == CID for r in rows)
    rows.append(REG_ROW)


def main(argv):
    apply_base(json.load(open(BASE, encoding='utf-8')))
    apply_pending(json.load(open(PENDING, encoding='utf-8')))
    apply_reg(json.load(open(REG, encoding='utf-8')))
    if '--write' not in argv:
        print('Сухой прогон.')
        return 0
    for path, fn in ((BASE, apply_base), (PENDING, apply_pending), (REG, apply_reg)):
        fresh = json.load(open(path, encoding='utf-8'))
        fn(fresh)
        json.dump(fresh, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
