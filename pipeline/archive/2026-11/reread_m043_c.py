# -*- coding: utf-8 -*-
"""Вычитка, марафон 12 ноября 2026, партия m043 (часть c): поля, которые таблица правок не берет.

g21beb4c1 («Урал»): год 2024 → 2023 (Интерфакс 31.05.2023: сделка закрыта); покупатель «Менеджмент…» —
  роль, а не имя: «компания, связанная с менеджментом», название не раскрыто — поле пустое с причиной.
g8fb922a6 («Легион II»): по ЕГРЮЛ ООО «Легион II» 13.04.2023 перешло от структур Siemens к ИГ «Инсайт»;
  дата — день закрытия (Ведомости: «закрылась 13 апреля»), а не статьи; оценка 7–10 млрд ₽ стояла в
  сумме (оценке место не в сумме) и в источниках не найдена — снята.
g23827051 («Трилоджи парк Томилино»): покупатели — Алексей и Александр Остапишины (Ведомости), а не
  «структуры братьев»; доля PPF не раскрыта (75% — раскрытие 2014 года), ООО «Томилино парк» по ЕГРЮЛ
  с 2022 года принадлежало Остапишину — предметом этой сделки не доказано, предмет — текстом;
  дата — год (статья 20.02.2023 о будущей сделке); оценка 6,2–7,5 млрд ₽ не найдена — снята.
gcbcd9b28 (Food Miles): год 2024 → 2023 (RB.ru и Retail.ru, 28.02.2023; по ЕГРЮЛ — конец января).
gb7a906e5 (Brookes): дата — год (Ведомости 27.01.2023 писали о будущей сделке, КП: «в начале прошлого
  года»), заголовок по стандарту.
gdf91b653 («Крекшино»): дата 17 января (Ведомости по СПАРК, ЕГРЮЛ), тип — Инвестиция (24,99% без
  контроля), предмет назван юрлицом.
Описания профилей — род занятий без пересказа сделки и без неверных лет.

Запуск: python3 pipeline/archive/2026-11/reread_m043_c.py [--write]
"""
import copy
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка m043, 12.11.2026'
IFX = 'https://www.interfax.ru/business/916354'
RETAIL = 'https://www.retail.ru/news/novym-sobstvennikom-kompanii-peredovye-platezhnye-resheniya-stala-kismet-capital-group/'
VED_TM = 'https://www.vedomosti.ru/realty/articles/2023/08/10/989374-central-properties-nashla-partnera-na-pokupku-torgovogo-tsentra'
REG_IIK = 'https://datanewton.ru/api/v2/history?ogrn=1036405019144&startDate=2000-01-01&attributes=OWNERS'
VED_MS = 'https://www.vedomosti.ru/realty/articles/2023/08/11/989571-set-gibkih-ofisov-multispace-mozhet-vikupit-biznes-tsentr'
KOM_KAMA = 'https://www.kommersant.ru/doc/6122479'
RENERA = 'g' + hashlib.md5('Рэнера Росатом'.encode()).hexdigest()[:8]


def setf(card, field, old, new, quote, url):
    """Поле-факт с assert на старое значение и цитатой в fact_log; повтор — «уже применено»."""
    path = field.split('.')
    obj = card
    for p in path[:-1]:
        obj = obj.setdefault(p, {})
    cur = obj.get(path[-1])
    if cur == new:
        return False
    assert cur == old, '%s %s: ожидали %r, стоит %r' % (card['id'], field, old, cur)
    obj[path[-1]] = new
    if field not in ('eco.sum',):
        fact_edit_guard.log(card, field, new, quote, url, BY)
    return True


def add_src(card, label, url):
    if url not in [u for _l, u in card.get('src') or []]:
        card.setdefault('src', []).append([label, url])
        return True
    return False


