# -*- coding: utf-8 -*-
"""Недельная очередь качества, 11 сентября 2026 — дочитывание карточки
`g70c0a9ff` («НМГ купила контрольный пакет ИД «Комсомольская правда»»,
закрыта 3 сентября 2026, дочитана в тот же день).

Дельта-поиск (саб-агент + личная проверка WebFetch) нашёл настоящую
юридическую конструкцию сделки — карточка знала её только косвенно
(«де-факто уже принадлежала НМГ с 2016 года, сейчас перевели в прямое
владение»), а точного механизма и продавца не называла вовсе.

Личный WebFetch подтвердил дословно (verstka.media, 10 сентября 2026,
https://verstka.media/prodavczom-komsomolskoi-pravdy-mediaholdingu-aliny-kabaevoi-okazalsya-nominal-vladimira-putina):

1) «9 сентября мультимедийный информационный центр (МИЦ) «Известия»,
   входящий в НМГ, получил под свой контроль 75,1% компании «ЛДВ
   Пресс».» — сделка формально прошла как приобретение доли в
   промежуточном холдинге, а не прямая покупка акций самого ИД.

2) «Доля «ЛДВ Пресс» в капитале ИД могла составлять около 60,5%,
   писало издание Adindex на основе собственных расчётов.» —
   оценка ДРУГОГО издания (Adindex), пересказанная Verstka; сохраняю
   хедж «могла составлять» и атрибуцию, а не выдаю за точный факт.

3) «С 2016 года эту долю контролировал Сергей Руднов – сын основателя
   «Балтийской медиагруппы» Олега Руднова.» — первое найденное прямое
   указание продавца; ни один из источников, стоявших в карточке на
   3 сентября (Известия, Интерфакс, ТАСС, Коммерсантъ, ComNews, РБК,
   Lenta.ru, mergers.ru), продавца не называл вовсе.

НЕ внесено: сумма сделки (по-прежнему нигде не раскрыта, включая эту
статью — «сумма сделки... в сообщении НМГ не раскрывались»);
консультанты (не найдены ни в одном из проверенных источников);
политическая интерпретация заголовка статьи («номинал Путина») — это
характеристика источника, а не проверяемый корпоративный факт, в базу
не переносится.

Запуск:
    python3 pipeline/fix_nmg_kp_ldv_press_structure.py            # сухой прогон
    python3 pipeline/fix_nmg_kp_ldv_press_structure.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_LAW_STRUCT = (
    'Участники рынка напоминают, что де-факто «Комсомольская правда» '
    'принадлежит НМГ еще с 2016 года, а сейчас компанию просто перевели '
    'в прямое владение.'
)
NEW_LAW_STRUCT = OLD_LAW_STRUCT + (
    ' Формально сделка оформлена как приобретение 9 сентября 2026 года '
    '75,1% в ООО «ЛДВ Пресс» — промежуточном холдинге, которому, по '
    'оценке издания Adindex, принадлежало около 60,5% капитала самого '
    'ИД; прежним контролирующим лицом «ЛДВ Пресс» с 2016 года был '
    'Сергей Руднов, сын основателя «Балтийской медиагруппы» Олега '
    'Руднова.'
)

NEW_SELLER = 'Сергей Руднов'

NEW_SRC = ['Verstka.media',
           'https://verstka.media/prodavczom-komsomolskoi-pravdy-mediaholdingu-aliny-kabaevoi-okazalsya-nominal-vladimira-putina']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g70c0a9ff']

    assert d['law']['struct'] == OLD_LAW_STRUCT, \
        'g70c0a9ff law.struct уже другой: %r' % (d['law']['struct'],)
    assert d.get('seller') is None, \
        'g70c0a9ff seller уже занят: %r' % (d.get('seller'),)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен: %s' % NEW_SRC[1]

    print('g70c0a9ff: law.struct дополнен (75,1% «ЛДВ Пресс» — '
          'промежуточный холдинг, а не прямая покупка ИД); seller '
          'заполнен (Сергей Руднов, контролировал долю с 2016 года); '
          'party_evidence.seller и источник Verstka.media добавлены')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['law']['struct'] = NEW_LAW_STRUCT
    d['seller'] = NEW_SELLER
    d.setdefault('party_evidence', {}).setdefault('seller', []).append({
        'value': NEW_SELLER,
        'field': 'seller',
        'method': 'human_review',
        'url': NEW_SRC[1],
    })
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
