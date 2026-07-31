#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Предмет сделки ЛСР/Domina Пулково ссылался на профиль человека, а не актива.

ЧТО СЛОМАНО. Карточка `g7bbe19c2` («Группа ЛСР приобрела гостиничный комплекс
Domina Пулково») хранит `target: "g309e931d"`, а профиль `g309e931d` называется
«Владимир Селегень» — имя человека, не юрлицо и не актив. На экране это была
самая заметная витрина дефекта: блок «По этой сделке раскрыто немного деталей»
у карточки «Агрострой» вёл на эту же сделку как на «более подробную» (по праву:
у неё 6 источников и разбор на несколько абзацев), а внутри читатель видел
«Предмет сделки: Владимир Селегень» — бессмыслицу для сделки про отель.

ПОЧЕМУ ИМЕННО ТАК И НЕ ИНАЧЕ. Текст самой карточки (`eco.share`, `extra`)
называет предмет дословно: «100% долей ООО «Пулково Скай» и ООО «УК Статус»,
владеющих гостиничным комплексом Domina Пулково». Это лот из двух юрлиц — тот
же случай, что уже описан в CLAUDE.md («Имя компании — не место для доли» и
соседний класс «лот из нескольких юрлиц»): у сделки одно поле «предмет», и
делить лот на два профиля значило бы выбрать одно юрлицо вместо двух. Новый
профиль называется «ООО «Пулково Скай» и ООО «УК Статус»» с признаком `lot`,
как и девять уже существующих профилей-лотов, — образец взят из них дословно
(`kpi:["Профиль","Автоматический"]`, `lot:true`).

ПРОВЕРЕНО, ЧТО «ВЛАДИМИР СЕЛЕГЕНЬ» — НЕ ЧЬЁ-ТО ПОТЕРЯННОЕ ИМЯ. Полнотекстовый
поиск по всем 1332 сделкам не находит «Селегень»/«Селегеня» ни в одном поле,
кроме самой ссылки `target`, — ни как продавца, ни как бенефициара. Профиль
использовался ровно в одной сделке и ни разу не упомянут текстом рядом. Это не
потерянный факт, а испорченная ссылка, поэтому профиль удаляется целиком, а не
переименовывается: переименование сохранило бы неверную запись под другим
именем.

Запуск:
    python3 pipeline/fix_pulkovo_target_profile.py            # сухой прогон
    python3 pipeline/fix_pulkovo_target_profile.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'g7bbe19c2'
BAD_PROFILE_ID = 'g309e931d'
BAD_PROFILE_NAME = 'Владимир Селегень'
NEW_PROFILE_ID = 'g7bbe19c2-target'
NEW_PROFILE_NAME = 'ООО «Пулково Скай» и ООО «УК Статус»'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    companies = data['companies']
    match_keys = data['match_keys']

    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    assert deal.get('target') == BAD_PROFILE_ID, \
        '%s: target уже не %s (сейчас %r) — правка уже применена или сделка изменилась' % (
            DEAL_ID, BAD_PROFILE_ID, deal.get('target'))

    bad = companies.get(BAD_PROFILE_ID)
    assert bad is not None, 'нет профиля %s' % BAD_PROFILE_ID
    assert bad.get('name') == BAD_PROFILE_NAME, \
        '%s: имя профиля не совпадает дословно: %r' % (BAD_PROFILE_ID, bad.get('name'))

    # Профиль использован РОВНО в одной сделке и нигде не упомянут текстом —
    # проверяем это на месте, а не полагаемся на замер из докстринга.
    refs = [d['id'] for d in data['deals']
            if BAD_PROFILE_ID in (d.get('target'), d.get('buyer'), d.get('seller_id'), d.get('asset_id'))]
    assert refs == [DEAL_ID], 'профиль %s используется не только в %s: %r' % (BAD_PROFILE_ID, DEAL_ID, refs)
    for d in data['deals']:
        blob = json.dumps(d, ensure_ascii=False).lower()
        assert 'елеген' not in blob, \
            '%s: упоминание фамилии найдено в тексте сделки — профиль может быть не лишним' % d['id']

    assert NEW_PROFILE_ID not in companies, 'профиль %s уже существует' % NEW_PROFILE_ID

    print('Сделка: %s | было target=%s (%r)' % (DEAL_ID, BAD_PROFILE_ID, BAD_PROFILE_NAME))
    print('Станет: target=%s (%r, lot=true)' % (NEW_PROFILE_ID, NEW_PROFILE_NAME))
    print('Удаляется профиль: %s (%r) — использовался только здесь, нигде не упомянут текстом' % (
        BAD_PROFILE_ID, BAD_PROFILE_NAME))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    companies[NEW_PROFILE_ID] = {
        'name': NEW_PROFILE_NAME,
        'ind': bad.get('ind', 'Недвижимость'),
        'desc': 'Описание компании пока не добавлено.',
        'kpi': ['Профиль', 'Автоматический'],
        'lot': True,
    }
    deal['target'] = NEW_PROFILE_ID
    del companies[BAD_PROFILE_ID]
    if BAD_PROFILE_ID in match_keys:
        del match_keys[BAD_PROFILE_ID]

    assert by_id[DEAL_ID]['target'] == NEW_PROFILE_ID
    assert NEW_PROFILE_ID in companies and companies[NEW_PROFILE_ID]['name'] == NEW_PROFILE_NAME
    assert BAD_PROFILE_ID not in companies
    assert BAD_PROFILE_ID not in match_keys

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
