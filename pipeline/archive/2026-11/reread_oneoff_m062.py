# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m062 (часть 1): правки, которые не ложатся в таблицу FIXES.

Что чинит: сумму-оценку (review.py не принимает «Не раскрыта» и «(по оценке)» в eco.sum), продавца и
предмет по реестру и статье, дату по реестру, основание даты, описания профилей. Каждая правка факта —
с цитатой источника (fact_edit_guard.log). Доказательства — в комментариях операций.

    python3 pipeline/archive/2026-11/reread_oneoff_m062.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m062.py --write   # запись

База перечитывается прямо перед записью; у каждой правки assert на старое значение; повторный
запуск — «уже применено».
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'reread m062'
_MISSING = object()

_KF_EST = ('Сумма сделки может составлять до 1,3 млрд руб., считает Михаил Бурмистров, генеральный директор '
           '«Infoline-Аналитики».')
_KF_EST_URL = 'https://www.retail.ru/news/kfc-prodaet-biznes-v-rf-izhevskoy-fud-servis/'
_KF_CLOSE = ('17 апреля стало известно, что американская компания Yum! Brands, которая являлась владельцем сети '
             'ресторанов KFC в России, завершила сделку по продаже своего бизнеса в стране')
_KF_CLOSE_URL = 'https://lenta.ru/news/2023/04/18/rostics_kfc/'
_QW_EST = ('Forbes на основе котировок бумаг Qiwi на закрытии торгов Мосбиржи 30 декабря отмечает, что пакет «Открытия» '
           'мог оцениваться в 8,85 млрд руб.')
_QW_SALE = ('Банк «Открытие» вышел из капитала платежного сервиса Qiwi, продав 30 декабря 2022 года 21 млн акций класса '
            '«B». Это следует из документа , опубликованного на сайте Комиссии по ценным бумагам и биржам (SEC) США.')
_QW_URL = 'https://www.kommersant.ru/doc/5826320'
_KK_PREV = ('В сентябре компанию переименовали в ООО «Кисс Коала», она перешла под управление топ-менеджеров российского '
            'подразделения группы Арины Дмитриевой (70%) и Дмитрия Козика (30%; см. “Ъ” от 8 сентября 2022 года ). '
            '… С 29 декабря им владеет зарегистрированное 9 декабря ООО «Мерит»')
_KK_URL = 'https://www.kommersant.ru/doc/5772915'
_KK_REG = ('ЕГРЮЛ, ООО «Коала Мьюзик» (до переименования ООО «Кисс Коала»), ИНН 7710357054: 29.12.2022 вышли '
           'Дмитриева Арина Евгеньевна (70%) и Козик Дмитрий Николаевич (30%), вошло ООО «Мерит» (100%)')
_KK_REG_URL = 'https://projectcompass.ru/api/companies/g63a953b7/fns'
_ED_REG = ('ЕГРЮЛ, ООО «Эдштейн» (ныне ООО «Скилаз-ЛМС»), ИНН 5050133936: 25.01.2023 в участники вошло '
           'АО «ИК «Хэдхантер» с долей 25%')
_ED_REG_URL = 'https://projectcompass.ru/api/companies/ga24cd4e1/fns'

