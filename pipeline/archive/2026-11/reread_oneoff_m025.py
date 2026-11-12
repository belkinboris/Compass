# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, марафон, партия m025: правки, которые review.py не умеет.

Доказательства — в докстроке pipeline/ingest/fixes/reread_2026_11_12_m025.py, тексты —
data/inbox/triage/sources_2026-11-12_m025.json.

Каждая правка проверяет старое значение (assert); повторный запуск — «уже применено».
Запуск — внутри pipeline/reread_apply.py (после review.py --write):
    python3 pipeline/archive/2026-11/reread_oneoff_m025.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m025.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка 12 ноября 2026, партия m025'
CARDS = {'g4b275e25', 'g99448cd9', 'g2668950b', 'g576de71f', 'g84a06224', 'g211615eb', 'g5160d16f', 'g2c9ecddc',
         'gff20fb8d', 'gf217e953', 'g81a22b7c', 'ge945a8e1'}
NO_ADV = [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались']]

Q_CLS = ('Учредителями «Кэпитал менеджмент» являются партнеры юридической компании CLS Дмитрий Чурин (99%) и Вадим '
         'Ковалев (1%).')
Q_GR = ('ГАП «Ресурс» Виктора Наурузова приобрела в конце декабря 2024 года по 30% в четырех юрлицах, '
        'зарегистрированных в Саратовской области и принадлежавших местным бизнесменам')
Q_VT = ('According to the Unified State Register of Legal Entities, on December 19, Megatek became the new owner of '
        'Agrocomplex Labinsky LLC, replacing Rosimushchestvo.')
Q_MO = ('Компания группы Газпромбанка приобрела 12,5% долей группы «Моторика» 27.12.2024, 18:40 Дочерняя компания '
        'группы Газпромбанка выступила покупателем доли в МК ООО «Хомо Ауктус»')
Q_T2 = ('По данным ЕГРЮЛ, структура Т2 - ООО "ТДМ Тех" - 20 декабря получила по 100% ООО "Ябби" (Yabbi) и ООО '
        '"Плацкарт Диджитал" (Plazkart), а 18 декабря - 100% ООО "Айфокс Групп".')
Q_EL = ('В ноябре 2024 года группа МТС приобрела активы и 100% долю в беларусской компании-разработчике '
        'электросамокатов Eleven.')
Q_EL2 = ('Речь идет о подконтрольном ПАО «МТС» сервисе шеринга «Юрент» (МТС «Юрент»), который в декабре завершил '
         'сделку по приобретению беларусской компании Eleven.')

Q_KL = ('АО "Точка" купила 70% компании Kleek, которая разрабатывает сервис для оплаты счетов и перечисления '
        'чаевых.')
Q_KL_REG = '2024-12-10 joined: АО "ТОЧКА" (None → 70.0)'
U_KL_REG = 'https://datanewton.ru/contragents/1215100006175/history/timeline'
U_KL = 'https://www.comnews.ru/digital-economy/content/236699/2024-12-05/2024-w49/1012/tochka-kupila-70-kompanii-kleek'
Q_WS = ('White Square выступила юридическим консультантом Balchug Capital в связи с приобретением производителя кормов '
        'для домашних животных.')
Q_FT = ('По его словам, вся компания оценена в сумму около 7 млрд руб., сейчас она находится на согласовании '
        'Федеральной антимонопольной службы (ФАС).')
U_FT = 'https://www.rbc.ru/technology_and_media/13/11/2024/673337949a794769598fb177'
U_NR = 'https://new-retail.ru/novosti/retail/moskovskiy_tts_vremena_goda_smenil_vladeltsa/'
U_KM_GR = 'https://www.kommersant.ru/doc/7432621'
U_IFX_VT = 'https://interfax.com/newsroom/top-stories/108859/'
U_KM_MO = 'https://www.kommersant.ru/doc/7419122'
U_IFX_T2 = 'https://www.interfax.ru/business/1000237'
U_REF = ('https://reform.news/mts-vykupilo-belarusskuju-kompaniju-razrabotchika-jelektrosamokatov-eleven-za-807-mln-'
         'rossijskih-rublej')

# (карточка, поле, старое, новое, цитата, адрес)
SET = [
    ('g4b275e25', 'law.adv',
     [['Юридический консультант продавца («Кэпитал менеджмент»)', 'CLS',
       'Продажа ТЦ «Времена года» структурам группы «Киевская площадь». Партнеры фирмы (одновременно продавцы) '
       'Дмитрий Чурин, Вадим Ковалев. Источник: cls.ru, realty.rbc.ru/news/693c00079a79475e5b2e7993']],
     NO_ADV, Q_CLS, U_NR),
    ('g99448cd9', 'date', '2024-12-01', '2024', Q_GR, U_KM_GR),
    ('g2668950b', 'date', '2024-12-01', '2024-12-19', Q_VT, U_IFX_VT),
    ('g2668950b', 'date_basis', None, 'registry', Q_VT, U_IFX_VT),
    ('g576de71f', 'date', '2024-12-01', '2024', Q_MO, U_KM_MO),
    ('g84a06224', 'date', '2024-12-01', '2024-12-20', Q_T2, U_IFX_T2),
    ('g84a06224', 'date_basis', None, 'registry', Q_T2, U_IFX_T2),
    ('g211615eb', 'date', '2024-12-01', '2024', Q_EL + ' … ' + Q_EL2, U_REF),
    # часть 2
    ('g5160d16f', 'buyer', 'g09ccbaca', 'g599e8557', Q_KL + ' … ' + Q_KL_REG, U_KL_REG),
    ('g5160d16f', 'date', '2024-12-01', '2024-12-10', Q_KL_REG, U_KL_REG),
    ('g5160d16f', 'date_basis', None, 'registry', Q_KL_REG, U_KL_REG),
    ('g5160d16f', 'ind', 'Банки', 'Финтех', Q_KL, U_KL),
    ('gf217e953', 'law.adv',
     [['Юридический консультант', 'White Square',
       'White Square выступила юридическим консультантом Balchug Capital в связи с приобретением производителя кормов '
       'для домашних животных Команда White Square сопровождала подписание и закрытие сделки инвестиционной компании '
       'Balchug Capital по приобретению одного из крупнейших производителей кормов для животных ООО «Радуга», '
       'выпускающего продукцию как под собственными торговыми марками (Cat&Man, Dog&Man Источник: '
       'https://t.me/LawFirms/8393)']],
     [['Юридический консультант покупателя (Balchug Capital)', 'White Square',
       'Сопровождала подписание и закрытие сделки Balchug Capital по покупке ООО «Радуга». Источник: '
       'https://t.me/LawFirms/8393']],
     Q_WS, 'https://t.me/LawFirms/8393'),
    ('ge945a8e1', 'sum', '7 млрд ₽ (по оценке)', 'Не раскрыта', Q_FT, U_FT),
    ('ge945a8e1', 'eco.sum', '7 млрд ₽ (по оценке)', 'Не раскрыта', Q_FT, U_FT),
]
RETRACT = [('ge945a8e1', 'sum', '7 млрд ₽ (по оценке)')]
NOTES = {
    'g4b275e25': {'searched': 'покупатель по протоколу торгов — ООО «Достижение», структура «Киевской площади» '
                              '(РИА Недвижимость, New Retail 14.04.2025); ИНН «Достижения» искали: WebSearch в двух '
                              'формулировках (с «Октан плюс альфа», с Нисановым и Илиевым), datanewton (не ответил), '
                              'OpenSanctions (только ООО «Киевская площадь»), Forbes (капча). Профиль покупателя — '
                              'общий профиль группы «Киевская площадь», юрлицо названо в law.struct. CLS снят: в '
                              'статьях это место работы учредителей продавца (Чурин, Ковалев), сообщений о '
                              'сопровождении сделки нет (WebSearch, РБК Недвижимость — топ-10 сделок 2025).'},
    'g99448cd9': {'no_profile': {'seller': 'по 30% в ООО «Клин-2002», «Белопольское», «Садко», «Аверо» продали, по '
                                           '«Коммерсанту» (ЕГРЮЛ), «местные бизнесмены» без имен; искали: '
                                           'Коммерсантъ, Oleoscope, mergers.ru, WebSearch по обществам, datanewton '
                                           '(не ответил) — имена продавцов не нашлись'}},
    'g84a06224': {'no_profile': {'seller': 'прежних владельцев ООО «Ябби», «Айфокс Групп», «Плацкарт Диджитал» '
                                           'источники не называют; искали: Интерфакс (ЕГРЮЛ), ADPASS, Forbes '
                                           '(капча), WebSearch (только записи OpenSanctions без дат, '
                                           'противоречат друг другу), datanewton (не ответил)'}},
    'g211615eb': {'no_profile': {'seller': 'владельцы белорусской Eleven не раскрываются (РБК: «Владельцы и '
                                           'финансовые показатели не раскрываются»); искали: РБК, Reform.news (МСФО '
                                           'МТС), WebSearch; белорусский реестр отсюда недоступен'}},
    'g576de71f': {'searched': 'Gazprombank.ru, Коммерсантъ (тот же релиз), годовой отчет «Моторики» за 2024 год '
                              '(реквизитов нет), WebSearch по ИНН МК ООО «Хомо Ауктус» — не нашелся; продавец доли '
                              'не назван ни в одном источнике (вход инвестора, способ — не раскрыт)'},
    'gff20fb8d': {'searched': 'Интерфакс (22.01.2025), РБК (25.02.2025, ЕГРЮЛ), ПРАЙМ (пересказ РБК), Global Trade '
                              'Alert (только о разрешении на выход Vinci), WebSearch в двух формулировках (по-русски и '
                              'по ИНН ОССП), реестр лицензий МЧС (ИНН 7703744408), datanewton (не ответил). Цена сделки '
                              'и консультанты нигде не названы.'},
    'ge945a8e1': {'no_profile': {'seller': 'сделка не состоялась; кто продал бы 50% — не сказано: участники ООО «ФТ» '
                                           'Алексей Юнин (60%) и Татьяна Красильникова (40%) сохранили доли (TAdviser, '
                                           'июнь 2026); искали: РБК, TAdviser, WebSearch'}},
}
DESC = [('gb3a41bdd',
         'Торговый центр в Москве; в 2024 году его на аукционе купила структура группы «Киевская площадь» Года '
         'Нисанова у «Кэпитал менеджмент».',
         'Торговый центр в Москве на Кутузовском проспекте; в апреле 2025 года его на торгах купила структура группы '
         '«Киевская площадь» Года Нисанова у «Кэпитал менеджмент».'),
        ('g6c3892cd',
         'Сервис оплаты счетов и чаевых Kleek; в 2024 году 70% его долей у физлиц купил банк «Точка».',
         'Сервис оплаты счетов и чаевых Kleek (теперь «Клик»); в декабре 2024 года 70% долей купило АО «Точка», в '
         'январе 2026 года — оставшиеся 30%.'),
        ('g18ad430e',
         'Новосибирский производитель телеком-оборудования (бренд Future Technologies); в 2024 году «Росатом» '
         'планировал купить 50% за 7 млрд ₽ (по оценке), сделка не состоялась.',
         'Новосибирский производитель телеком-оборудования (бренд Future Technologies); в 2024 году «Росатом» '
         'собирался купить 50%, но сделка не состоялась.'),
        ('g935fdad2',
         'Нидерландский холдинг, консолидирующий ОССП — крупнейшего оператора платных дорог в России; в 2024 году '
         'директор Нацпроектстроя Алексей Крапивин выкупил оставшиеся 50% у французской Vinci Concessions.',
         'Нидерландское СП Vinci Concessions и «Мостотреста» (по 50%), владевшее ОССП — крупнейшим оператором платных '
         'дорог в России; в декабре 2024 года 100% ОССП перешли от него к гендиректору «Нацпроектстроя» Алексею '
         'Крапивину, в январе 2025 года — к АО «ГК НПС».')]
COMP_IND = [('g6c3892cd', 'Банки', 'Финтех')]


def get(card, field):
    obj = card
    for p in field.split('.'):
        obj = obj.get(p) if isinstance(obj, dict) else None
    return obj


def put(card, field, value):
    parts = field.split('.')
    obj = card
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    if value is None:
        obj.pop(parts[-1], None)
    else:
        obj[parts[-1]] = value


def merge_notes(acc, notes):
    n = 0
    for key, val in notes.items():
        if isinstance(val, dict):
            sub = acc.setdefault(key, {})
            for k2, v2 in val.items():
                if sub.get(k2) != v2:
                    sub[k2] = v2
                    n += 1
        elif acc.get(key) != val:
            acc[key] = val
            n += 1
    return n


def main(argv):
    write = '--write' in argv
    import fact_edit_guard
    import mass_edit_guard
    raw = open(DATA, encoding='utf-8').read()          # перечитать прямо перед записью
    data = json.loads(raw)
    old = json.loads(raw)
    by = {d['id']: d for d in data['deals']}
    done = 0
    for cid, field, was, new, quote, url in SET:
        card = by[cid]
        cur = get(card, field)
        if cur == new:
            print('уже применено: %s.%s' % (cid, field))
            continue
        assert cur == was, '%s.%s: в базе %r, ожидали %r' % (cid, field, cur, was)
        put(card, field, new)
        fact_edit_guard.log(card, field, new, quote, url, BY)
        print('%s.%s: %r → %r' % (cid, field, str(was)[:60], str(new)[:60]))
        done += 1
    for cid, field, value in RETRACT:
        lst = by[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
            done += 1
    for comp, was, new in COMP_IND:
        cur = data['companies'][comp].get('ind')
        if cur != new:
            assert cur == was, '%s.ind: %r' % (comp, cur)
            data['companies'][comp]['ind'] = new
            done += 1
    for cid, notes in NOTES.items():
        done += merge_notes(by[cid].setdefault('accepted_notes', {}), notes)
    for comp, was, new in DESC:
        cur = data['companies'][comp].get('desc')
        if cur != new:
            assert cur == was, '%s.desc: %r' % (comp, cur)
            data['companies'][comp]['desc'] = new
            done += 1
    print('изменений: %d' % done)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    if not done:
        return 0
    mass_edit_guard.check(old, data, key='reread')
    out = json.dumps(data, ensure_ascii=False, indent=1)
    if raw.endswith('\n'):
        out += '\n'
    open(DATA, 'w', encoding='utf-8').write(out)
    print('записано')
    return 0


def rebaseline_mine(write):
    """Исправленные этой партией старые нарушения text_rules убираются из базовой линии — только
    свои карточки (test_card_text_follows_the_house_rules требует убрать исправленное)."""
    from pipeline import text_rules
    data = json.load(open(DATA, encoding='utf-8'))
    now = {f[0] for f in text_rules.all_findings(data)}
    known = json.load(open(text_rules.BASELINE, encoding='utf-8'))
    gone = [fp for fp in known['known'] if fp.split('|')[0] in CARDS and fp not in now]
    print('базовая линия text_rules: исправлено своих %d' % len(gone))
    if write and gone:
        known['known'] = [fp for fp in known['known'] if fp not in gone]
        with open(text_rules.BASELINE, 'w', encoding='utf-8') as fh:
            json.dump(known, fh, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    code = main(sys.argv[1:])
    rebaseline_mine('--write' in sys.argv[1:])
    sys.exit(code)
