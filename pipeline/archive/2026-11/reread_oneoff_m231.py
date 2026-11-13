# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m231 (короткая проверка): правки по статьям и ЕГРЮЛ, которые review.py не принимает.

g0e9b1b92 («Тольяттиазот»): продавцы — иностранные компании Сергея Махлая, а не он сам (Ведомости: акции
  «принадлежащие Instantania Holdings и Kamara Ltd.», «компаниям Махлая Trafalgar Trafhold Limited и Bairiki Inc.»).
g3b95a20e («Квадра»): продавцы — четыре ООО Михаила Прохорова, названные Интерфаксом (50% + 24,7% + 4,8% + 2,9%),
  а не «группа».
g3766be95 (небоскреб у моста «Багратион»): MSK1.RU (16.10.2026) — в RWB подтвердили, что актив полностью принадлежит
  компании, здание выкуплено у «Галс-Девелопмента» еще в 2024 году: статус «Закрыта», дата — год (25 декабря 2024 года
  было лишь объявление «выкупает»), заголовок — в прошедшем времени.
gf0796603 («Кама»): дата по ЕГРЮЛ — 11 сентября 2024 года (смена участников; Интерфакс: «в сентябре 2024 года
  завершила сделку»); в заголовке «у структуры Харитонина» — не узнаваемый продавец; seller_id указывал на профиль
  «Структуры Виктора Харитонина», а текст стороны — ООО «Лес Инвест Холдинг»: пара расходилась, профиль снят.
g420af896 (AFI2B): 28–35 млрд ₽ — оценка консультанта IBC Real Estate, не цена (она в eco.val); Commonwealth
  Partnership «выступала консультантом этой сделки» — клиент не назван; заголовок — по покупателю, АО «Толиман».
gac8cfa76 (завод Toyota): покупатель площадки — ООО «Шушары-Авто», дочерняя компания ФГУП «НАМИ» (Ведомости).
g02cbc362 (My.Games): доля без описания компании; заголовок без эпитета «игровой холдинг».
g3ce61e68 («Нефтетранссервис»): по ЕГРЮЛ единственный акционер АО с 2021 года — НТС Холдинг ПиЭлСи, 19 января 2024
  года вместо нее записано ООО «Кинетик капитал»; продавец — она, Аминовы и Лихтенфельд — бенефициары (в eco.context).
g737b71a1 («Русь-Ойл»): изъятие по суду — продавца нет (Хотин признан конечным владельцем-бенефициаром, а не
  акционером); доля без пересказа решения.

    python3 pipeline/archive/2026-11/reread_oneoff_m231.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m231', '2026-11-12'

VED_TOAZ = 'https://www.vedomosti.ru/business/articles/2022/02/08/908415-dmitriya-mazepina-tolyattiazota'
IFX_KV = 'https://www.interfax.ru/business/819454'
MSK1 = 'https://msk1.ru/text/gorod/2026/10/16/76703527/'
IFX_KAMA = 'https://www.interfax.ru/business/1016590'
VED_AFI = 'https://www.vedomosti.ru/realty/articles/2025/01/16/1086650-u-biznes-tsentra-afi2b-ryadom'
VED_TOY = 'https://www.vedomosti.ru/auto/articles/2023/05/03/973639-pvo-poluchil-toyota'
MG = 'https://about.my.games/news/185'
KOM_NTS = 'https://www.kommersant.ru/doc/6413813'
KOM_RO = 'https://www.kommersant.ru/doc/5978359'
EGRUL_KAMA = ('ЕГРЮЛ, ООО «Кама» (ИНН 5916031750): 2024-09-11 вышли ООО «Лес Инвест Холдинг» (99,9%) и МКООО «Огмент '
              'Инвестментс Лимитед» (0,1%), вошло ООО «Свеза»')
EGRUL_NTS = ('ЕГРЮЛ, АО «Нефтетранссервис» (ИНН 7731537410): 2021-07-06 вошла НТС Холдинг ПиЭлСи; 2024-01-19 вышла '
             'НТС Холдинг ПиЭлСи, вошло ООО «Кинетик капитал»')