OPS = [
    # g0a0d451a: 1,3 млрд ₽ — оценка гендиректора Infoline-Аналитики «до 1,3 млрд», стороны цену не раскрывали.
    ('deal', 'g0a0d451a', 'sum', '1,3 млрд ₽', 'Не раскрыта (по оценке аналитика — до 1,3 млрд ₽)', _KF_EST, _KF_EST_URL),
    ('deal', 'g0a0d451a', 'eco.sum', '1,3 млрд ₽', 'Не раскрыта (по оценке аналитика — до 1,3 млрд ₽)', _KF_EST, _KF_EST_URL),
    ('deal', 'g0a0d451a', 'sum_basis', 'reported', 'estimate', _KF_EST, _KF_EST_URL),
    ('deal', 'g0a0d451a', 'date_basis', _MISSING, 'closing', _KF_CLOSE, _KF_CLOSE_URL),
    ('company', 'g80b6ec0d', 'desc',
     '70 корпоративных ресторанов и франшиза KFC в России; в 2023 году их купила компания «Смарт Сервис» Константина Котова у Yum! Brands, став единственным франчайзи бренда в стране.',
     'Российский бизнес KFC: 70 собственных ресторанов и мастер-франшиза бренда. Юрлицо — ООО «Ям Ресторантс Раша», ныне ООО «Юнирест»; с 2023 года сеть работает под брендом Rostic\'s.'),
    # g5d9d8e6c: сумма — оценка Forbes по котировкам; продана доля в Qiwi plc (акции класса «B»), а не в АО «Киви».
    ('deal', 'g5d9d8e6c', 'sum', '8,85 млрд ₽', '8,85 млрд ₽ (по оценке)', _QW_EST, _QW_URL),
    ('deal', 'g5d9d8e6c', 'eco.sum', '8,85 млрд ₽', '8,85 млрд ₽ (по оценке)', _QW_EST, _QW_URL),
    ('deal', 'g5d9d8e6c', 'target', 'gd5d02d09', 'gdf829638', _QW_SALE, _QW_URL),
    ('deal', 'g5d9d8e6c', 'date_basis', _MISSING, 'closing', _QW_SALE, _QW_URL),
    # Состав группы Qiwi в extra не подтверждает ни один источник карточки.
    ('deal', 'g5d9d8e6c', 'extra',
     'В группу Qiwi входят платежная система Qiwi, Киви-банк, система денежных переводов Contact, «Факторинг-плюс», Flocktory и QPlatform.',
     '—', None, None),
    ('deal', 'g5d9d8e6c', 'accepted_notes.no_profile.buyer', _MISSING,
     'Покупатель не раскрыт: Ъ (5826320) — «Покупатель пакета акций неизвестен»; искали в Forbes (ссылка Ъ), Reuters '
     '(The Moscow Times, 14 февраля 2023 года), Kursiv, поиском «кто купил пакет Qiwi у Открытия» по-русски и по-английски '
     '(раскрытие SEC называет только продавца).', None, None),
    # gbb8eba27: описание профиля предмета говорило о действии покупателя (находка post).
    ('company', 'gb6bfe549', 'desc',
     'Рыбодобывающая компания на Камчатке (9 участков, 16 судов, 2 перерабатывающих завода мощностью 440 тонн в сутки); в 2022 году ее 100% купила АФК «Система», включив в холдинг «Восход».',
     'Рыбодобывающая компания на западном побережье Камчатки: 9 рыболовных участков, 16 судов, 2 перерабатывающих завода мощностью 440 тонн в сутки.'),
    # g3c56d235: Sony вышла из ООО 24.08.2022; 29.12.2022 доли продали менеджеры Дмитриева и Козик (ЕГРЮЛ, Ъ).
    ('deal', 'g3c56d235', 'seller', 'Sony Music Group', 'Арина Дмитриева и Дмитрий Козик', _KK_PREV, _KK_URL),
    ('deal', 'g3c56d235', 'seller_id', 'g91a8db4b', _MISSING, _KK_PREV, _KK_URL),
    ('deal', 'g3c56d235', 'seller_src', 'text', 'registry', None, None),
    ('deal', 'g3c56d235', 'retracted.seller', _MISSING, ['Sony Music Group'], None, None),
    ('deal', 'g3c56d235', 'eco.share', '—', '100% доли в ООО «Кисс Коала»', _KK_REG, _KK_REG_URL),
    # g5fb345dc: 26 декабря 2022 года — день заметки CNews; АО «ИК «Хэдхантер» вошло в ООО 25 января 2023 года.
    ('deal', 'g5fb345dc', 'date', '2022-12-26', '2023-01-25', _ED_REG, _ED_REG_URL),
    ('deal', 'g5fb345dc', 'date_basis', _MISSING, 'registry', _ED_REG, _ED_REG_URL),
    ('company', 'ga24cd4e1', 'desc',
     'HRTech-стартап Edstein, развивает HCM-платформу совместно со Skillaz; в 2022 году 25% с опционом на выкуп контроля купил hh Ventures.',
     'Разработчик системы обучения и оценки персонала Edstein, основан в 2017 году Евгением Обогоровым. С марта 2025 года — ООО «Скилаз-ЛМС» в группе HeadHunter.'),
]


