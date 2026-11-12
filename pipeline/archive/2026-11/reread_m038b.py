# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m038 (вторая часть): правки, которые review.py не умеет.

Стороны по реестру (продавец и покупатель — юрлица, вышедшие и вошедшие в участники),
даты, которые меняют год (review.py год не переносит), сумма-оценка → «Не раскрыта»
(review.py не принимает «Не раскрыта» и «≈»), новые профили сторон, имена и описания
профилей, заметки приемки. Каждая правка факта — с `fact_edit_guard.log` (цитата и адрес).
Тексты статей — data/inbox/triage/sources_2026-11-12_m038.json; таблица правок —
pipeline/ingest/fixes/reread_2026_11_12_m038b.py.

    python3 pipeline/archive/2026-11/reread_m038b.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_m038b.py --write

База перечитывается прямо перед записью; каждая операция проверяет старое значение;
повторный запуск после записи печатает «уже применено» и ничего не меняет.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка 12.11.2026 (m038)'
API = 'https://projectcompass.ru/api/companies/%s/fns'
DN = 'https://datanewton.ru/api/v2/history?ogrn=%s&startDate=2000-01-01&attributes=OWNERS'
FACTS = ('title', 'date', 'status', 'sum', 'eco.sum', 'eco.share', 'buyer', 'seller', 'target', 'asset',
         'buyer_name', 'seller_name', 'law.adv', 'eco.finadv')

# Новые профили сторон: id → данные профиля и ключи сопоставления.
NEW = {}
# Операции над карточками: (id, поле, старое, новое, цитата, адрес). Цитата — для полей-фактов.
OPS = []
# Профили: (id профиля, поле, старое, новое).
CO = []
# Заметки приемки и снятые значения: (id, путь в accepted_notes, текст) / (id, поле, значение).
NOTES = []
RETRACT = []
# Ключи сопоставления профилей, которые дописываются.
KEYS = []


# ---------- g01b8b8f6: Ozon / «Восток Инвестиции»
U_FM = 'https://frankmedia.ru/199224'
Q_OZB = ('Согласно документам, в 2024 году «Кенигсберг Инвестментс» приобрела акции публичной компании, после чего передала их в уставный капитал '
         'своей дочерней структуры. Эта дочерняя компания была полностью реализована обществом в течение отчетного периода третьему лицу. … '
         'Покупатель, удовлетворяющий этим требованиям, был найден, однако его имя источник не раскрывает. Формально предметом сделки выступило «О23», '
         'на которое и был переоформлен пакет акций.')
Q_OZS = ('Сделка по продаже 27,64% акций одного из крупнейших российских маркетплейсов — Ozon — была завершена в 2024 году. … '
         'Формально предметом сделки выступило «О23», на которое и был переоформлен пакет акций.')
OPS += [
    ('g01b8b8f6', 'buyer', 'g8a3b7795', None, Q_OZB, U_FM),
    ('g01b8b8f6', 'eco.share', '—', '27,64% акций МКПАО «Озон» — через продажу 100% АО «О23», на которое их переоформили', Q_OZS, U_FM),
]
RETRACT += [('g01b8b8f6', 'buyer', 'О23')]
NOTES += [('g01b8b8f6', 'no_profile.buyer', 'Покупатель 100% АО «О23» в 2024 году не раскрыт: РБК (по Frank Media), Ведомости 28.07.2025, Интерфакс 1083246 — '
           '«российская структура, не попадающая под санкции». АО «О23» — дочерняя компания продавца, а не покупатель. В июле 2025 года Ozon сообщил, '
           'что 100% «О23» купили структуры Александра Чачавы, — это следующая сделка с тем же пакетом (вычитка 12.11.2026, m038)')]
CO += [
    ('gfe425e93', 'desc', 'Инвестиционный фонд; российская структура бывшего фонда Baring Vostok, получившая его активы при разделе бизнеса в 2022 году.',
     'Инвестиционный холдинг, который через калининградскую МКООО «Кенигсберг Инвестментс» консолидировал российские активы фонда Baring Vostok, включая долю в Ozon; в 2024 году вышел из капитала Ozon.'),
    ('gfe425e93', 'legal_short', None, 'МКООО «Кенигсберг Инвестментс»'),
    ('ga3bc7294', 'legal_short', None, 'МКПАО «Озон»'),
]

# ---------- g46c6e23f: «Яндекс» / Boxberry
Q_BX = ('Согласно ЕГРЮЛ, ООО "Смарт Логистик" на 100% принадлежит Владимиру Теплюкову, он также владеет 45% ООО "Боксберри Софт" '
        '(еще 30% у Вероники Тагуновой и 25% у Константина Астафьева).')
