# -*- coding: utf-8 -*-
"""Профиль-продавец gc0f11fd7 назывался «ПАО «Газпром» (через АО «Газпром
космические системы»)» и в этом виде был стороной ТРЁХ разных сделок, для
двух из которых уточнение про космические системы бессмысленно.

ЧТО СЛОМАНО. Название верно ровно для ОДНОЙ сделки — g029b7531 («Газпром
продал спутниковый завод Gazprom SPKA»), где 100% продавца, ООО «Газпром
СПКА», действительно принадлежали АО «Газпром космические системы» (это
прямо записано в её собственном `eco.share`, факт не теряется). Но тот же
профиль стоит СЕЛЛЕРОМ у g031152d0 («Газпром продаёт «Газпром нефтехим
Салават» холдингу «Росхим») — нефтехимия к спутникам отношения не имеет —
и БАЙЕРОМ у g94dcc5cc («Газпром может приобрести до 40% Aurus») — про
покупку автопроизводителя источник космические системы не упоминает вовсе.
Похоже, автоимпорт создал один общий профиль «Газпром-продавец» и взял имя
из первой попавшейся карточки, где так угадал, а остальные две получили
чужое уточнение бесплатно.

ПОЧЕМУ НЕ ЧЕРЕЗ `review.py`. Правка касается ИМЕНИ ПРОФИЛЯ КОМПАНИИ
(`companies[...]['name']`), а не поля конкретной сделки — `review.py`
работает только с записями `deals`, а не с `companies`.

Правка: имя профиля укорочено до «ПАО «Газпром»» — верно для всех трёх
сделок; текстовое поле `seller` карточки g031152d0 (дублирующее старое имя
профиля) укорочено тем же способом.

Запуск:
    python3 pipeline/fix_gazprom_seller_profile_name.py            # сухой прогон
    python3 pipeline/fix_gazprom_seller_profile_name.py --write    # записать
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
COMPANY_ID = 'gc0f11fd7'
OLD_NAME = 'ПАО «Газпром» (через АО «Газпром космические системы»)'
NEW_NAME = 'ПАО «Газпром»'
DEAL_ID = 'g031152d0'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    company = data['companies'].get(COMPANY_ID)
    assert company is not None, 'нет компании %s' % COMPANY_ID
    assert company.get('name') == OLD_NAME, \
        'имя компании уже другое: %r' % company.get('name')

    by_id = {d['id']: d for d in data['deals']}
    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('seller') == OLD_NAME, \
        'seller уже другое: %r' % deal.get('seller')

    refs = [d['id'] for d in data['deals']
            if d.get('seller_id') == COMPANY_ID or d.get('buyer') == COMPANY_ID
            or d.get('target') == COMPANY_ID]
    print('профиль %s используется в сделках: %s' % (COMPANY_ID, refs))
    print('company.name: %r -> %r' % (OLD_NAME, NEW_NAME))
    print('%s.seller: %r -> %r' % (DEAL_ID, OLD_NAME, NEW_NAME))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    company['name'] = NEW_NAME
    deal['seller'] = NEW_NAME

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
