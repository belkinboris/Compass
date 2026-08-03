# -*- coding: utf-8 -*-
"""Починить то, что вскрыло слияние базы в один файл.

ЗАЧЕМ. До 3 августа 2026 девятнадцать кураторских карточек и 36 профилей
компаний жили в `static/index.html` и НИКОГДА не проверялись инвариантами
базы: `test_data.py` читает `deals_promoted.json`. После слияния они попали
под проверки — и семь тестов упали. Это не регресс слияния, а долг, который
слияние сделало видимым.

ЧТО ЧИНИТСЯ.

1. ОТРАСЛЬ ВНЕ СПИСКА. У трёх карточек стояла «Фарма и медицина» — такой
   отрасли в `INDUSTRIES` нет. Все три про клиники и больницу, поэтому
   «Здравоохранение», а не «Фармацевтика»: лечат людей, а не производят
   лекарства.

2. ПРОФИЛИ-БЛИЗНЕЦЫ. `selectel` («Selectel») из кураторского набора и
   `gd4a7c612` («ООО «Селектел»») — одна компания. Это не тот случай, когда
   близнецов оставляют намеренно (иностранный владелец и его российское
   юрлицо, как «Fortum» и ПАО «Фортум»): здесь обе записи об одном
   российском провайдере. Оставляем ту, на которую больше ссылок, вторая
   уходит в `merged_companies` — старый адрес продолжает открываться.

3. ПРЕДМЕТ, ОН ЖЕ СТОРОНА. У `g5ebff17c` («Яндекс» монетизировал инвестиции
   в SPAC) продавец — «Яндекс», и `target` тоже указывал на профиль
   «Яндекса». Раньше эта ссылка вела в никуда (профиля `yandex` в базе не
   было) и правило молчало; теперь профиль есть, и дефект виден. Предмет
   сделки — акции SPAC-компаний, а не сам «Яндекс»: ссылка снимается.

4. СОГЛАСОВАНИЯ, КОТОРЫЕ НЕ СОГЛАСОВАНИЯ. У `domodedovo-aukcion` в поле
   «Согласования» описана процедура торгов, у `adv-erlan` — стадия судебного
   спора. Ни там, ни там нет органа, который что-то согласовал. Текст не
   выбрасывается: он переносится в «Дополнительную информацию», а поле
   становится честно пустым.

Запуск:
    python3 pipeline/fix_after_merge.py            # сухой прогон
    python3 pipeline/fix_after_merge.py --write    # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

IND_FIX = {'Фарма и медицина': 'Здравоохранение'}
TWIN_DROP, TWIN_KEEP = 'selectel', 'gd4a7c612'
ASSET_IS_PARTY = 'g5ebff17c'
APPR_TO_EXTRA = ('domodedovo-aukcion', 'adv-erlan')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    log = []

    # 1. Отрасль
    for d in data['deals']:
        if d.get('ind') in IND_FIX:
            log.append(('отрасль', d['id'], '%s -> %s' % (d['ind'], IND_FIX[d['ind']])))
            if write:
                d['ind'] = IND_FIX[d['ind']]

    # 2. Близнецы
    assert TWIN_DROP in data['companies'] and TWIN_KEEP in data['companies'], \
        'ожидали оба профиля-близнеца на месте'
    refs = sum(1 for d in data['deals']
               for f in ('buyer', 'target', 'seller_id', 'asset_id') if d.get(f) == TWIN_DROP)
    log.append(('близнецы', TWIN_DROP, 'ссылок на удаляемый профиль: %d -> %s' % (refs, TWIN_KEEP)))
    if write:
        for d in data['deals']:
            for f in ('buyer', 'target', 'seller_id', 'asset_id'):
                if d.get(f) == TWIN_DROP:
                    d[f] = TWIN_KEEP
        data.setdefault('merged_companies', {})[TWIN_DROP] = TWIN_KEEP
        data['companies'].pop(TWIN_DROP, None)
        data.get('match_keys', {}).pop(TWIN_DROP, None)

    # 3. Предмет = сторона
    deal = by_id[ASSET_IS_PARTY]
    assert deal.get('target') == 'yandex' and deal.get('seller'), \
        'карточка %s изменилась — перепроверьте' % ASSET_IS_PARTY
    log.append(('предмет=сторона', ASSET_IS_PARTY, 'target «yandex» снят, продавец «%s» остаётся'
                % deal.get('seller')))
    if write:
        deal['target'] = None

    # 4. Согласования, где нет органа
    for did in APPR_TO_EXTRA:
        d = by_id[did]
        appr = str((d.get('law') or {}).get('appr') or '').strip()
        assert appr, '%s: поле «Согласования» уже пусто' % did
        log.append(('согласования', did, appr[:70]))
        if write:
            extra = str(d.get('extra') or '').strip()
            d['extra'] = (extra + ' ' + appr).strip() if extra else appr
            d['law']['appr'] = '—'

    for kind, did, note in log:
        print('  %-16s %-20s %s' % (kind, did, note))
    print('\nвсего правок: %d' % len(log))

    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    else:
        print('Сухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
