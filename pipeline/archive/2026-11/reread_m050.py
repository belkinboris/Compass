# -*- coding: utf-8 -*-
"""Вычитка базы, марафон 12 ноября 2026, партия m050: правки, которые не ложатся в таблицу FIXES.

ЧТО ЧИНИТ. Поля-факты, подтвержденные статьей или реестром (заголовок по стандарту
`pipeline/title_standard.py`, дата события вместо выдуманного 1-го числа, продавец по истории
участников ЕГРЮЛ, предмет и доля), снятие неподтвержденных значений и тексты профилей сторон.
Каждая правка факта несет цитату источника (`fact_edit_guard.log`), перед записью стоит
`assert` на старое значение; повторный запуск пропускает уже примененное.

ПОЧЕМУ НЕ review.py. Дата годом или из реестра, снятие значений, заголовок своей фразой и
профили компаний таблица FIXES не переносит.

Поиск источников — в note ответа каждой карточки (answers_m050.json партии).

    python3 pipeline/archive/2026-11/reread_m050.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_m050.py --write    # запись (делает reread_apply.py)
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
DAY, BY = '2026-11-12', 'reread_m050'
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

K_SOKRA = 'https://www.kommersant.ru/doc/6160637'
Q_SOKRA = ('ООО «Восточный актив» договорилось со Сбербанком об уступке прав требований к ООО «Рыбоперерабатывающий завод '
           '"Сокра"» на Камчатке, следует из картотеки арбитражных дел. В рамках взыскания банком с компании 1,19 млрд руб. '
           'арбитражный суд Камчатского края 9 августа произвел замену истца на «Восточный актив».')
EDITS += [
 # g65d042bc «Сокра»: Ткачев в заголовке — версия источников Ъ («может действовать в интересах»), а не сторона;
 # 1 августа 2023 — выдуманный день: день уступки не назван (суд заменил истца 9 августа), дата — годом.
 dict(id='g65d042bc', field='title', old='Структура Александра Ткачева выкупила долги рыбозавода «Сокра» у Сбербанка',
      new='«Восточный актив» купил у Сбербанка долги завода «Сокра»', quote=Q_SOKRA, url=K_SOKRA),
 dict(id='g65d042bc', field='date', old='2023-08-01', new='2023',
      quote=Q_SOKRA + ' — день самой уступки в источниках не назван (Ъ, 15.08.2023).', url=K_SOKRA),
]
COMPANY += [
 ('g302361d5', 'legal_short', None, 'ООО «Восточный актив»'),
 ('g302361d5', 'desc', 'Структура Александра Ткачева и Евгения Свистулы; в 2023 году выкупила у Сбербанка долги рыбоперерабатывающего завода «Сокра», получив право определять судьбу должника.',
  'Краснодарская компания Евгения Свистулы. В 2023 году купила у Сбербанка долги камчатского завода «Сокра» и стала владельцем ООО «Витязь Авто»; по неофициальным данным, может действовать в интересах Александра Ткачева.'),
 ('g23f61dc8', 'legal_short', None, 'ООО «РПЗ «Сокра»»'),
 ('g23f61dc8', 'desc', 'Долги рыбоперерабатывающего завода «Сокра» на Камчатке; в 2023 году их у Сбербанка выкупила структура Александра Ткачева и Евгения Свистулы, получив право определять судьбу должника.',
  'Долги камчатского рыбоперерабатывающего завода «Сокра» (ООО «РПЗ «Сокра»») перед Сбербанком; в 2023 году банк уступил их ООО «Восточный актив». В декабре 2023 года завод признан банкротом.'),
]

K_POP = 'https://www.kommersant.ru/doc/6149674'
API_POP = 'https://projectcompass.ru/api/companies/g066e7011/fns'
Q_POP = ('Издательство «Эксмо» получило контроль над Popcorn Books, которое ориентируется на выпуске книг для молодежи. '
         'Сумма покупки 51% в ООО «Попкорн Букс» не раскрывается.')
Q_REG_POP = ('ЕГРЮЛ (API-ФНС), ООО «Попкорн Букс» (ИНН 9718154910): запись от 2023-08-10 — Котов Денис Алексеевич 100% → 49%, '
             'ООО "ИЗДАТЕЛЬСТВО "ЭКСМО" вошло с 51%.')
EDITS += [
 # g5792754e «Эксмо» / Popcorn Books: 40–60 млн ₽ — оценка Михаила Бурмистрова («Infoline»), а не цена сделки
 # (стороны сумму не раскрыли) — уходит в eco.val с именем; 1 августа — выдуманный день, переход доли — 10.08.2023.
 dict(id='g5792754e', field='title', old='Эксмо приобрела 51% издательства Popcorn Books',
      new='«Эксмо» купило 51% Popcorn Books', quote=Q_POP, url=K_POP),
 dict(id='g5792754e', field='date', old='2023-08-01', new='2023-08-10', quote=Q_REG_POP, url=API_POP),
 dict(id='g5792754e', field='date_basis', old=None, new='registry', quote='', url=''),
 dict(id='g5792754e', field='sum', old='40–60 млн ₽ (по оценке)', new='Не раскрыта', quote=Q_POP, url=K_POP),
 dict(id='g5792754e', field='eco.sum', old='40–60 млн ₽ (по оценке)', new='Не раскрыта', quote=Q_POP, url=K_POP),
]
RETRACT += [('g5792754e', 'sum', '40–60 млн ₽ (по оценке)')]
COMPANY += [
 ('g6f9c9a9c', 'legal_short', None, 'ООО «Издательство «Эксмо»»'),
 ('g066e7011', 'legal_short', None, 'ООО «Попкорн Букс»'),
]

IF_VOS = 'https://www.interfax.ru/business/912966'
Q_VOS = ('ПАО АФК "Система" продало 22,5% ООО "Рыбопромышленный холдинг "Восход"" компании АО "Краунинвест" Ольги Зачиняевой; '
         'информация о переходе прав собственности содержится в аналитической системе " СПАРК-Интерфакс ". '
         'Сделка состоялась 21 июля, по ее итогам "дочка" "Системы" - АО "Море проект" сохранило за собой 77,5% РПХ "Восход".')
EDITS += [
 # g424715f8 «Восход»: заголовок по стандарту; день 21 июля — и в Интерфаксе, и в ЕГРЮЛ (запись 2023-07-21).
 dict(id='g424715f8', field='title', old='АФК «Система» продала 22,5% ООО «Рыбопромышленный холдинг «Восход»» компании АО «Краунинвест»',
      new='«Краунинвест» купил 22,5% рыбного холдинга «Восход» у АФК «Система»', quote=Q_VOS, url=IF_VOS),
 dict(id='g424715f8', field='date_basis', old=None, new='registry', quote='', url=''),
]
COMPANY += [
 ('g72611cf4', 'legal_short', None, 'ООО РПХ «Восход»'),
 ('g2a237114', 'legal_short', None, 'АО «Краунинвест»'),
]

K_VET = 'https://www.kommersant.ru/doc/6149270'
REG_VET = 'https://datanewton.ru/api/v2/history?ogrn=5077746936053&startDate=2000-01-01&attributes=OWNERS'
Q_VET = ('Информацию о том, что Дмитрий Кокин стал единственным владельцем ООО «Вет Юнион» — операционной компании сети ветклиник '
         'Vet Union, входящей в «Инвитро», “Ъ” обнаружил в ЕГРЮЛ.')
Q_REG_VET = ('Запись ЕГРЮЛ от 2023-07-20 (20 июля 2023 года): было — КОМПАНИЯ "ИНВИТРО ХОЛДИНГ ЛИМИТЕД" 100%; (10 000 руб.); '
             'стало — выбыл. … стало — КОКИН ДМИТРИЙ ВЛАДИМИРОВИЧ (ИНН: 772583399102) 100%')
Q_VAL_VET = 'Гендиректор DSM Group Сергей Шуляк оценивает текущую стоимость сети в 200–250 млн руб.'
EDITS += [
 # g937b94f4 Vet Union: 200–250 млн ₽ — оценка стоимости сети аналитиком DSM Group, не цена сделки; продавец — по ЕГРЮЛ
 # компания «Инвитро Холдинг Лимитед»; цель сделки стояла версией Габышева о финансировании «Инвитро» — это контекст.
 dict(id='g937b94f4', field='title', old='Продажа сети ветеринарных клиник Vet Union (Инвитро) Дмитрию Кокину',
      new='Дмитрий Кокин купил сеть ветклиник Vet Union у «Инвитро»', quote=Q_VET, url=K_VET),
 dict(id='g937b94f4', field='seller', old=None, new='Компания «Инвитро Холдинг Лимитед»', quote=Q_REG_VET, url=REG_VET),
 dict(id='g937b94f4', field='date_basis', old=None, new='registry', quote='', url=''),
 dict(id='g937b94f4', field='sum', old='200–250 млн ₽ (по оценке)', new='Не раскрыта', quote=Q_VAL_VET, url=K_VET),
 dict(id='g937b94f4', field='eco.sum', old='200–250 млн ₽ (по оценке)', new='Не раскрыта', quote=Q_VAL_VET, url=K_VET),
 dict(id='g937b94f4', field='eco.rationale', old='Есть версия Дмитрия Габышева, управляющего директора Peregrine Capital: Кокин, возможно, отчасти дал средства на покупку основного бизнеса «Инвитро», а потом его заем стал долей в других структурах холдинга. По данным СПАРК, Газпромбанк тоже мог участвовать в финансировании: 100% головной структуры «Инвитро» заложены у банка.', new='—', quote='', url=''),
 dict(id='g937b94f4', field='extra', old='Сделка включала продажу 100% ООО «Вет Юнион» (операционная компания сети из трех ветклиник и лаборатории), 74,9% в «Проактив Информ» (управлял медиапроектами) и 76% в «Раритас Тера». Оставшиеся доли перешли Роману Мирончику.', new='—', quote='', url=''),
]
RETRACT += [('g937b94f4', 'sum', '200–250 млн ₽ (по оценке)')]
COMPANY += [
 ('geca16a9c', 'desc', 'Три актива сети ветклиник Vet Union (Инвитро) — операционная компания и два смежных бизнеса; в 2024 году проданы Дмитрию Кокину.',
  'Сеть ветеринарных клиник Vet Union (три клиники и лаборатория для животных) с двумя смежными компаниями «Инвитро»; в июле 2023 года все перешло Дмитрию Кокину.'),
]

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
