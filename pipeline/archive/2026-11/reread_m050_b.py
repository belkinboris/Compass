# -*- coding: utf-8 -*-
"""Вычитка базы, марафон 12 ноября 2026, партия m050, вторая часть (карточки 5–12): правки, которые не ложатся в таблицу FIXES.

ЧТО ЧИНИТ. Поля-факты, подтвержденные статьей или реестром (заголовок по стандарту
`pipeline/title_standard.py`, дата события вместо выдуманного 1-го числа, продавец по истории
участников ЕГРЮЛ, предмет и доля), снятие неподтвержденных значений и тексты профилей сторон.
Каждая правка факта несет цитату источника (`fact_edit_guard.log`), перед записью стоит
`assert` на старое значение; повторный запуск пропускает уже примененное.

ПОЧЕМУ НЕ review.py. Дата годом или из реестра, снятие значений, заголовок своей фразой и
профили компаний таблица FIXES не переносит.

Поиск источников — в note ответа каждой карточки (answers_m050.json партии).

    python3 pipeline/archive/2026-11/reread_m050_b.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_m050_b.py --write    # запись (делает reread_apply.py)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DAY, BY = '2026-11-12', 'reread_m050_b'
FACT = set(fact_edit_guard.FACT_FIELDS)

# Правки карточек: id, поле (через точку: eco.val), старое, новое, цитата, адрес.
EDITS = []
# Правки профилей: id профиля, ключ, старое, новое.
COMPANY = []
# Снятые значения — в retracted, чтобы обогащение их не вернуло: id, поле, значение.
RETRACT = []
# Ключи сопоставления профилей (match_keys): id профиля, ключ.
MATCH = []

# --- данные партии ---

VED_POT = 'https://www.vedomosti.ru/realty/articles/2023/07/20/986093-rosimuschestvo-prodalo-odno-iz-stareishih-poligraficheskih-predpriyatii-rossii'
K_POT = 'https://www.kommersant.ru/doc/6111899'
Q_POT = ('Московский бизнесмен Денис Избрехт купил 100% акций АО «Первая образцовая типография» у государства. … '
         'Торги прошли 19 июля. Пресс-служба Росимущества подтвердила РБК продажу.')
EDITS += [
 # g756f35a3 «Первая образцовая типография»: 20 июля — день публикации, торги прошли 19 июля (Ъ, «Ведомости», rupor73).
 # Заголовок не меняется: карточка в золотой выборке, смена заголовка сбивает отпечаток подтвержденной
 # доли (facts.card_hash, known_issues/card.md) — до повторного подтверждения фактов.
 dict(id='g756f35a3', field='date', old='2023-07-20', new='2023-07-19', quote=Q_POT, url=K_POT),
]
COMPANY += [
 ('g4fa8787f', 'legal_short', None, 'АО «Первая образцовая типография»'),
 ('g4fa8787f', 'ind', 'Недвижимость', 'Медиа'),
]

IF_HEM = 'https://www.interfax.ru/business/918738'
HEM = 'https://hempel.com/news/2023/hempel-completes-the-sale-of-its-russian-assets'
Q_HEM = ('ГК "Литум", выкупившая у датской Hempel завод в Ульяновске … "В июле 2023 года Hempel продал завод по производству '
         'красок, расположенный в индустриальном парке "Заволжье". Предприятие вошло в состав российской производственной компании "Литум"')
Q_HEM_DAY = ('Hempel, 12.07.2023: Hempel has completed the sale of its wholly owned subsidiary in Russia, selling to Russian '
             'industrial company, Atomstroykomplex. Necessary approvals from the relevant Danish and Russian authorities have been obtained.')
EDITS += [
 # g5301e77e Hempel / «Литум»: 13 июля не найдено ни в одном источнике; закрытие Hempel объявила 12.07.2023.
 # Сумма 10 млн € — из годового отчета Hempel за 2023 год (адрес в src больше не открывается, копия в веб-архиве
 # не скачалась): не опровергнута, оставлена; приведена к одной записи в sum и eco.sum.
 dict(id='g5301e77e', field='title', old='Hempel продала российский завод по производству лакокрасочных покрытий',
      new='«Литум» купил у Hempel завод красок в Ульяновске', quote=Q_HEM, url=IF_HEM),
 dict(id='g5301e77e', field='date', old='2023-07-13', new='2023-07-12', quote=Q_HEM_DAY, url=HEM),
 dict(id='g5301e77e', field='date_basis', old=None, new='closing', quote='', url=''),
 dict(id='g5301e77e', field='sum', old='10 млн €', new='€10 млн',
      quote='Правка только формы записи, как в eco.sum: 10 млн евро — 6 млн евро деньгами и 4 млн евро списанием дебиторской задолженности (годовой отчет Hempel за 2023 год).',
      url='https://www.hempel.com/hu-hu/-/media/Files/Global/PDF/Annual-Report/Hempel-Annual-Report-2023.pdf'),
]
COMPANY += [
 ('g001e45f4', 'name', 'завод по производству лакокрасочных покрытий', 'Литум. Ульяновск'),
 ('g001e45f4', 'legal_short', None, 'АО «Литум. Ульяновск»'),
 ('g001e45f4', 'desc', 'Завод лакокрасочных покрытий мощностью 16 млн литров в год; в 2023 году его продала датская Hempel за 10 млн € (6 млн денежными + списание долга на 4 млн €).',
  'Лакокрасочный завод в Ульяновске (бывшее АО «Хемпель»), проектная мощность — около 16 млн литров краски в год. В июле 2023 года датская Hempel продала его группе «Литум».'),
]
MATCH += [('g001e45f4', 'литум ульяновск')]

K_KEL = 'https://www.kommersant.ru/doc/6098761'
Q_KEL = ('Входящее в ГК «Черноголовка» АО «Аквалайф ресурс» стало единственным владельцем воронежского производителя продуктов '
         'ООО «Келлогг Рус» (основное российское юрлицо американской компании Kellogg). Компания купила 100% уставного капитала '
         '13 июля, следует из данных ЕГРЮЛ.')
EDITS += [
 # g1f098415 Kellogg / «Черноголовка»: заголовок по стандарту; день — запись ЕГРЮЛ 13 июля 2023 года.
 dict(id='g1f098415', field='title', old='Kellogg продал российский бизнес ГК «Черноголовка»',
      new='«Черноголовка» купила российский бизнес Kellogg', quote=Q_KEL, url=K_KEL),
 dict(id='g1f098415', field='date_basis', old=None, new='registry', quote='', url=''),
]

CN_BOR = 'https://www.comnews.ru/content/227406/2023-07-13/2023-w28/softline-priobrela-kontrolnyy-paket-gk-borlas'
Q_BOR = 'ГК Softline закрыла сделку по приобретению 50,1% доли в ГК "Борлас".'
EDITS += [
 # g037385e2 Softline / «Борлас»: заголовок по стандарту (стоял пересказ пресс-релиза с «ГК» и скобкой).
 dict(id='g037385e2', field='title', old='ГК Softline приобрела контрольный пакет (50,1%) ГК Борлас',
      new='Softline купил 50,1% группы «Борлас»', quote=Q_BOR, url=CN_BOR),
]
COMPANY += [
 ('gb35af751', 'legal_short', None, 'ООО «Борлас АФС»'),
]

K_SAF = 'https://www.kommersant.ru/doc/6147961'
Q_SAF = ('Структура агрохолдинга «Таврос» в июле стала владельцем ООО «Советская агрофирма» — производителя пищевого яйца '
         'в Кировской области, следует из ЕГРЮЛ.')
EDITS += [
 # gcef66398 «Таврос» / «Советская агрофирма»: заголовок по стандарту; день — запись ЕГРЮЛ 10.07.2023.
 dict(id='gcef66398', field='title', old='Агрохолдинг «Таврос» приобрел птицефабрику «Советская агрофирма» в Кировской области',
      new='«Таврос» купил птицефабрику «Советская агрофирма»', quote=Q_SAF, url=K_SAF),
 dict(id='gcef66398', field='date_basis', old=None, new='registry', quote='', url=''),
]

AKM_HAR = 'https://www.akm.ru/news/bank_otkrytie_prodayet_neftedobyvayushchuyu_kompaniyu_kharyaga/'
Q_HAR = ('AK&M 25 мая 2023 11:06. Банк «Открытие» выставил на торги нефтедобывающую компанию ООО «Харьяга». Об этом говорится '
         'в сообщении банка. … Торги состоятся 5 июля 2023 года')
EDITS += [
 # g66bb0d00 «Харьяга»: продажа без покупателя — дата первого объявления торгов (25 мая 2023), а не день назначенного аукциона.
 dict(id='g66bb0d00', field='title', old='Банк «Открытие» выставил на продажу нефтедобывающую компанию «Харьяга»',
      new='«Харьяга» выставлена на продажу', quote=Q_HAR, url=AKM_HAR),
 dict(id='g66bb0d00', field='date', old='2023-07-05', new='2023-05-25', quote=Q_HAR, url=AKM_HAR),
 dict(id='g66bb0d00', field='date_basis', old=None, new='announcement', quote='', url=''),
 dict(id='g66bb0d00', field='eco.share', old='Продается ООО «Харьяга» с извлекаемыми запасами нефти 14,8 млн т. Компании принадлежат две лицензии — на Шушукский участок в Эвенкийском муниципальном районе Красноярского края; по ним можно разведывать и добывать нефть и газ. Нефть здесь нашли в 2008 году, испытывая скважину Шушукская-1: она дала приток из пласта Б-IX оскобинской свиты на восточном склоне поднятия.',
      new='100% долей в ООО «Харьяга» вместе с ее обязательствами перед банком. Компании принадлежат две лицензии на разведку и добычу нефти и газа на Шушукском участке в Эвенкийском районе Красноярского края.',
      quote='На площадке «РОСЭЛТОРГ» (организатор торгов) стартовал прием заявок на покупку 100%-ной доли и обязательства перед банком. … ООО «Харьяга» принадлежат две лицензии на разведку и добычу нефти и газа в Красноярском крае на территории Эвенкийского муниципального района в пределах Шушукского участка.', url=AKM_HAR),
]
COMPANY += [
 ('g5d0389f6', 'desc', 'Нефтедобывающая компания; в 2023 году ее 100% с обязательствами перед банком продал на торгах РОСЭЛТОРГ банк «Открытие».',
  'Владелец двух лицензий на разведку и добычу нефти и газа на Шушукском участке (Эвенкийский район Красноярского края). Принадлежит банку «ФК Открытие», в 2023–2024 годах выставлялась им на торги; в 2026 году признана банкротом.'),
]

K_HOZ = 'https://www.kommersant.ru/doc/6564254'
REG_HOZ = 'https://datanewton.ru/api/v2/history?ogrn=1022401152905&startDate=2000-01-01&attributes=OWNERS'
Q_HOZ = ('Входящее в ГК «Содружество» ООО «Содружество-Сибирь» в январе стало владельцем переработчика зерна и масличных '
         'ООО «Хозяин» в Ачинске Красноярского края, следует из ЕГРЮЛ.')
Q_REG_HOZ = ('Запись ЕГРЮЛ от 2024-01-12 (12 января 2024 года): было — ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ТРАНССЕРВИС" '
             '(ОГРН: 1153926027584) 99.9%; (99 900 руб.); стало — выбыл. … стало — ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ '
             '"СОДРУЖЕСТВО-СИБИРЬ" (ОГРН: 1175543011038) 99.9%')
EDITS += [
 # g55a86137 «Содружество» / «Хозяин»: день в ЕГРЮЛ есть (12.01.2024), продавец по реестру — ООО «Транссервис» (99,9%).
 dict(id='g55a86137', field='title', old='ГК «Содружество» приобрела ООО «Хозяин» в Красноярском крае',
      new='«Содружество» купило ООО «Хозяин»', quote=Q_HOZ, url=K_HOZ),
 dict(id='g55a86137', field='date', old='2024', new='2024-01-12', quote=Q_REG_HOZ, url=REG_HOZ),
 dict(id='g55a86137', field='date_basis', old=None, new='registry', quote='', url=''),
 dict(id='g55a86137', field='seller', old=None, new='ООО «Транссервис»', quote=Q_REG_HOZ, url=REG_HOZ),
 dict(id='g55a86137', field='eco.share', old='—', new='99,9% долей в ООО «Хозяин»', quote=Q_REG_HOZ, url=REG_HOZ),
]
COMPANY += [
 ('g7b63fad7', 'legal_short', None, 'ООО «Группа Содружество»'),
]

VED_DEC = 'https://www.vedomosti.ru/business/articles/2023/07/21/986408-decathlon-kupil-franchaizi'
SOS_DEC = 'https://www.sostav.ru/publication/decathlon-63423.html'
RBK_DEC = 'https://kuban.rbc.ru/krasnodar/freenews/657613f99a79471828e154e3'
Q_DEC = ('35 магазинов и склад французской компании Decathlon в России купила российская компания АРМ. По данным «Контур.Фокуса», '
         'ее генеральный директор и владелец доли в 1% – Вячеслав Мареев.')
Q_DEC_SHARE = ('В сообщении указано, что «после нескольких месяцев поиска» найден российский партнёр — ООО «АРМ» (владеет франшизой '
               'Mango в России). Ему передадут 35 магазинов и фирменный склад «Бетонка».')
Q_DEC_VAL = ('Сумму сделки, в зависимости от того, какие именно активы в нее вошли, директор ритейл-департамента Core.XP Марина '
             'Малахатько оценивает в 3–5 млрд руб.')
EDITS += [
 # g60280ac0 Decathlon / АРМ: 3–5 млрд ₽ — оценка Марины Малахатько (Core.XP), не цена; 3 октября 2023 не найдено ни в
 # одном источнике (Ведомости 21.07.2023 — «купила», РБК-Кубань — «в сентябре»): дата — годом.
 dict(id='g60280ac0', field='title', old='Покупка 35 магазинов и склада Decathlon в России компанией ООО «АРМ»',
      new='АРМ купил российский бизнес Decathlon', quote=Q_DEC, url=VED_DEC),
 dict(id='g60280ac0', field='date', old='2023-10-03', new='2023',
      quote='Сеть спортивных магазинов Desport запускает российская компания АРМ. В сентябре компания приобрела 35 магазинов и склад ретейлера Decathlon Russia.', url=RBK_DEC),
 dict(id='g60280ac0', field='sum', old='3–5 млрд ₽ (по оценке)', new='Не раскрыта', quote=Q_DEC_VAL, url=VED_DEC),
 dict(id='g60280ac0', field='eco.sum', old='3–5 млрд ₽ (по оценке)', new='Не раскрыта', quote=Q_DEC_VAL, url=VED_DEC),
 dict(id='g60280ac0', field='eco.share', old='По данным IBC Real Estate, в собственности Decathlon 26 объектов общей площадью более 150 000 кв. м — 25 гипермаркетов и склад. По данным СПАРК-Интерфакса, еще 16 магазинов «Октоблу» арендует.',
      new='35 магазинов и склад «Бетонка» Decathlon в России.', quote=Q_DEC_SHARE, url=SOS_DEC),
]
RETRACT += [('g60280ac0', 'sum', '3–5 млрд ₽ (по оценке)')]
COMPANY += [
 ('g1bec4f97', 'name', 'Decathlon Russia', 'Октоблу'),
 ('g1bec4f97', 'legal_short', None, 'АО «Октоблу»'),
 ('g1bec4f97', 'desc', 'Российский бизнес французской сети спортивных товаров Decathlon.',
  'Российская «дочка» Decathlon (основное юрлицо сети, зарегистрировано в 2005 году). С 2023 года принадлежит компании АРМ и работает под брендом Desport; в 2026 году в отношении нее начато банкротство.'),
]
MATCH += [('g1bec4f97', 'октоблу')]

# --- конец данных ---


def get(card, field):
    if '.' in field:
        head, tail = field.split('.', 1)
        return (card.get(head) or {}).get(tail)
    return card.get(field)


def put(card, field, value):
    if '.' in field:
        head, tail = field.split('.', 1)
        card.setdefault(head, {})[tail] = value
    elif value is None:
        card.pop(field, None)
    else:
        card[field] = value


def apply(data, verbose=False):
    by = {d['id']: d for d in data['deals']}
    done = skipped = 0
    for e in EDITS:
        card = by[e['id']]
        cur = get(card, e['field'])
        if cur == e['new']:
            skipped += 1
            continue
        assert cur == e['old'], '%s %s: в базе %r, ожидали %r' % (e['id'], e['field'], cur, e['old'])
        put(card, e['field'], e['new'])
        if e['field'] in FACT:
            fact_edit_guard.log(card, e['field'], e['new'], e['quote'], e['url'], BY, DAY)
        done += 1
        if verbose:
            print('%s %s: %r → %r' % (e['id'], e['field'], str(cur)[:80], str(e['new'])[:80]))
    for cid, key, old, new in COMPANY:
        comp = data['companies'].setdefault(cid, {}) if old is None else data['companies'][cid]
        if comp.get(key) == new:
            skipped += 1
            continue
        assert comp.get(key) == old, '%s.%s: %r' % (cid, key, comp.get(key))
        if new is None:
            comp.pop(key, None)
        else:
            comp[key] = new
        done += 1
        if verbose:
            print('профиль %s.%s: %r → %r' % (cid, key, str(old)[:80], str(new)[:80]))
    for cid, key in MATCH:
        keys = data.setdefault('match_keys', {}).setdefault(cid, [])
        if key not in keys:
            keys.append(key)
            done += 1
    for did, field, value in RETRACT:
        lst = by[did].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
    return done, skipped


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    done, skipped = apply(data, verbose=True)
    print('правок: %d, уже применено: %d' % (done, skipped))
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    if not done:
        print('Все уже применено.')
        rebaseline(json.loads(raw))
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО.')
    rebaseline(fresh)
    return 0


def rebaseline(data):
    """Исправленные вычиткой старые нарушения правил текста уходят из text_rules_baseline.json
    (test_card_text_follows_the_house_rules требует убрать «исправленные»). Только для карточек
    партии и только сокращение списка."""
    import text_rules
    ids = {e['id'] for e in EDITS}
    known = json.load(open(text_rules.BASELINE, encoding='utf-8'))
    now = {f[0] for f in text_rules.all_findings({'deals': [d for d in data['deals'] if d['id'] in ids]})}
    left = [fp for fp in known['known'] if fp.split('|')[0] not in ids or fp in now]
    if len(left) != len(known['known']):
        print('из списка старых нарушений убрано: %d' % (len(known['known']) - len(left)))
        known['known'] = left
        with open(text_rules.BASELINE, 'w', encoding='utf-8') as fh:
            json.dump(known, fh, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
