# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень): дочитывание
`g7ad4e39d» («Консорциум российских инвесторов приобретает российский
бизнес Henkel», Подписана) обернулось находкой дубля. Та же самая
сделка (продажа Henkel российского бизнеса консорциуму Харитонина/
Таврина/Крюкова) уже полностью описана в `g6f4a071a` («Henkel продала
российский бизнес (Lab Industries) консорциуму инвесторов», Закрыта,
дата закрытия 2023-05-04) — карточка гораздо полнее: точный состав
консорциума с долями, полная сумма, консультант продавца (EY),
опцион обратного выкупа, шесть источников, уже пройден полный цикл
дочитывания (`deep_researched`/`weekly_researched`/`followup_researched`
= 2026-08-15). `g7ad4e39d` при этом стояла беднее (почти все eco/law
поля — прочерк) и с устаревшим статусом «Подписана».

Родня уже записанного в CLAUDE.md урока: у той же сделки задвоился и
профиль ПРЕДМЕТА — `gf2c1da31` («российский бизнес Henkel») и
`g14db9bb2` («Lab Industries») описывают ОДНО И ТО ЖЕ юрлицо (бывшее
ООО «Хенкель Рус», ИНН 7702691545, переименовано в ООО «ЛАБ
Индастриз» 15 мая 2023 года) — оба профиля дословно называют тот же
состав покупателей (Augment Investments/Kismet Capital Group/Elbrus
Services). `gf2c1da31` использовался ТОЛЬКО в удаляемой карточке
`g7ad4e39d`, match_keys на него нет — удаляется вместе с карточкой без
потери связей.

Проверено: обе карточки описывают ОДНУ сделку с идентичными фактами
(сумма 54 млрд ₽ / €600 млн, дата подписания 20.04.2023, консорциум с
теми же тремя участниками) — не совпадение, а дубль. `g6f4a071a`
не тронута; `g7ad4e39d` удаляется, адрес `#/deal/g7ad4e39d` через
`merged` ведёт на `g6f4a071a`.

FIXES-запись `id='g7ad4e39d', field='sum'` (batch_agents100_r8.py) снята
отдельно, тем же заходом — правка к удаляемой карточке не должна
оставаться в таблице (см. урок «Слияние дублей обязано снять правки к
удалённой карточке вместе с ней»); тот же факт (54 млрд ₽) уже стоит в
`g6f4a071a` через собственную запись.

Запуск: python3 pipeline/merge_henkel_lab_industries_dup.py
        python3 pipeline/merge_henkel_lab_industries_dup.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DUP_DEAL = 'g7ad4e39d'
KEEP_DEAL = 'g6f4a071a'
DUP_COMPANY = 'gf2c1da31'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    assert any(d['id'] == DUP_DEAL for d in data['deals'])
    assert any(d['id'] == KEEP_DEAL for d in data['deals'])
    assert DUP_COMPANY in data['companies']
    assert data.get('merged', {}).get(DUP_DEAL) is None
    refs = [d['id'] for d in data['deals']
            if d['id'] != DUP_DEAL and DUP_COMPANY in
            (d.get('buyer'), d.get('seller_id'), d.get('target'), d.get('asset_id'))]
    assert refs == [], 'профиль %s используется ещё где-то: %s' % (DUP_COMPANY, refs)

    print('Удаляется карточка:', DUP_DEAL)
    print('Оставшаяся карточка:', KEEP_DEAL)
    print('Удаляется профиль компании:', DUP_COMPANY, '->', data['companies'][DUP_COMPANY])
    print('merged[%r] = %r' % (DUP_DEAL, KEEP_DEAL))

    if write:
        data['deals'] = [d for d in data['deals'] if d['id'] != DUP_DEAL]
        data.setdefault('merged', {})[DUP_DEAL] = KEEP_DEAL
        del data['companies'][DUP_COMPANY]
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
