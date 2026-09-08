# -*- coding: utf-8 -*-
"""Карточка ТРК «Родник» и «Алмаз»: стороны становятся профилями, а не текстом.

ЧТО ЧИНИТ. Владелец 8 сентября 2026: «Очень плохая карта про тц родник и
алмаз… в ссылке ведомостей написано ооо «Центр инжиниринговых услуг при
проектировании и строительстве» оно такое одно, значит как минимум продавец
должен быть кликабельный. В структуре сделки вообще нет предмета, хотя это
очевидно два тц. Вроде как в источниках написано, что они остались от макфы,
этого нигде не написано у нас. И активы принадлежали государству когда у макфы
национализированы, значит продавец тоже ясен».

Первая половина замечания снята слиянием дубля
(`pipeline/merge_specs/2026-09-08-ciups-rodnik-almaz.json`): владелец смотрел
карточку `g10bfcb70`, заведённую притоком 7 сентября со стороны покупателя,
тогда как та же сделка уже месяц лежала в базе карточкой
`gmru-psb-tpk-chelyabinsk` со стороны продавца — с Макфой, Росимуществом,
площадями обоих ТРК и всеми четырьмя раундами торгов. Слияние вернуло эти
факты и перенесло на них живой пост канала.

Этот скрипт закрывает вторую половину — то, чего не было НИ В ОДНОЙ из двух
карточек: сторон, по которым можно кликнуть.
  * ПОКУПАТЕЛЬ стоял текстом (`buyer_name`). Имя уникально: в ЕГРЮЛ ровно одно
    юрлицо «Центр инжиниринговых услуг при проектировании и строительстве» —
    ИНН 7811793787, ОГРН 1237800136012, Санкт-Петербург, гендиректор Белов
    Тимофей Александрович; Ведомости называют владельцем Тимофея Белова —
    имя и роль совпадают. Заводится профиль `gciups`, `buyer_name` снимается
    (у покупателя либо профиль, либо текст — `test_buyer_is_named_once`).
  * ПРЕДМЕТ не был связан ни с чем: `target` пуст, `asset` — только текст, и
    на экране плашка «Структура сделки» показывала предмет пустым местом
    (`assetName = targetName || (assetWillShow ? assetTextRaw : "")`, а
    `assetWillShow` у дубля был ложью — текст предмета дословно повторял
    заголовок). Продавали ДВА юрлица одним лотом: ООО «Родник» (ИНН
    7452045112, ОГРН 1057424047834) и ООО «Управляющая компания «Содействие»»
    (ИНН 7452079175, ОГРН 1107452004857) — у обоих в ЕГРЮЛ одна и та же
    управляющая организация, ООО «РСХБ-Финанс». Поэтому профиль `grodnik-almaz`
    заводится с признаком `lot`, а состав лота назван в описании — по правилу
    «имя профиля — компания, а не состав сделки» (`test_lot_profile_
    composition_is_named_somewhere_the_reader_sees`). Отдельного профиля на
    одно юрлицо из двух не заводим намеренно: у сделки одно поле «предмет», и
    выбрать одно юрлицо из двух значило бы потерять половину лота.
  * ПРОДАВЕЦ стоял текстом «ПСБ» — а это агент, а не собственник. Активы
    обращены в доход государства по иску Генпрокуратуры (Центральный районный
    суд Челябинска, май 2024), и на торги их выставляло Росимущество — это
    уже стоит дословно в `eco.context` самой карточки. Продавцом становится
    профиль Росимущества (`g9fd82fee`), а роль ПСБ («отвечающий за продажу
    государственного имущества») названа в `law.struct`, где она и есть.
  * ЗАГОЛОВОК описывал ЛИСТИНГ («ПСБ выставил на продажу компании…»), хотя
    сделка закрыта и покупатель известен. Переписан на закрытие.

ПОЧЕМУ ОДНОРАЗОВЫЙ СКРИПТ, А НЕ ТАБЛИЦА FIXES. `review.py` умеет дописывать
поля по дословной цитате источника, но не умеет ни заводить профиль, ни
менять заголовок, ни переставлять роль стороны с текста на ссылку — это тот
же класс, что и `fix_mortehprom_profile_title_date.py`.

Запуск:
    python3 pipeline/fix_ciups_rodnik_almaz_parties.py            # сухой прогон
    python3 pipeline/fix_ciups_rodnik_almaz_parties.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'

DEAL_ID = 'gmru-psb-tpk-chelyabinsk'
BUYER_ID = 'gciups'
TARGET_ID = 'grodnik-almaz'
ROSIM_ID = 'g9fd82fee'          # Росимущество, уже есть в базе

OLD_TITLE = 'ПСБ выставил на продажу компании, владеющие двумя ТРК в Челябинске'
NEW_TITLE = ('ЦИУПС купил у государства ТРК «Родник» и «Алмаз» в Челябинске '
             'за 6,08 млрд ₽')
OLD_BUYER_NAME = 'ООО «Центр инжиниринговых услуг при проектировании и строительстве» (Тимофей Белов)'
OLD_SELLER = 'ПСБ'
NEW_SELLER = 'Росимущество'

BUYER_PROFILE = {
    'name': 'ЦИУПС',
    'ind': 'Недвижимость',
    'desc': ('ООО «Центр инжиниринговых услуг при проектировании и строительстве» '
             'из Санкт-Петербурга, принадлежит Тимофею Белову. Скупает на торгах '
             'обращённые в доход государства активы в Челябинске: до торговых '
             'комплексов «Родник» и «Алмаз» купило отель Radisson Blu за '
             '1,342 млрд ₽.'),
    'kpi': ['Профиль', 'Прочитан'],
}
BUYER_KEYS = ['циупс', 'центр инжиниринговых услуг при проектировании и строительстве']

TARGET_PROFILE = {
    'name': 'Родник',
    'ind': 'Недвижимость',
    'desc': ('Владелец двух торгово-развлекательных комплексов в Челябинске — '
             '«Родник» на 126 тыс. кв. м и «Алмаз» на 212 тыс. кв. м, оба входят '
             'в сотню крупнейших торговых центров России. Входил в холдинг '
             '«Макфа», в 2024 году обращён в доход государства и в 2026 году '
             'продан одним лотом: ООО «Родник» и ООО «Управляющая компания '
             '«Содействие»».'),
    'lot': True,
    'kpi': ['Профиль', 'Прочитан'],
}
TARGET_KEYS = ['родник']


def main(write=False):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    deal = next((d for d in data['deals'] if d['id'] == DEAL_ID), None)
    assert deal, 'карточки %s нет в базе' % DEAL_ID

    # Проверки исходного состояния: скрипт падает, а не портит уже изменённые
    # данные (правило репозитория «assert на исходное состояние поля»).
    assert deal.get('title') == OLD_TITLE, deal.get('title')
    assert deal.get('buyer') is None, deal.get('buyer')
    assert deal.get('buyer_name') == OLD_BUYER_NAME, deal.get('buyer_name')
    assert deal.get('target') is None, deal.get('target')
    assert deal.get('asset_id') is None, deal.get('asset_id')
    assert deal.get('seller') == OLD_SELLER, deal.get('seller')
    assert deal.get('seller_id') is None, deal.get('seller_id')
    assert BUYER_ID not in data['companies'], 'профиль %s уже есть' % BUYER_ID
    assert TARGET_ID not in data['companies'], 'профиль %s уже есть' % TARGET_ID
    assert ROSIM_ID in data['companies'], 'профиля Росимущества нет'
    # Слияние дубля должно быть уже применено — иначе стороны уедут на карточку,
    # рядом с которой продолжает жить вторая, про ту же сделку.
    assert data.get('merged', {}).get('g10bfcb70') == DEAL_ID, \
        'сначала слияние дубля g10bfcb70 (pipeline/merge_duplicate_deals_batch.py)'

    print('=== профиль покупателя %s ===' % BUYER_ID)
    print(json.dumps(BUYER_PROFILE, ensure_ascii=False, indent=1))
    print('=== профиль предмета %s (лот) ===' % TARGET_ID)
    print(json.dumps(TARGET_PROFILE, ensure_ascii=False, indent=1))
    print('=== карточка %s ===' % DEAL_ID)
    print(' title:   %r\n       -> %r' % (OLD_TITLE, NEW_TITLE))
    print(' buyer:   текст %r -> профиль %s' % (OLD_BUYER_NAME, BUYER_ID))
    print(' target:  нет -> профиль %s (лот)' % TARGET_ID)
    print(' seller:  %r -> %r + профиль %s' % (OLD_SELLER, NEW_SELLER, ROSIM_ID))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    data['companies'][BUYER_ID] = BUYER_PROFILE
    data['companies'][TARGET_ID] = TARGET_PROFILE
    data.setdefault('match_keys', {})[BUYER_ID] = BUYER_KEYS
    data['match_keys'][TARGET_ID] = TARGET_KEYS

    deal['title'] = NEW_TITLE
    deal['buyer'] = BUYER_ID
    deal.pop('buyer_name', None)
    deal['target'] = TARGET_ID
    deal['seller'] = NEW_SELLER
    deal['seller_id'] = ROSIM_ID

    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    print('\nЗаписано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