# (id, поле, старое (строка, или ('^', начало)), новое, цитата, адрес)
SETS = [
    ('g0e9b1b92', 'seller', 'Сергей Махлай через компании (Instantania Holdings, Kamara, Trafalgar Trafhold, Bairiki)',
     'Instantania Holdings Ltd., Kamara Ltd., Trafalgar Trafhold Limited и Bairiki Inc.',
     'На торги были выставлены акции ТоАЗа, принадлежащие Instantania Holdings и Kamara Ltd., бенефициаром которых '
     'является бывший председатель совета директоров, основатель «Тольяттиазота» Сергей Махлай. Торги по продаже еще '
     '32% акций «Тольяттиазота», принадлежащих компаниям Махлая Trafalgar Trafhold Limited и Bairiki Inc.', VED_TOAZ),
    ('g3b95a20e', 'seller', 'Группа «Онэксим»',
     'ООО «Группа «Онэксим»», ООО «Бизнесинформ», ООО «Страховая компания «Согласие»» и ООО «Бона спорт»',
     'Основным акционером компании является ООО "Группа "Онэксим" Михаила Прохорова с долей 50%, ООО "Бизнесинформ" '
     'владеет 24,7%, ООО "Страховая компания "Согласие" - 4,8%, ООО "Бона спорт" - 2,9% (все три также входят в число '
     'активов Михаила Прохорова).', IFX_KV),
    ('g3766be95', 'status', 'Подписана', 'Закрыта',
     'Напомним, что ранее RWB выкупил проект башни у строительной компании «Галс-Девелопмент». Сумму сделки также не '
     'раскрывали, но в компании подтвердили MSK1.RU, что актив теперь полностью принадлежит компании. Здание выкупили '
     'еще в 2024 году.', MSK1),
    ('g3766be95', 'date', '2024-12-25', '2024',
     'Здание выкупили еще в 2024 году.', MSK1),
    ('g3766be95', 'title', 'Wildberries & Russ покупает у «Галс-Девелопмента» небоскреб у моста «Багратион»',
     'Wildberries & Russ купил у «Галс-Девелопмента» небоскреб у моста «Багратион»',
     'Напомним, что ранее RWB выкупил проект башни у строительной компании «Галс-Девелопмент».', MSK1),
    ('gf0796603', 'title', '«Свеза» купила пермский комбинат «Кама» у структуры Виктора Харитонина',
     '«Свеза» купила пермский комбинат «Кама»',
     'Как сообщалось, группа "Свеза", один из крупнейших лесопромышленных холдингов в РФ, в сентябре 2024 года '
     'завершила сделку по приобретению комбината "Кама" и связанных с ним компаний.', IFX_KAMA),
    ('gf0796603', 'date', '2024', '2024-09-11', EGRUL_KAMA, ''),
    ('g420af896', 'eco.sum', '28–35 млрд ₽ (по оценке)', 'Не раскрыта',
     'В «Лукойле», «Толимане» и «Сбережения плюс» на запросы «Ведомостей» не ответили. — цену стороны не назвали, '
     '28–35 млрд ₽ — оценка IBC Real Estate', VED_AFI),
    ('g420af896', 'eco.finadv', 'Commonwealth Partnership — консультант сделки (от комментариев отказался)',
     'Commonwealth Partnership — консультант одной из сторон',
     'В Commonwealth Partnership, которая выступала консультантом этой сделки, от комментариев отказались.', VED_AFI),
    ('g420af896', 'title', 'Компания, связанная с ЛУКОЙЛом, купила бизнес-центр AFI2B в Москве',
     '«Толиман» купил бизнес-центр AFI2B в Москве',
     'АО «Толиман» выкупило у закрытого паевого инвестиционного фонда «Структурные инвестиции – 7» (находится под '
     'управлением ООО «Сбережения плюс», которое до 2022 г. называлось « ВТБ капитал пенсионный резерв») бизнес-центр '
     'AFI2B (50 200 кв. м)', VED_AFI),
    ('gac8cfa76', 'buyer_name', 'ФГУП «НАМИ»', 'ООО «Шушары-Авто» (дочерняя компания ФГУП «НАМИ»)',
     'Саму производственную площадку японского производителя недавно выкупила компания «Шушары-Авто» – «дочка» '
     'ФГУП «НАМИ».', VED_TOY),
    ('g02cbc362', 'eco.share', '100% игрового холдинга My.Games со всеми студиями и играми', '100% My.Games',
     'On September 27, VK announced the sale of 100% of its international game developer and publisher MY.GAMES to '
     'Alexander Chachava, managing partner of LETA Capital.', MG),
    ('g02cbc362', 'title', 'Александр Чачава купил игровой холдинг My.Games у VK за $642 млн',
     'Александр Чачава купил My.Games у VK за $642 млн',
     'On September 27, VK announced the sale of 100% of its international game developer and publisher MY.GAMES to '
     'Alexander Chachava, managing partner of LETA Capital. The deal is valued at $642 million.', MG),
    ('g3ce61e68', 'seller', 'Вячеслав Аминов, Вадим Аминов, Алексей Лихтенфельд', 'НТС Холдинг ПиЭлСи', EGRUL_NTS, ''),
    ('g3ce61e68', 'law.struct', 'Покупатель — закрытый паевой фонд под управлением ООО «Кинетик капитал»; пайщиков '
     'фонда не раскрывают.',
     'Покупатель — закрытый паевой фонд под управлением ООО «Кинетик капитал»; пайщиков фонда не раскрывают. По ЕГРЮЛ, '
     'единственным акционером «Нефтетранссервиса» с 2021 года была НТС Холдинг ПиЭлСи; 19 января 2024 года вместо нее '
     'записано ООО «Кинетик капитал».', EGRUL_NTS, ''),
    ('g737b71a1', 'seller', 'Алексей Хотин', None,
     'Сообщается, что в доход государства также обратят акции и 100% долей в уставных капиталах всех субъектов, '
     'входивших в «Русь-Ойл» — изъятие по суду, продавца нет', KOM_RO),
    ('g737b71a1', 'eco.share', '100% акций АО «Русь-Ойл» и доли во всех компаниях группы (75 юрлиц) обращены в доход '
     'государства', '100% акций АО «Русь-Ойл» и 100% долей компаний группы',
     'Сообщается, что в доход государства также обратят акции и 100% долей в уставных капиталах всех субъектов, '
     'входивших в «Русь-Ойл»', KOM_RO),
]