OPS += [('g46c6e23f', 'seller', None, 'Владимир Теплюков, Вероника Тагунова и Константин Астафьев', Q_BX, 'https://www.interfax.ru/business/1021099')]
NOTES += [('g46c6e23f', 'no_profile.seller', 'Продавцы — физические лица, профилей нет: по ЕГРЮЛ (Интерфакс 16.04.2025, Ъ 7659049) Владимиру Теплюкову принадлежали '
           '100% ООО «Смарт Логистик» и 45% ООО «Боксберри Софт», Веронике Тагуновой — 30%, Константину Астафьеву — 25% (вычитка 12.11.2026, m038)')]

# ---------- gc681c2b6: «АГ Майнинг»
Q_AG = ('разрешить совершение обществом с ограниченной ответственностью "Горнорудная Компания Альянс" сделки по приобретению 10 223 223 акций '
        'публичного акционерного общества "АГ Майнинг", принадлежащих Копи Голдфилдс АБ (публ) (Kopy Goldfields AB (publ). … 25 марта 2025 года № 90-рп')
OPS += [('gc681c2b6', 'date', '2024', '2025-03-25', Q_AG, 'http://static.kremlin.ru/media/events/files/ru/AXb6abJjVgiZNAnWlbnBklEzAvxQlzm3.pdf')]
CO += [
    ('gfffc5ddd', 'desc', 'Структура Мусы Бажаева; купила у Kopy Goldfields золотодобывающую компанию «Амур Золото».',
     'ООО «Горнорудная компания «Альянс»»: по ЕГРЮЛ, Арсену Идрисову принадлежат 60%, Дени и Тимуру Бажаевым — по 20%. В марте 2025 года получила разрешение Президента купить у Kopy Goldfields 99,999% акций ПАО «АГ Майнинг».'),
    ('gfffc5ddd', 'legal_short', None, 'ООО «Горнорудная компания «Альянс»»'),
    ('gfcf13ca6', 'desc', '88% принадлежит Мусе Бажаеву; в 2024 году продает 100% акций ПАО «АГ Майнинг» ГК «Альянс», сделку одобрил президент РФ.',
     'Шведская Kopy Goldfields AB: через ПАО «АГ Майнинг» владеет российскими золотодобывающими активами («Амур Золото»). 92,5% принадлежат Магомеду Бажаеву и HC Alliance Mining Group; в октябре 2024 года ушла с биржи Nasdaq First North.'),
    ('g34180872', 'desc', 'ПАО, владеет золотодобывающей компанией «Амур Золото» (в двадцатке крупнейших производителей России); в 2024 году 100% акций покупает ГК «Альянс» Мусы Бажаева у Kopy Goldfields.',
     'ПАО «АГ Майнинг» — холдинг российских золотодобывающих активов Kopy Goldfields («Амур Золото»). В марте 2025 года Президент разрешил ГК «Альянс» купить 99,999% его акций у Kopy Goldfields.'),
]

# ---------- g399c1f98: МТС / Vinteo (история участников ООО «Винтео», ИНН 2312200249)
Q_VN = ('ЕГРЮЛ, ООО «Винтео» (ИНН 2312200249), история участников: 2024-11-13 joined ООО «ВЕБИНАР» 51% (номинал 15 536,60 руб.); '
        'Самойлов Роман Борисович 34,3486% → 16,8308% (10 463,92 → 5 127,32 руб.); Ливикин Алексей Алексеевич и Серый Дмитрий Иванович — '
        'по 16,0846% (4 900 руб. каждый при прежних 10 000 руб.)')