def get(obj, path):
    for k in path.split('.'):
        if not isinstance(obj, dict) or k not in obj:
            return _MISSING
        obj = obj[k]
    return obj


def put(obj, path, value):
    ks = path.split('.')
    for k in ks[:-1]:
        obj = obj.setdefault(k, {})
    if value is _MISSING:
        obj.pop(ks[-1], None)
    else:
        obj[ks[-1]] = value


def apply(data):
    import fact_edit_guard
    by = {d['id']: d for d in data['deals']}
    done = 0
    for op in OPS:
        if op[0] == 'deal':
            _k, cid, path, old, new, quote, url = op
            card = by[cid]
            cur = get(card, path)
            if cur == new:
                print('уже применено: %s %s' % (cid, path))
                continue
            assert cur == old, '%s %s: в базе %r, ожидали %r' % (cid, path, cur, old)
            put(card, path, new)
            if quote:
                fact_edit_guard.log(card, path, None if new is _MISSING else new, quote, url, BY)
            print('%s %s: %r → %r' % (cid, path, str(old)[:60], str(new)[:60]))
        else:
            _k, pid, key, old, new = op
            comp = data['companies'][pid]
            cur = comp.get(key, _MISSING)
            if cur == new:
                print('уже применено: профиль %s %s' % (pid, key))
                continue
            if key == 'legal_short' and old is _MISSING and cur not in (_MISSING, None, ''):
                # Правовую форму успел поставить party_legal_names.py другой партии — не спорим.
                print('правовая форма уже стоит: профиль %s %r' % (pid, cur))
                continue
            assert cur == old, 'профиль %s %s: %r, ожидали %r' % (pid, key, cur, old)
            if new is _MISSING:
                comp.pop(key, None)
            else:
                comp[key] = new
            print('профиль %s %s: %r → %r' % (pid, key, str(old)[:60], str(new)[:60]))
        done += 1
    return done


def drop_fixed_baseline(data):
    """Старые нарушения правил текста, исправленные этой партией, уходят из
    text_rules_baseline.json (иначе test_card_text_follows_the_house_rules: «исправлено
    старых нарушений — уберите их»). Трогаются только записи карточек этой партии."""
    import text_rules
    ids = {op[1] for op in OPS if op[0] == 'deal'}
    found = {fp for fp, did, *_ in text_rules.all_findings({'deals': [d for d in data['deals'] if d['id'] in ids]})}
    store = json.load(open(text_rules.BASELINE, encoding='utf-8'))
    keep = [fp for fp in store['known'] if fp.split('|')[0] not in ids or fp in found]
    if len(keep) != len(store['known']):
        print('из базовой линии правил текста убрано исправленных: %d' % (len(store['known']) - len(keep)))
        store['known'] = keep
        json.dump(store, open(text_rules.BASELINE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def main(argv):
    write = '--write' in argv
    data = json.load(open(DATA, encoding='utf-8'))
    before = copy.deepcopy(data)
    n = apply(data)
    if not write:
        print('Сухой прогон: %d правок. Запись — --write.' % n)
        return 0
    if not n:
        return 0
    data = json.load(open(DATA, encoding='utf-8'))          # перечитать прямо перед записью
    before = copy.deepcopy(data)
    apply(data)
    import mass_edit_guard
    mass_edit_guard.check(before, data, os.environ.get('MASS_OK'))
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    drop_fixed_baseline(data)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