SRC_ADD = {'g3766be95': ['MSK1.RU (актив принадлежит компании)', MSK1]}
DATE_BASIS = {'gf0796603': 'registry', 'g3766be95': 'closing'}
DROP = {'gf0796603': ['seller_id']}
FIXUP = {
    'g3ce61e68': {'accepted_notes.no_profile.seller': 'Продавец — НТС Холдинг ПиЭлСи, единственный акционер АО по ЕГРЮЛ '
                  'с 06.07.2021 по 19.01.2024 (сайт /api/companies, история участников); иностранная компания, '
                  'российского ИНН и профиля нет. Бенефициары — Вячеслав и Вадим Аминовы и Алексей Лихтенфельд '
                  '(Коммерсантъ), они в eco.context.'},
    'g737b71a1': {'no_parties': 'Изъятие по решению суда: продавца нет, акции и доли перешли Росимуществу.',
                  'accepted_notes.no_profile.seller': 'Продавца нет: изъятие по суду. Прежний конечный владелец — '
                  'Алексей Хотин, признанный судом бенефициаром АО «Русь-Ойл» (Коммерсантъ, РАПСИ).'},
    'gf0796603': {'accepted_notes.no_profile.seller': 'Продавец — ООО «Лес Инвест Холдинг» (99,9% «Камы», Коммерсантъ); '
                  'профиля с этим юрлицом в базе нет, прежняя ссылка вела на профиль «Структуры Виктора Харитонина» — '
                  'не юрлицо, снята. 0,1% принадлежали МКООО «Огмент Инвестментс Лимитед» (ЕГРЮЛ).'},
}


def get(c, path):
    cur = c
    for p in path.split('.'):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def put(c, path, val):
    parts = path.split('.')
    cur = c
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    if val is None:
        cur.pop(parts[-1], None)
    else:
        cur[parts[-1]] = val


def same_old(cur, old):
    if isinstance(old, tuple):
        return isinstance(cur, str) and cur.startswith(old[1])
    return cur == old


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, field, old, new, quote, url in SETS:
        c = by[cid]
        cur = get(c, field)
        if cur == new:
            continue
        assert same_old(cur, old), (cid, field, cur)
        if field in ('status', 'seller', 'asset', 'buyer_name', 'eco.sum') and cur and not isinstance(old, tuple):
            key = 'sum' if field == 'eco.sum' else field
            c.setdefault('retracted', {}).setdefault(key, []).append(cur)
        put(c, field, new)
        if field == 'eco.sum' and c.get('sum') is not None:
            c['sum'] = new
            fact_edit_guard.log(c, 'sum', new, quote, url, BY, DAY)
        if field == 'date' and cid in DATE_BASIS:
            c['date_basis'] = DATE_BASIS[cid]
        fact_edit_guard.log(c, field, new, quote, url, BY, DAY)
        n += 1
    for cid, item in SRC_ADD.items():
        if all(s[1] != item[1] for s in by[cid]['src']):
            by[cid]['src'].append(item)
            n += 1
    for cid, keys in DROP.items():
        for k in keys:
            if k in by[cid]:
                by[cid].pop(k)
                n += 1
    for cid, kv in FIXUP.items():
        for path, val in kv.items():
            if get(by[cid], path) != val:
                put(by[cid], path, val)
                n += 1
    for cid, basis in DATE_BASIS.items():
        if by[cid].get('date_basis') != basis:
            by[cid]['date_basis'] = basis
            n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