IFX_URAL = 'https://www.interfax.ru/amp/904182'
VED_LEG = 'https://www.vedomosti.ru/realty/articles/2023/04/21/971880-bivshii-top-menedzher-holdinga-gutserieva-vikupil-esche-odin-aktiv-siemens'
REG_LEG = 'https://datanewton.ru/api/v2/history?ogrn=5067746348632&startDate=2000-01-01&attributes=OWNERS'
VED_TOM = 'https://www.vedomosti.ru/business/articles/2023/02/20/963577-ppf-group-prodast-dolyu-v-logoparke?shared_token=ce04f21d725ed2f091020e25cd4997a12ed1abd3'
RIA_PPF = 'https://realty.ria.ru/20231218/ppf-1916403264.html'
RB_FM = 'https://rb.ru/news/food-miles'
RET_FM = 'https://www.retail.ru/news/osnovatel-vkusvilla-vlozhilsya-v-servis-dostavki-fermerskikh-produktov-food-mile-28-fevralya-2023-226241/'
VED_RYB = 'https://www.vedomosti.ru/society/articles/2023/01/27/960635-ribakov-pokupaet-odnu-iz-chastnih-shkol'
KP_RYB = 'https://www.kp.ru/daily/27607.5/4958038/'
VED_KR = 'https://www.vedomosti.ru/realty/articles/2023/01/19/959595-sberbank-stal-sovladeltsem-skladskogo-kompleksa-krekshino'


def set_desc(p, start, new):
    if p.get('desc') == new:
        return 0
    assert p['desc'].startswith(start), p['desc']
    p['desc'] = new
    return 1


def set_prop(p, key, new):
    if p.get(key) == new:
        return 0
    p[key] = new
    return 1


def drop_sum(c, old, quote, url):
    if c.get('sum') == 'Не раскрыта':
        return 0
    assert c['sum'] == old and c['eco']['sum'] == old, (c['id'], c['sum'])
    c['sum'] = c['eco']['sum'] = 'Не раскрыта'
    for f in ('sum', 'eco.sum'):
        fact_edit_guard.log(c, f, 'Не раскрыта', quote, url, BY + ': оценка не цена сделки, в источниках не найдена')
    return 1


