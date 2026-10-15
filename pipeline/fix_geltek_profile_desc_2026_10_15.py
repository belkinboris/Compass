# -*- coding: utf-8 -*-
"""Профиль покупателя «Гельтек» (`g7666e3f4`) держал в `desc` предложение
о МЕХАНИКЕ этой конкретной сделки («Покупку Nomi провёл через свою
100%-ю дочку ООО «Гельтек РНД»») — класс `profile_desc_is_event`
(CARD_ACCEPTANCE_BRIEF.md): описание профиля пересказывает ЭТУ сделку
вместо рода занятий компании. Вдобавок пост сделки («Покупатель: ...»)
печатал только это предложение без имени «Гельтек» — has_novelty()
решил, что имя уже упомянуто внутри («Гельтек РНД» содержит «Гельтек»),
и не напечатал его перед деталью. Предложение о «Гельтек РНД» и так
есть в `eco.share` самой карточки — из профиля убрано, не продублировано.

Запуск:
    python3 pipeline/fix_geltek_profile_desc_2026_10_15.py            # сухой прогон
    python3 pipeline/fix_geltek_profile_desc_2026_10_15.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
COMPANY_ID = 'g7666e3f4'

OLD = ('Российский производитель косметики, владелец — Сергей Кирш; бренды Geltek Baby '
       '(уход за детской кожей) и молодёжная косметика The U. Покупку Nomi провёл через '
       'свою 100%-ю дочку ООО «Гельтек РНД».')
NEW = ('Российский производитель косметики, владелец — Сергей Кирш; бренды Geltek Baby '
       '(уход за детской кожей) и молодёжная косметика The U.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    company = data['companies'][COMPANY_ID]
    assert company['desc'] == OLD, company['desc']

    print('ПРАВКА %s: desc' % COMPANY_ID)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(DATA, encoding='utf-8'))
    assert fresh['companies'][COMPANY_ID]['desc'] == OLD, 'кто-то уже поправил — перечитайте'
    fresh['companies'][COMPANY_ID]['desc'] = NEW
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
