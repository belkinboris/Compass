# -*- coding: utf-8 -*-
"""Бэклог A20, последний признак: «купил у основателя X», «у компании X».

ЧТО ПРОПУСКАЛОСЬ. Прогоны 32 и 34 искали продавца формулой «купил Y У X», но
шаблон требовал заглавную букву сразу после «у»: `у\\s+([А-ЯЁA-Z…])`. В живом
тексте между предлогом и именем почти всегда стоит строчное пояснение — «у
основателя Анатолия Покатилова», «у экс-депутата Госдумы Бекхана Агаева», «у
компании «Курс»», «у структур основателя Александра Нинбурга». Из-за одного
класса символов эти карточки не попадали ни в один замер.

ЗАМЕР. Признак «основатель / владелец / совладелец / бенефициар + имя» есть у
54 карточек без продавца. Прочитаны все: заполнено 14, отклонено 40 — и это
ожидаемо низкий выход. Слово «основатель» в 40 случаях описывает не сторону
сделки: «команда сохранит основателя в должности гендиректора», «в раунде
участвовал сооснователь Qiwi», «фонд, совладельцы которого — основатель
«ВкусВилл» и глава «ХимРар»». Признак закрыт, но брать его механически нельзя.

ПРАВКА ДВУХ НАЗВАНИЙ. У карточек этой партии в поле «предмет» стоят профили
с испорченными именами: «Выкуп Reg» (обрывок заголовка) и «Лабораторией
Касперского» (падежная форма). Оба видны на экране как предмет сделки. Новое
имя обязано выводиться из старого ИЛИ из заголовка сделки — заголовок здесь
такой же первоисточник, и проверка та же.

Запуск:
    python3 pipeline/extract_sellers_owner.py            # сухой прогон
    python3 pipeline/extract_sellers_owner.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

TABLE = {
    'g596c8144': 'Анатолий Владимирович Покатилов',
    # в тексте — «у структур основателя Александра Нинбурга»: продавали его
    # структуры, само имя переносится в именительном падеже
    'g85883f11': 'Александр Нинбург',
    'g61cccee7': 'Юрий Кузнецов',
    'g3b91745f': 'Олег Кайбелов',
    'g96674c34': 'Компания «Курс»',
    'gfd78ef6d': 'Михаил Иванов',
    'g5de426be': 'Бекхан Агаев',
    'gfe268487': 'Александр Елисеев',
    'g9b76cf8d': 'Наследники сооснователя Филиппа Гросс-Днепрова',
    'gf174262b': 'Алексей Де-Мондерик',
    'gde4f9941': 'ООО «Финансовые решения»',
    'gc92ba4cb': 'Havi',
    'geb645292': 'Volkswagen Financial Services',
    'g7ad4e39d': 'Henkel',
}

# Продавец и предмет называются похоже, но это разные стороны.
SAME_NAME_OK = {
    'g7ad4e39d': 'продавец — Henkel, предмет — «российский бизнес Henkel»',
}

# Профили в поле «предмет» с испорченными именами. Второе значение — источник,
# из которого выводится новое имя: 'name' (старое имя) или 'title' (заголовок).
NAME_FIX = {
    'g4f9e4c87': ('Выкуп Reg', 'Reg.ru', 'g9b76cf8d'),
    'g623b934f': ('Лабораторией Касперского', 'Лаборатория Касперского', 'gf174262b'),
}

SKIP_WHY = (
    '40 карточек отклонены: слово «основатель / владелец» в них описывает не сторону '
    'сделки, а её обстоятельства — гендиректора, который остаётся после сделки, '
    'инвестора раунда, бенефициара покупателя или структуру капитала после закрытия.'
)

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
    assert set(SAME_NAME_OK) <= set(TABLE), 'разрешение на совпадение без имени продавца'

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
            assert not (other and close_names(other, name)) or deal_id in SAME_NAME_OK, \
                '%s: продавец совпал с полем %s (%r) — решение не записано' % (deal_id, field, other)
        planned.append((deal_id, name, deal))

    for cid, (was, now, deal_id) in NAME_FIX.items():
        assert norm(comps[cid]['name']) == was, 'профиль %s уже не %r' % (cid, was)
        assert fits(now, was) or fits(now, norm(by_id[deal_id]['title'])), \
            'новое имя профиля не выводится ни из старого, ни из заголовка сделки'

    print('Карточек к заполнению: %d; %s' % (len(planned), SKIP_WHY))
    for deal_id, name, _ in planned:
        print('  %s  %s' % (deal_id, name))
    for was, now, _ in NAME_FIX.values():
        print('  правка названия профиля: %s -> %s' % (was, now))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    for deal_id, name, deal in planned:
        deal['seller'] = name
        deal['seller_src'] = 'text'
    for cid, (_, now, _d) in NAME_FIX.items():
        comps[cid]['name'] = now
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    filled = sum(1 for d in data['deals'] if d.get('seller_id') or norm(d.get('seller')))
    print('\nЗаписано. Продавец известен у %d карточек из %d.' % (filled, len(data['deals'])))


# Правило проверяется на себе: строчное пояснение между «у» и именем не мешает,
# а чужое имя не проходит.
assert fits('Бекхан Агаев', 'приобрел компанию у экс-депутата Госдумы Бекхана Агаева')
assert not fits('Иван Петров', 'приобрел компанию у экс-депутата Госдумы Бекхана Агаева')
assert fits('Лаборатория Касперского', 'Выкуп «Лабораторией Касперского» доли сооснователя')

if __name__ == '__main__':
    main('--write' in sys.argv)