def apply(data):
    deals = {d['id']: d for d in data['deals']}
    comp = data['companies']
    n = 0

    # --- g21beb4c1 «Урал»
    c = deals['g21beb4c1']
    q = ('По его словам, сделка по продаже Стрежневым акций АО "Автомобильный завод "Урал" закрыта. Покупателем '
         'выступила компания, связанная с менеджментом предприятия.')
    n += setf(c, 'date', '2024', '2023', 'Москва. 31 мая. INTERFAX.RU Активы автозавода "Урал" (Миасс Челябинской области), '
              'принадлежавшие бизнесмену Дмитрию Стрежневу, проданы менеджменту предприятия', IFX_URAL)
    n += setf(c, 'buyer', 'g21934e29', None, q, IFX_URAL)
    n += setf(c, 'title', 'Дмитрий Стрежнев продал автозавод «Урал» менеджменту',
              'Компания менеджмента купила автозавод «Урал» у Дмитрия Стрежнева', q, IFX_URAL)
    note = ('Покупатель — «компания, связанная с менеджментом предприятия» (Интерфакс, 31.05.2023), название не '
            'раскрыто; искали: Интерфакс (рус. и англ.), Ведомости (2023, о заводе Volvo в Калуге), ДП, drom.ru, '
            'Миасский рабочий, веб-поиск по новым акционерам АО «АЗ «Урал» — реестр акционеров АО не публичен')
    an = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    if an.get('buyer') != note:
        an['buyer'] = note
        n += 1
    n += set_desc(comp['g21934e29'], 'Группа топ-менеджеров',
                  'Компания, связанная с менеджментом автозавода «Урал» (Миасс); название не раскрывалось.')
    n += set_desc(comp['g999eef95'], 'Производитель тяжелых грузовиков',
                  'Производитель тяжелых грузовиков и спецтехники на их шасси в Миассе (Челябинская область).')
    n += set_prop(comp['g999eef95'], 'legal_short', 'АО «АЗ «Урал»')

    # --- g8fb922a6 «Легион II»
    c = deals['g8fb922a6']
    n += setf(c, 'date', '2023-04-21', '2023-04-13',
              'По его словам, сделка была одобрена правительственной комиссией по контролю за иностранными '
              'инвестициями, она закрылась 13 апреля.', VED_LEG)
    if c.get('date_basis') != 'closing':
        c['date_basis'] = 'closing'
    n += drop_sum(c, '7–10 млрд ₽ (по оценке)', 'По его словам, сделка была одобрена правительственной комиссией '
                  'по контролю за иностранными инвестициями, она закрылась 13 апреля. Условия соглашения он раскрывать '
                  'не стал.', VED_LEG)
    n += setf(c, 'title', 'Siemens продал бизнес-центр «Легион II» инвесткомпании «Инсайт»',
              '«Инсайт» купил бизнес-центр «Легион II» у Siemens',
              'Структуры немецкого концерна Siemens продали бизнес-центр «Легион II» (27 600 кв. м) … По их словам, '
              'покупателем комплекса стала инвестиционная группа «Инсайт».', VED_LEG)
    n += add_src(c, 'ЕГРЮЛ: история участников ООО «Легион II»', REG_LEG)
    p = comp['gba35c8d8']
    n += set_prop(p, 'name', 'Бизнес-центр «Легион II»')
    n += set_prop(p, 'legal_short', 'ООО «Легион II»')
    n += set_desc(p, 'Бизнес-центр «Легион II»; в 2023',
                  'Бизнес-центр на 27 600 кв. м на Большой Татарской улице в Замоскворечье; построен в 2007 году.')
    n += set_prop(comp['g21fac69d'], 'legal_short', 'ООО «Инвестиционная группа «Инсайт»')

    # --- g23827051 «Трилоджи парк Томилино»
    c = deals['g23827051']
    qv = ('Покупателями, по их словам, станут девелоперы и совладельцы этого объекта Алексей и Александр Остапишины.')
    n += setf(c, 'date', '2023-02-20', '2023', qv, VED_TOM)
    n += drop_sum(c, '6,2–7,5 млрд ₽ (по оценке)', 'Размер доли, которая была у PPF Real Estate в логопарке, '
                  'собеседники «Ведомостей» не уточнили.', VED_TOM)
    if c['eco'].get('val') != '—':
        assert c['eco']['val'] == 'Сумма не раскрыта; объект оценивают в 6,2–7,5 млрд ₽.'
        c['eco']['val'] = '—'
        n += 1
    n += setf(c, 'target', 'g39d6172a', None, 'Входящая в чешскую PPF Group фирма PPF Real Estate нашла покупателей '
              'на свою долю в складском комплексе «Трилоджи парк Томилино» (107 000 кв. м)', VED_TOM)
    n += setf(c, 'asset', None, 'Доля PPF Real Estate в складском комплексе «Трилоджи парк Томилино» (107 000 кв. м)',
              'PPF Real Estate нашла покупателей на свою долю в складском комплексе «Трилоджи парк Томилино» (107 000 кв. м)',
              VED_TOM)
    n += setf(c, 'title', 'PPF Real Estate продала 75% логопарка «Трилоджи парк Томилино» братьям Остапишиным',
              'Алексей и Александр Остапишины купили у PPF Real Estate долю в «Трилоджи парк Томилино»', qv, VED_TOM)
    n += add_src(c, 'РИА Недвижимость', RIA_PPF)
    p = comp['g55752f80']
    n += set_prop(p, 'name', 'Алексей и Александр Остапишины')
    n += set_desc(p, 'Структуры Алексея и Александра Остапишиных',
                  'Девелоперы и совладельцы складского комплекса «Трилоджи парк Томилино»; Алексей Остапишин — '
                  'гендиректор управляющей компании «Трилоджи».')
    n += set_desc(comp['g39d6172a'], 'Складской комплекс, ранее принадлежал',
                  'Владелец складского комплекса «Трилоджи парк Томилино» (107 тыс. кв. м) на Новорязанском шоссе.')
    n += set_desc(comp['g7b8bd1f5'], 'В 2023 году продала 75%',
                  'Девелоперская компания чешской PPF Group, владела офисной и складской недвижимостью в Москве '
                  'и Подмосковье; к концу 2023 года ушла из России.')

    # --- gcbcd9b28 Food Miles
    c = deals['gcbcd9b28']
    n += setf(c, 'date', '2024', '2023',
              'Сумма сделки не уточняется, по данным ЕГРЮЛ, она состоялась в конце января.', RET_FM)
    n += setf(c, 'title', 'ТилТех Капитал приобрел 20% Food Miles', '«ТилТех Капитал» купил 20% Food Miles',
              'Инвестфонд «ТилТех Капитал» приобрел 20% аутсорс-сервиса Food Miles', RB_FM)
    n += add_src(c, 'Retail.ru', RET_FM)
    p = comp['gedcf4bdc']
    n += set_prop(p, 'legal_short', 'ООО «Фуд Майлз»')
    n += set_desc(p, 'Продуктовый стартап; в 2024',
                  'Сервис логистики и сбыта для малых и средних фермерских хозяйств: поставляет их продукцию в '
                  'крупные торговые сети.')

    # --- gb7a906e5 Brookes
    c = deals['gb7a906e5']
    n += setf(c, 'date', '2023-01-27', '2023',
              'В начале прошлого года появилась информация, что Игорь Рыбаков выкупил у группы «Пионер» весь '
              'комплекс зданий', KP_RYB)
    n += setf(c, 'title', 'Группа «Пионер» продала здание школы Brookes School Moscow Игорю Рыбакову',
              'Игорь Рыбаков купил комплекс Brookes School Moscow у группы «Пионер»',
              'Игорь Рыбаков выкупил у группы «Пионер» весь комплекс зданий общей площадью более 20 000 м2 где '
              'располагается образовательный комплекс BROOKES SCHOOL MOSCOW', KP_RYB)
    n += set_desc(comp['g601bcc88'], 'Сооснователь «Технониколь»',
                  'Сооснователь «Технониколь», основатель «Рыбаков фонда».')
    n += set_desc(comp['gc6400e24'], 'Здание частной школы в Москве',
                  'Образовательный комплекс в Botanica у метро «Ботанический сад»: школа, ясли и детский сад '
                  'примерно на 800 человек, 18 358 кв. м; открыт в 2018 году.')
    p = comp['gc1321af8']
    n += set_desc(p, 'Девелопер; в 2023', 'Девелопер жилой и коммерческой недвижимости в Москве.')
    n += set_prop(p, 'legal_short', 'АО «ГК «Пионер»')

    # --- gdf91b653 «Крекшино»
    c = deals['gdf91b653']
    qk = ('Входящая в группу Сбербанка компания « Сбербанк инвестиции» получила 24,99% долей в ООО «Вудвелл '
          'инвестментс лимитед»')
    n += setf(c, 'date', '2023-01-19', '2023-01-17', 'По данным «СПАРК-Интерфакса», сделка закрыта 17 января.', VED_KR)
    if c.get('date_basis') != 'registry':
        c['date_basis'] = 'registry'
    n += setf(c, 'type', 'M&A', 'Инвестиция', qk, VED_KR)
    n += setf(c, 'title', 'Сбербанк Инвестиции приобрела 25% компании-собственника складского комплекса «Крекшино»',
              '«Сбербанк Инвестиции» купила 24,99% владельца складского комплекса «Крекшино»', qk, VED_KR)
    p = comp['g49c5ecec']
    n += set_prop(p, 'name', 'Вудвелл Инвестментс Лимитед')
    n += set_prop(p, 'legal_short', 'ООО «Вудвелл Инвестментс Лимитед»')
    n += set_desc(p, 'Владеет складским комплексом',
                  'Через ООО «Феникс-К» владеет складским комплексом «Крекшино» (253 000 кв. м) и 22 га земли в новой Москве.')
    p = comp['gbc011965']
    n += set_prop(p, 'ind', 'Недвижимость')
    n += set_desc(p, 'Московская компания; в январе 2023',
                  'Компания девелопера Malltech; с декабря 2022 года участник ООО «Вудвелл Инвестментс Лимитед».')
    # Ключи поиска упоминаний — под новые имена профилей (test_match_key_alias_is_a_name).
    mk = data['match_keys']
    for cid, keys in (('g55752f80', ['алексей и александр остапишины', 'братьев остапишиных', 'остапишины']),
                      ('gba35c8d8', ['легион ii', 'легион']),
                      ('g49c5ecec', ['вудвелл инвестментс лимитед', 'вудвелл инвестментс'])):
        if mk.get(cid) != keys:
            mk[cid] = keys
            n += 1
    return n


def main(argv):
    old = json.load(open(DATA, encoding='utf-8'))
    new = copy.deepcopy(old)
    n = apply(new)
    print('изменений: %d' % n)
    if not n:
        print('уже применено')
        return 0
    mass_edit_guard.check(old, new, os.environ.get('MASS_OK'))
    if '--write' in argv:
        cur = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
        apply(cur)
        json.dump(cur, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('записано')
    else:
        print('сухой прогон; запись — --write')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
