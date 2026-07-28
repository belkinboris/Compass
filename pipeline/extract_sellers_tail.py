# -*- coding: utf-8 -*-
"""Бэклог A20, хвост: слово «продавец» записано не подписью, а внутри фразы.

ЧТО ОСТАВАЛОСЬ. Прогон 42 закрыл карточки, подписанные «Продавец — X».
Осталось 29, где то же слово стоит иначе: «X (продавец)», «продавец первого
пакета — X», «между Henderson (покупатель) и Айсель Трудел (продавец)»,
«продавец 75% акций». Это последняя часть выборки по слову «продавец»: после
этого прогона карточек с этим признаком и пустым полем не остаётся.

ЗАМЕР. Кандидатов 29, прочитаны все: заполнено 21, отклонено 8.

ЧТО ОТКЛОНЕНО И ПОЧЕМУ ЭТО ВАЖНО. Половина отказов — это места, где слово
«продавец» есть, а стороны нет: «Продавец публично не раскрывался», «Продавец —
физические лица», «Продавец — бенефициары не раскрыты», «продавец оценивает в
20 млрд руб.». Механическая выемка «того, что стоит рядом со словом» записала
бы всё это в имя стороны.

ОТДЕЛЬНЫЙ ОТКАЗ — g0806cf90. Там подпись противоречит сделке: «между ОАО
«Каравай» (покупатель) и ЗАО «Щелковохлеб» (продавец)», хотя «Щелковохлеб» —
это и есть купленный завод, он же стоит предметом сделки. Продавцом был кто-то
из его владельцев, и кто именно — из карточки не следует.

ЧТО ПРОВЕРЯЕТСЯ ПЕРЕД ЗАПИСЬЮ — то же, что в прогонах 40–42: имя ложится на
текст карточки слово в слово с точностью до окончаний, продавец не совпадает с
покупателем, а совпадение с предметом сделки требует явного решения — либо
ROLE_FIX (продавец стоял предметом), либо SAME_NAME_OK (продаётся российский
актив материнской компании).

Запуск:
    python3 pipeline/extract_sellers_tail.py            # сухой прогон
    python3 pipeline/extract_sellers_tail.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

TABLE = {
    'g56989e44': 'Сергей Дашков',
    'ge386fb20': 'Денис Таран',
    'g162c155f': 'Тельман Дмитрий Тельманович',
    'g68297df0': 'Марков Александр Иванович',
    'g0a2088ba': 'Лизинговая компания «Дельта»',
    'g9c255b9c': 'Фарыгин Антон Борисович',          # продавец первого пакета
    'g5da91c40': 'Владислав Тимохин',
    'g5d835058': 'Дмитрий Маргасов',
    'g829e5f99': '«Магнит»',
    'gc5eb971c': 'Геннадий Иванович Локотков',
    'gcc054516': 'Алексей Зайцев',
    'g60c0956e': 'Autoliv',
    'g2a9fcf0f': 'Анатолий Аубекеров',
    'g3d815d6f': 'Отгай Асланов',
    'g5b65aad0': 'Айсель Трудел',
    'gfda775ad': 'Европейский медицинский центр',
    'gc80f7910': 'Банк «Траст»',
    'g8de46135': 'Faurecia',
    'gde280a8d': 'PNK Group',
    'g6ef203a1': 'Банк непрофильных активов «Траст»',
    'gfc260e10': 'USM Holdings Limited',
}

# Профиль продавца стоял в `target`: предметом сделки числился сам продавец.
ROLE_FIX = {
    'g56989e44': 'g17625390',   # продана: сеть кофеен «Даблби»
    'g829e5f99': 'gd19e26bf',   # продаются: крупноформатные магазины «Магнита»
}

# Продавец и предмет называются похоже, но это разные стороны.
SAME_NAME_OK = {
    'g8de46135': 'продавец — Faurecia, предмет — «Faurecia (российские активы)»',
}

SKIP = {
    'g18413e61': '«Продавец публично не раскрывался» — прямо сказано, что имени нет',
    'ged395e90': '«Продавец — физические лица» — имени нет',
    'g623cf943': '«Продавец — бенефициары не раскрыты» — это пустота',
    'g5b8fa758': 'слово «продавец» стоит в оценке цены, а не рядом с именем',
    'g2369d101': 'продавец назван описательно — «дочка Сибура», юрлицо не названо',
    'g9d9e7ab6': 'компания привлекает инвестора в свой капитал: продавцом подписана она '
                 'сама, а кто именно продаёт долю — из текста не следует',
    'g57a44f07': 'продавцом названо само приобретаемое ООО «Эйдос Робототехника»',
    'g0806cf90': 'продавцом подписан купленный завод «Щелковохлеб», он же предмет сделки; '
                 'кто из его владельцев продавал — из карточки не следует',
}

WORD = re.compile(r"[\w%,.]+", re.U)
SPLIT = re.compile(r'\s+и\s+|,\s*')


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def bare(word):
    return word.strip('«»"\'(),.;:%').lower()


def same_word(a, b):
    a, b = bare(a), bare(b)
    if not a or not b:
        return False
    if a == b:
        return True
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i >= max(3, int(0.6 * n))


def words(s):
    return [w for w in WORD.findall(s) if bare(w)]


def fits(result, source):
    rw, sw = words(result), words(source)
    if not rw:
        return False
    return any(all(same_word(a, b) for a, b in zip(rw, sw[i:i + len(rw)]))
               for i in range(len(sw) - len(rw) + 1))


def fits_parts(result, sources):
    parts = [p for p in (x.strip() for x in SPLIT.split(result)) if words(p)]
    return all(any(fits(p, t) for t in sources if t) for p in parts)


def close_names(a, b):
    x, y = bare(a), bare(b)
    if x in y or y in x:
        return True
    wa, wb = words(a), words(b)
    n = min(len(wa), len(wb))
    return bool(n) and all(same_word(p, q) for p, q in zip(wa[:n], wb[:n]))


def texts(deal):
    eco = deal.get('eco') or {}
    law = deal.get('law') or {}
    return [t for t in [norm(deal.get('title')), norm(deal.get('extra')),
                        norm(eco.get('share')), norm(eco.get('rationale')),
                        norm(eco.get('context')), norm(law.get('struct')),
                        norm(law.get('terms'))] if t]


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    comps = data['companies']
    assert not (set(TABLE) & set(SKIP)), 'карточка одновременно в таблице и в отказах'
    assert set(ROLE_FIX) <= set(TABLE) and set(SAME_NAME_OK) <= set(TABLE), \
        'решение по роли без имени продавца'

    done = sum(1 for i, name in TABLE.items() if norm(by_id[i].get('seller')) == norm(name))
    if done == len(TABLE):
        print('Уже применено: у всех %d карточек продавец записан.' % done)
        return
    assert done == 0, 'скрипт применён частично (%d из %d)' % (done, len(TABLE))

    planned = []
    for deal_id, name in TABLE.items():
        deal = by_id.get(deal_id)
        assert deal is not None, 'нет сделки %s' % deal_id
        assert not deal.get('seller_id') and not norm(deal.get('seller')), \
            '%s: продавец уже заполнен — %r' % (deal_id, norm(deal.get('seller')))
        src = texts(deal)
        assert any(fits(name, t) for t in src) or fits_parts(name, src), \
            '%s: имя не ложится на текст карточки (%r)' % (deal_id, name)
        buyer = comps.get(deal.get('buyer'), {}).get('name') if deal.get('buyer') else None
        assert not buyer or bare(buyer) != bare(name), \
            '%s: продавец совпал с покупателем' % deal_id
        for field in ('target', 'asset_id'):
            other = comps.get(deal.get(field), {}).get('name') if deal.get(field) else None
            if other and close_names(other, name) and deal_id not in SAME_NAME_OK:
                assert ROLE_FIX.get(deal_id) == deal.get(field) and field == 'target', \
                    '%s: продавец стоит в поле %s (%r) — решение не записано' % (deal_id, field, other)
        if deal_id in ROLE_FIX:
            cid = ROLE_FIX[deal_id]
            assert comps.get(cid), '%s: нет профиля %s' % (deal_id, cid)
            assert deal.get('target') == cid, '%s: ожидали профиль продавца в target' % deal_id
            assert close_names(comps[cid]['name'], name), \
                '%s: профиль %r не похож на имя продавца' % (deal_id, comps[cid]['name'])
        planned.append((deal_id, name, deal))

    print('Карточек к заполнению: %d (из них роль исправляется: %d; отклонено при чтении: %d)'
          % (len(planned), len(ROLE_FIX), len(SKIP)))
    for deal_id, name, _ in planned:
        print('  %s%s  %s' % (deal_id, ' [роль]' if deal_id in ROLE_FIX else '      ', name))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    for deal_id, name, deal in planned:
        deal['seller'] = name
        deal['seller_src'] = 'text'
        if deal_id in ROLE_FIX:
            deal['seller_id'] = ROLE_FIX[deal_id]
            deal['target'] = None
            deal['target_was_seller'] = True
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    filled = sum(1 for d in data['deals'] if d.get('seller_id') or norm(d.get('seller')))
    print('\nЗаписано. Продавец известен у %d карточек из %d.' % (filled, len(data['deals'])))
    print('Связано с профилем компании: %d.'
          % sum(1 for d in data['deals'] if d.get('seller_id')))


# Правило проверяется на себе.
assert not fits('Иван Петров', 'между Henderson (покупатель) и Айсель Трудел (продавец)')
assert fits('Айсель Трудел', 'между Henderson (покупатель) и Айсель Трудел (продавец)')
assert fits('Владислав Тимохин', 'и Владиславом Тимохиным (продавец 75% акций)')

if __name__ == '__main__':
    main('--write' in sys.argv)
