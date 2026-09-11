#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Карточка Positive Technologies/CyberOK: имя предмета вместо описания и
кликабельные стороны.

ЧТО УВИДЕЛ ВЛАДЕЛЕЦ (11 сентября 2026, сразу после публикации поста).
В «Структуре сделки» стояло «ПРЕДМЕТ СДЕЛКИ: долю в компании‑разработчике
решений в области кибербезопасности CyberOK» — косвенный падеж, не
вычитано, и вместо имени компании её описание. Ни предмет, ни покупатель
не были кликабельны. Формулировка требования владельца: «должно быть
просто такая-то доля в такой-то компании, или если не известно число —
просто доля или акции в такой-то компании».

ОТКУДА ВЗЯЛОСЬ ОПИСАНИЕ — НЕ ИЗ ПРИТОКА. Скрипт, заведший карточку в
обход ворот (`fix_add_positive_technologies_cyberok.py`), записал предмет
ПРАВИЛЬНО: `asset = 'CyberOK'`. Имя подменило ДОЧИТЫВАНИЕ: запись в
таблице `FIXES` файла `pipeline/ingest/fixes/fix_pt_cyberok_deep_read.py`
меняла `asset` с «CyberOK» на «долю в компании‑разработчике решений в
области кибербезопасности CyberOK» с обоснованием «точнее, чем голое имя
цели». `review.py` эту правку пропустил и был прав по своим правилам:
фраза дословно лежит в источнике. Он проверяет, что текст РЕАЛЕН, но не
знает, что `asset` — это ИМЯ КОМПАНИИ, а не проза (тот же класс, что уже
записан для `law.terms` у HeadHunter/Happy Job: дословная цитата в не
своём поле). Та запись снята из таблицы вместе с этой правкой — оставить
её значило бы требовать, чтобы описание вернулось на место имени.

ПОЧЕМУ СТОРОНЫ НЕ БЫЛИ КЛИКАБЕЛЬНЫ. Профилей ни Positive Technologies, ни
CyberOK в базе не было вовсе, а приток их не заводит: он пишет стороны
текстом (`buyer_name`, `asset`). Замер в день находки: из 145 карточек
притока 107 не имеют ни привязанного предмета, ни привязанного
покупателя — это класс, а не одна карточка, и он чинится отдельно.

ЧТО ДЕЛАЕТ ЭТОТ СКРИПТ (только эта карточка):
  * заводит профиль CyberOK и профиль Positive Technologies;
  * `target` и `buyer` ссылаются на них — предмет и покупатель становятся
    кликабельными, а схема сделки показывает имя компании, а не фразу;
  * `asset` возвращается к чистому имени «CyberOK»;
  * `buyer_name` снимается: пара «ссылка на профиль + текст» не может
    существовать одновременно (это ловит тест);
  * `eco.share` («Предмет / доля» на «Обзоре») говорит по-человечески,
    что куплена доля, размер которой стороны не назвали.

Размер доли не выдумывается: ни РБК, ни пресс-релиз Positive Technologies
его не называют.

Запуск:
    python3 pipeline/fix_cyberok_asset_name_and_party_profiles.py
    python3 pipeline/fix_cyberok_asset_name_and_party_profiles.py --write
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DEAL_ID = 'gdc686ec2'

OLD_ASSET = ('долю в компании‑разработчике решений в области '
             'кибербезопасности CyberOK')
NEW_ASSET = 'CyberOK'

TARGET_ID = 'gcyberok'
TARGET_NAME = 'CyberOK'
TARGET_DESC = ('Российский разработчик решений в области кибербезопасности: '
               'ищет уязвимости на внешнем периметре компании и проверяет, '
               'можно ли их использовать.')

BUYER_ID = 'gpositivetech'
BUYER_NAME = 'Positive Technologies'
BUYER_DESC = ('Российский разработчик решений в области кибербезопасности.')

NEW_SHARE = ('Доля в CyberOK. Размер доли стороны не назвали.')


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    companies = data['companies']
    match_keys = data.setdefault('match_keys', {})

    deal = next((d for d in data['deals'] if d['id'] == DEAL_ID), None)
    assert deal is not None, 'карточка %s не найдена' % DEAL_ID

    # Проверки исходного состояния: если данные уже другие, падаем, а не
    # портим их молча.
    assert deal.get('asset') == OLD_ASSET, \
        'предмет уже другой: %r' % deal.get('asset')
    assert not deal.get('target') and not deal.get('asset_id'), \
        'предмет уже привязан к профилю'
    assert not deal.get('buyer'), 'покупатель уже привязан к профилю'
    assert deal.get('buyer_name') == BUYER_NAME, \
        'покупатель текстом уже другой: %r' % deal.get('buyer_name')
    assert TARGET_ID not in companies, 'профиль %s уже есть' % TARGET_ID
    assert BUYER_ID not in companies, 'профиль %s уже есть' % BUYER_ID
    # Близнец ищется не по ключу теста, а по именам и описаниям всех
    # профилей: под нужным именем в базе может уже стоять другой профиль.
    for cid, c in companies.items():
        blob = ((c.get('name') or '') + ' ' + (c.get('desc') or '')).lower()
        assert 'cyberok' not in blob, 'CyberOK уже упомянут в профиле %s' % cid
        assert c.get('name', '').lower() != 'positive technologies', \
            'профиль Positive Technologies уже есть: %s' % cid

    print('Карточка %s: %s' % (DEAL_ID, deal['title']))
    print('  предмет   : %r' % deal.get('asset'))
    print('           -> %r + ссылка на профиль %s' % (NEW_ASSET, TARGET_ID))
    print('  покупатель: текстом %r' % deal.get('buyer_name'))
    print('           -> ссылка на профиль %s' % BUYER_ID)
    print('  доля      : %r -> %r' % (deal['eco'].get('share'), NEW_SHARE))

    companies[TARGET_ID] = {
        'name': TARGET_NAME,
        'ind': 'ИТ и интернет',
        'desc': TARGET_DESC,
        'kpi': ['Профиль', 'Автоматический'],
    }
    companies[BUYER_ID] = {
        'name': BUYER_NAME,
        'ind': 'ИТ и интернет',
        'desc': BUYER_DESC,
        'kpi': ['Профиль', 'Автоматический'],
    }
    match_keys[TARGET_ID] = ['cyberok', 'сайберок']
    match_keys[BUYER_ID] = ['positive technologies']

    deal['asset'] = NEW_ASSET
    deal['target'] = TARGET_ID
    deal['buyer'] = BUYER_ID
    deal.pop('buyer_name', None)
    deal['eco']['share'] = NEW_SHARE

    assert deal['asset'] == NEW_ASSET
    assert 'buyer_name' not in deal
    assert companies[TARGET_ID]['name'] == TARGET_NAME

    if not write:
        print('\n(сухой прогон, для записи — --write)')
        return

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('\nЗаписано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