U_VN = API % 'g2c64f815'
OPS += [
    ('g399c1f98', 'date', '2024', '2024-11-13', Q_VN, U_VN),
    ('g399c1f98', 'date_basis', None, 'registry', '', ''),
    ('g399c1f98', 'seller', None, 'Роман Самойлов, Алексей Ливикин и Дмитрий Серый', Q_VN, U_VN),
    ('g399c1f98', 'eco.context',
     'Изначально по 32,8% в компании принадлежали ее гендиректору Роману Самойлову, Алексею Ликину и Дмитрию Серому, еще 1,5% — Фонду развития интернет-инициатив (ФРИИ). В 2017 году ФРИИ вышел из проекта, продав свою долю Самойлову, и доля Самойлова выросла до 34,35%. После сделки с МТС 51% в ООО «Винтео» принадлежат ООО «Вебинар», доли Самойлова, Ликина и Серого сократились до 16,08% у каждого. Опцион на выкуп оставшихся 49% не реализован: структура долей не менялась, Роман Самойлов по-прежнему возглавляет «Винтео». Интеграция прошла: сервер Vinteo MCU объединен с экосистемой «МТС Линк», бренд Vinteo сохранен.',
     'ООО «Винтео» в 2013 году учредили Роман Самойлов, Алексей Ливикин и Дмитрий Серый, по трети каждому. В 2015 году 1,5% получил Фонд развития интернет-инициатив; в 2017 году эта доля перешла к Самойлову, и у него стало 34,35%.\n\n'
     'По ЕГРЮЛ, 51% в сделке продали все трое основателей: доля Самойлова уменьшилась до 16,83%, у Ливикина и Серого осталось по 16,08%. По последним данным реестра, остальные 49% по-прежнему у основателей.\n\n'
     'В марте 2025 года «МТС Линк» и Vinteo завершили интеграцию сервера Vinteo MCU в экосистему «МТС Линк».', '', ''),
]
NOTES += [('g399c1f98', 'no_profile.seller', 'Продавцы — физические лица, профилей нет: по истории участников ЕГРЮЛ ООО «Винтео» 13.11.2024 номинал долей '
           'Романа Самойлова, Алексея Ливикина и Дмитрия Серого уменьшился ровно на номинал 51%, полученных ООО «Вебинар» (вычитка 12.11.2026, m038)')]


def _get(obj, path):
    for p in path.split('.'):
        obj = (obj or {}).get(p) if isinstance(obj, dict) else None
    return obj


def _set(obj, path, value):
    parts = path.split('.')
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    if value is None:
        obj.pop(parts[-1], None)
    else:
        obj[parts[-1]] = value


def apply(data, log):
    import fact_edit_guard
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    mkeys = data.setdefault('match_keys', {})
    changed = 0
    for cid, prof in NEW.items():
        keys = prof.pop('_keys', None) if '_keys' in prof else None
        if cid in comps:
            assert comps[cid]['name'] == prof['name'], (cid, comps[cid]['name'])
            log.append('уже есть профиль %s %s' % (cid, prof['name']))
        else:
            comps[cid] = dict(prof)
            if keys:
                mkeys[cid] = keys
            changed += 1
            log.append('новый профиль %s %s' % (cid, prof['name']))
        if keys is not None:
            prof['_keys'] = keys
    for cid, field, old, new, quote, url in OPS:
        card = deals[cid]
        curv = _get(card, field)
        if curv == new:
            log.append('уже применено %s %s' % (cid, field))
            continue
        assert curv == old, (cid, field, curv, old)
        _set(card, field, new)
        if field in FACTS:
            assert quote and url, (cid, field)
            fact_edit_guard.log(card, field, new, quote, url, BY)
        changed += 1
        log.append('%s %s: %r -> %r' % (cid, field, str(old)[:50], str(new)[:50]))
    for cid, field, old, new in CO:
        c = comps[cid]
        if c.get(field) == new:
            log.append('уже применено профиль %s %s' % (cid, field))
            continue
        assert c.get(field) == old, (cid, field, c.get(field))
        if new is None:
            c.pop(field, None)
        else:
            c[field] = new
        changed += 1
        log.append('профиль %s %s -> %r' % (cid, field, str(new)[:60]))
    for cid, key in KEYS:
        lst = mkeys.setdefault(cid, [])
        if key not in lst:
            lst.append(key)
            changed += 1
            log.append('ключ %s %r' % (cid, key))
    for cid, path, text in NOTES:
        notes = deals[cid].setdefault('accepted_notes', {})
        curv = _get(notes, path)
        if curv == text:
            continue
        assert curv is None, (cid, path, curv)
        _set(notes, path, text)
        changed += 1
        log.append('заметка %s %s' % (cid, path))
    for cid, field, value in RETRACT:
        lst = deals[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
            changed += 1
            log.append('снято %s %s %r' % (cid, field, value))
    return changed


def main():
    write = '--write' in sys.argv
    data = json.load(open(DATA, encoding='utf-8'))
    log = []
    n = apply(data, log)
    print('\n'.join(log))
    print('изменений: %d' % n)
    if not write or not n:
        print('Сухой прогон.' if not write else 'Нечего записывать.')
        return
    import mass_edit_guard
    fresh = json.load(open(DATA, encoding='utf-8'))
    old = json.loads(json.dumps(fresh))
    apply(fresh, [])
    mass_edit_guard.check(old, fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(fresh, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main()
