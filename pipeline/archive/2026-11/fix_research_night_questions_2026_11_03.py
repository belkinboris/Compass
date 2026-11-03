# -*- coding: utf-8 -*-
"""Ответы на вопросы ночной вычитки 3 ноября 2026 — найдены поиском, а не владельцем.

ЗАЧЕМ. Ночью 3 ноября прогоны вычитки отправили владельцу 15 вопросов, поискав в двух-трех
изданиях. Владелец: «мы же обсуждали, что сначала ты сам ресерчишь, а потом спрашиваешь у
создателей». Пять агентов-исследователей прочитали первоисточники (раскрытие эмитентов,
отчеты компаний, суды, отчет Росимущества, реестр ФНС); здесь — их ответы. Правило «сначала
поиск» записано в routines/reread.md (шаг 7).

Что меняется (точечно, подтвержденное в карточках не трогаем):
- g2b1fe015 «Точка»: стороны — юрлицами из раскрытия (AK&M, согласие акционеров МКПАО «ВК»):
  продавец ООО «Компания ВК», покупатель МКООО «Интеррос Капитал», предмет — акции АО «Точка».
- gbc48b9e4 Prosto Barista: к профилю сети было привязано чужое ООО «Просто Бариста» (Элиста,
  зарегистрировано в декабре 2024 года, ОКВЭД — опт машин, выручка 125 тыс. ₽); сеть основана в
  2021 году Миннигалиным и Пономаревым. legal_short снят, решение реестра — brand_needs_inn.
- g703d5597 «Кама»: продавец по истории участников ООО «Кама» в ЕГРЮЛ — «ФК Открытие»
  (вышло 10.02.2023 со 100%); «Траст» вел продажу и остается в тексте.
- g06b7ba6e «Полюс»: продавец — «Группа Акрополь»: годовой отчет «Полюса» за 2023 год —
  «AKROPOL GROUP LTD controlled by Akhmet Palankoyev ceased to be a shareholder».
- g796316fe «Делимобиль»: покупатель — ООО «Делимобиль Холдинг» (реестр акционеров на сайте
  компании: 90,9871% на 30.06.2026 = 78,08% + 12,9069% пакета «Дельты»); 66,15% — неверный
  пересчет CNews, снят из карточки и профиля Трани.
- gdde6bef5 Whoosh/«Юрент»: роли — покупатель Whoosh, покупаемая компания «Юрент», продавец МТС
  (Интерфакс: «"ВУШ Холдинг" подтвердил факт переговоров о присоединении "ЮрентБайк.ру"»).
  Сведения, которые есть только у РБК, остаются с пометкой «по данным РБК».
- g420cae8d «Авито»: «Naspers настоял на lock-up 18–24 месяца» не подтверждено; The Bell со
  ссылкой на два источника — два года «Авито» нельзя передать третьим лицам; релиз Naspers —
  «certain deal protection mechanisms in favour of the Sellers».
- gd01de1ad «Стокманн»: сделка 2017 года (дата в карточке была днем судебного решения, которое
  отменили); итог спора — Верховный суд в мае 2024 года (Коммерсантъ), экспертиза в апелляции —
  около 48 млн ₽ (ЭПАМ).
- g71aec6a5 «Роснефть — Артаг»: по отчету Росимущества о приватизации за 2025 год пакет продан
  25.09.2025 по минимально допустимой цене Павлу Тимофееву за 5 100 000 ₽ (начальная —
  3 800 800 ₽); торги 2023 года и аукцион июня 2025 года пакет не продали.
- g3cc2009d УГМК/Petropavlovsk: юристы продажи подтверждены решением Высокого суда Англии
  [2022] EWHC 2097 (Ch); DAC Beachcroft, Shoosmiths и Isadore Goldman по смете управляющих вели
  трудовые претензии и аренду — консультанты процедуры, не сделки (docs/card_parties.md).
- gecc48c49 Qiwi/RealWeb: iTech Capital не продавал (25% после сделки — у кипрской компании,
  CNews); вышли из бизнеса Лазука, Виноградов и Хмелевской (Inc. по Forbes); O2Consulting —
  сообщение самой фирмы.
- g02eed099 «Лента»/OBI: сумма — диапазон, на котором сходятся оценки (3–6 млрд ₽), по правилу
  docs/card_money.md (13.10.2026); оценку CORE.XP дала Светлана Шорина (Деловой Петербург).
- g3bb1fadb Wintershall/OMV, продажа 2026 года: номера распоряжений, цены по долям и дата
  16.04.2026 (Neftegaz.RU, Интерфакс). Решение «одна карточка или две» и снятие g4cd1fa52 —
  за владельцем, здесь не делается.

Каждое меняемое поле, у которого есть записи FIXES, получает отпечатки этих записей в
proofread_absorbed (docs/card_editing.md, «Правка поля мимо таблицы синхронизирует запись»).

    python3 pipeline/archive/2026-11/fix_research_night_questions_2026_11_03.py          # сухой прогон
    python3 pipeline/archive/2026-11/fix_research_night_questions_2026_11_03.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import review  # noqa: E402
import accept_card  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CHANGED = []          # (id, поле) — для синхронизации записей FIXES


def get(card, field):
    v = card
    for p in field.split('.'):
        v = v.get(p) if isinstance(v, dict) else None
    return v


def put(card, field, old, new):
    parts = field.split('.')
    obj = card
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    cur = obj.get(parts[-1])
    if cur == new:
        return
    assert cur == old, (card['id'], field, cur)
    obj[parts[-1]] = new
    CHANGED.append((card['id'], field))


def replace_in(card, field, old_part, new_part):
    cur = get(card, field)
    if new_part and new_part in (cur or '') and old_part not in (cur or ''):
        return
    assert old_part in (cur or ''), (card['id'], field, cur)
    put(card, field, cur, cur.replace(old_part, new_part))


def add_src(card, name, url):
    if any(s[1] == url for s in card.get('src') or []):
        return
    card.setdefault('src', []).append([name, url])


def new_profile(data, name, ind, desc, legal_short=None):
    for cid, c in data['companies'].items():
        if c.get('name') == name:
            return cid
    cid = accept_card._new_profile_id(data, name)
    prof = {'name': name, 'ind': ind, 'desc': desc, 'kpi': []}
    if legal_short:
        prof['legal_short'] = legal_short
    data['companies'][cid] = prof
    print('  новый профиль %s %s' % (cid, name))
    return cid


def apply(data):
    D = {d['id']: d for d in data['deals']}
    C = data['companies']

    # ---- Точка
    t = D['g2b1fe015']
    ic = new_profile(data, 'МКООО «Интеррос Капитал»', 'Холдинги',
                     'Инвестиционная компания группы «Интеррос» Владимира Потанина.', 'МКООО «Интеррос Капитал»')
    vk = new_profile(data, 'ООО «Компания ВК»', 'ИТ и интернет',
                     'Дочерняя компания МКПАО «ВК»; через нее VK владела 25% акций АО «Точка».', 'ООО «Компания ВК»')
    at = new_profile(data, 'АО «Точка»', 'Банки',
                     'Держатель банка «Точка» для предпринимателей и малого бизнеса.', 'АО «Точка»')
    put(t, 'buyer', 'g088e8f9f', ic)
    put(t, 'seller', 'VK', 'ООО «Компания ВК»')
    put(t, 'seller_id', 'g4e694234', vk)
    put(t, 'target', 'g09ccbaca', at)

    # ---- Prosto Barista
    pb = C['gprostobarista']
    assert pb.get('legal_short') == 'ООО «Просто Бариста»'
    del pb['legal_short']
    fx = (D['gbc48b9e4'].get('facts') or {}).get('target') or {}
    if fx.get('inn') == '0800024709':
        D['gbc48b9e4']['facts'].pop('target')

    # ---- Кама
    k = D['g703d5597']
    put(k, 'seller', 'Банк непрофильных активов «Траст»', 'ФК Открытие')
    put(k, 'seller_id', 'gdc4235da', 'g7ac0b3cc')

    # ---- Полюс
    p = D['g06b7ba6e']
    ak = new_profile(data, 'Группа Акрополь', 'Холдинги',
                     'Компания Ахмета Паланкоева (AKROPOL GROUP LTD); в 2022 году получила 29,99% «Полюса», '
                     'в 2023 году перестала быть его акционером.')
    put(p, 'seller', None, 'Группа Акрополь')
    put(p, 'seller_id', None, ak)
    put(p, 'seller_src', None, 'text')
    replace_in(p, 'extra',
               'Кто продал акции, компания не сообщила. До выкупа 29,99% «Полюса» владела «Группа Акрополь» '
               'Ахмета Паланкоева; по оценке «ВЕЛЕС Капитала», выкуп прошел в основном в ее пользу.',
               'Кто продал акции, компания прямо не сообщила. До выкупа 29,99% «Полюса» владела «Группа '
               'Акрополь» Ахмета Паланкоева; в годовом отчете за 2023 год «Полюс» записал, что в том году '
               '«Акрополь» перестал быть его акционером, а выкуплено было 40 799 587 акций — почти весь ее пакет.')
    add_src(p, 'Полюс (годовой отчет за 2023 год)', 'https://polyus.com/upload/iblock/7b9/polyus-go-2023-2307-dlya-sayta.pdf')
    add_src(p, 'Interfax (англ.)', 'https://interfax.com/newsroom/top-stories/103128/')

    # ---- Делимобиль
    dm = D['g796316fe']
    dh = new_profile(data, 'ООО «Делимобиль Холдинг»', 'Транспорт и логистика',
                     'Прямой владелец ПАО «Каршеринг Руссия» («Делимобиль»); его контролирует Винченцо Трани.',
                     'ООО «Делимобиль Холдинг»')
    put(dm, 'buyer', None, dh)
    replace_in(dm, 'eco.context',
               'После сделки косвенная доля Винченцо Трани в «Каршеринг Руссия» выросла с 53,25% до 66,15%.',
               'После сделки ООО «Делимобиль Холдинг», через которое компанией владеет Винченцо Трани, '
               'держит 90,99% «Каршеринг Руссия».')
    add_src(dm, 'Делимобиль (раскрытие для инвесторов)', 'https://invest.delimobil.ru/shareholder_info')
    add_src(dm, 'AK&M (англ.)', 'https://akm.ru/eng/news/delta-holding-withdrew-from-delimobil-s-capital/')
    tr = C['g33023870']
    assert tr['desc'] == ('Итальянский бизнесмен, конечный бенефициар «Делимобиля»; в 2026 году нарастил косвенную '
                          'долю с 53,25% до 66,15%.')
    tr['desc'] = ('Итальянский бизнесмен, конечный бенефициар «Делимобиля»; в 2026 году его ООО «Делимобиль '
                  'Холдинг» выкупило 12,9% компании у «Дельта Холдинга».')
    dl = C['g7f250a60']
    if 'структурам Винченцо Трани' in dl['desc']:
        dl['desc'] = dl['desc'].replace('структурам Винченцо Трани', 'ООО «Делимобиль Холдинг» Винченцо Трани')

    # ---- Whoosh / Юрент
    w = D['gdde6bef5']
    put(w, 'buyer', None, 'g83f5db27')
    put(w, 'target', 'g83f5db27', 'g30d7fdce')
    put(w, 'title', 'Слияние Whoosh и МТС Юрент (ЮрентБайк.ру)',
        'Whoosh не стал покупать «Юрент» у МТС после возражений ФАС')
    put(w, 'eco.share',
        'Обсуждалось безденежное слияние Whoosh и «Юрента» (ООО «ЮрентБайк.ру», 84,6% которого принадлежало МТС) '
        'путем обмена долями около паритета, без создания нового юрлица и с консолидацией активов внутри ПАО «ВУШ Холдинг».',
        '84,6% ООО «ЮрентБайк.ру» принадлежали МТС. По данным РБК, Whoosh и «Юрент» обсуждали обмен долями '
        'примерно поровну, без нового юрлица: активы собрали бы внутри ПАО «ВУШ Холдинг».')
    put(w, 'eco.val',
        'Рыночная капитализация каждого из объединяемых игроков (Whoosh и «Юрент») оценивалась примерно в 10–12 млрд ₽.',
        'По оценке инвестиционного директора УК «МЭФ Legal» Андрея Клименко (РБК), каждая из двух компаний '
        'стоила примерно 10–12 млрд ₽.')
    put(w, 'eco.rationale',
        'Логика объединения для акционеров «Юрента» (МТС) заключалась в получении ликвидности через долю в публичной '
        'компании ПАО «ВУШ Холдинг» вместо отдельного IPO.',
        'По данным РБК, МТС получила бы долю в публичной компании ПАО «ВУШ Холдинг» вместо отдельного IPO «Юрента».')
    put(w, 'law.struct',
        'Предполагалось безденежное слияние с обменом долями около паритета, без создания нового юридического лица и '
        'с консолидацией активов внутри ПАО «ВУШ Холдинг». Ходатайства были поданы в ФАС и отозваны ВУШ 10 февраля 2026 года.',
        'Whoosh подал в ФАС ходатайство о присоединении «Юрента» и отозвал его 10 февраля 2026 года. По данным РБК, '
        'обсуждался обмен долями без денег.')
    replace_in(w, 'extra', 'По неофициальным данным, стороны обсуждали', 'По данным РБК, стороны обсуждали')
    add_src(w, 'Финмаркет', 'https://www.finmarket.ru/news/6636074')
    add_src(w, 'New Retail (доля МТС)', 'https://new-retail.ru/novosti/retail/mts_dokupila_5_5_kiksheringa_mts_yurent/')

    # ---- Авито
    a = D['g420cae8d']
    replace_in(a, 'law.terms',
               'По условиям сделки Naspers настоял на условии lock-up, запрещающем перепродажу актива в течение 18–24 месяцев.',
               'По данным The Bell со ссылкой на два источника, два года после сделки «Авито» нельзя было передать '
               'третьим лицам; в релизе Naspers сказано лишь, что договор защищает интересы продавцов.')
    add_src(a, 'The Bell (англ.)', 'https://en.thebell.io/kremlin-backed-vk-fails-to-buy-russia-s-most-wanted-internet-company')

    # ---- Стокманн
    s = D['gd01de1ad']
    put(s, 'date', '2022-11-16', '2017')
    replace_in(s, 'extra', 'позже спор дошел до Верховного суда.',
               'кассация оставила постановление апелляции в силе, а в мае 2024 года Верховный суд окончательно '
               'подтвердил правоту «Стокманна».')
    replace_in(s, 'eco.val', 'в 12 раз дороже.',
               'в 12 раз дороже. Повторная экспертиза в апелляции оценила бизнес примерно в 48 млн ₽.')
    add_src(s, 'Коммерсантъ', 'https://www.kommersant.ru/doc/7400736')
    add_src(s, 'ЭПАМ (англ.)', 'https://epam.ru/en/news/view/komanda-ab-epam-uspeshno-zashitila-interesy-stokmann-v-spore-s-konkursnym-upravlyayushim-ipk-atlas')

    # ---- Артаг
    r = D['g71aec6a5']
    put(r, 'date', '2023-02-21', '2025-09-25')
    put(r, 'sum', '51,4 млн ₽', '5,1 млн ₽')
    put(r, 'eco.sum', '51,4 млн ₽', '5,1 млн ₽')
    put(r, 'sum_basis', 'auction_start', None)
    put(r, 'buyer_name', None, 'Павел Тимофеев')
    put(r, 'title', 'Росимущество продало госпакет 11,9% компании «Роснефть — Артаг»',
        'Росимущество продало госпакет 11,9% «Роснефть — Артаг» Павлу Тимофееву за 5,1 млн ₽')
    put(r, 'law.terms',
        'Лот — 11,9% уставного капитала, это 9 429 акций: 6448 привилегированных и 2981 обыкновенная. Начальная цена — '
        '51,437 млн ₽, шаг — 2,572 млн ₽. Заявки принимались до 6 марта, торги назначены на 17 марта 2023.',
        'Пакет продан по минимально допустимой цене по распоряжению Росимущества № 463-р от 11 марта 2025 года: '
        'начальная цена — 3,8 млн ₽, итог — 5,1 млн ₽. Лот — 11,9% уставного капитала, 9 429 акций: 6448 '
        'привилегированных и 2981 обыкновенная.')
    replace_in(r, 'eco.context',
               'В мае 2025 года пакет снова выставили на аукцион, уже с начальной ценой 38 млн ₽. По данным AK&M, '
               'в 2025 году его купил Павел Тимофеев за 3,8 млн ₽.',
               'В 2023 году начальная цена была 51,4 млн ₽. Аукцион 5 июня 2025 года с начальной ценой 38 млн ₽ '
               'пакет тоже не продал; 25 сентября 2025 года его продали по минимально допустимой цене Павлу '
               'Тимофееву за 5,1 млн ₽.')
    r.setdefault('retracted', {}).setdefault('sum', [])
    if '51,4 млн ₽' not in r['retracted']['sum']:
        r['retracted']['sum'].append('51,4 млн ₽')
    add_src(r, 'Росимущество (отчет о приватизации за 2025 год)',
            'https://rosim.gov.ru/app/uploads/2025/12/d16d1b_otchet-o-vypolnenii-prognoznogo-plana-privatizaczii-na-2025-2027-gg.-v-2025-godu.pdf')

    # ---- УГМК / Petropavlovsk
    u = D['g3cc2009d']
    adv = u['law']['adv']
    names = [row[1] for row in adv]
    assert names[:3] == ['Joseph Hage Aaronson LLP (JHA)', 'Peter Arden KC и Joseph Wigley (insolvency counsel)',
                         'Jim Sturman KC (sanctions counsel)'], names
    court = 'Решение Высокого суда Англии [2022] EWHC 2097 (Ch)'
    new_adv = [[row[0], row[1], court] for row in adv[:3]]
    put(u, 'law.adv', adv, new_adv)
    add_src(u, 'Высокий суд Англии, [2022] EWHC 2097 (Ch)', 'https://caselaw.nationalarchives.gov.uk/ewhc/ch/2022/2097')

    # ---- Qiwi / RealWeb
    q = D['gecc48c49']
    put(q, 'seller', 'Совладельцы Realweb — Эмин и Олеся Аветисян, Василий Лазука, Максим Виноградов, Иван Хмелевской, '
        'а также фонд iTech Capital',
        'Совладельцы Realweb, в том числе Василий Лазука, Максим Виноградов и Иван Хмелевской, вышедшие из бизнеса '
        'после сделки')
    add_src(q, 'O2Consulting (официальный сайт)', 'https://o2consult.com/en/news/m-a-deal-qiwi-acquires-advertising-agency-realweb/')
    add_src(q, 'Inc. Russia', 'https://incrussia.ru/news/qiwi-realweb/')
    rw = C['g1e2d10ab']
    old = ' у всех акционеров, включая фонд iTech Capital (25%),'
    if old in rw['desc']:
        rw['desc'] = rw['desc'].replace(old, '')

    # ---- Лента / OBI
    l = D['g02eed099']
    put(l, 'sum', '7,5–8,5 млрд ₽ (по оценке)', '3–6 млрд ₽ (по оценке)')
    put(l, 'eco.sum', '7,5–8,5 млрд ₽ (по оценке)', '3–6 млрд ₽ (по оценке)')
    replace_in(l, 'eco.val', 'Сергей Платицын из Союза торговых центров и CORE.XP — 3–5 млрд ₽',
               'Сергей Платицын из Союза торговых центров и Светлана Шорина из CORE.XP — 3–5 млрд ₽')

    # ---- Wintershall/OMV 2026 — только факты
    g = D['g3bb1fadb']
    put(g, 'date', '2026', '2026-04-16')
    put(g, 'eco.share',
        '«Согазу» — 50% «Севернефтегазпрома» и по 0,01% «Газпром ЮРГМ Трейдинг» и «Газпром ЮРГМ Девелопмент»; '
        '«Газовым технологиям» — 50% «Ачимгаза», 25% «Ачим Девелопмент» и 9% «Ачим сбыта».',
        '«Согазу» — 49,999% «Севернефтегазпрома» за 1,8 млрд ₽ и по 0,01% «Газпром ЮРГМ Трейдинг» за 3 млрд ₽ и '
        '«Газпром ЮРГМ Девелопмент» за 3,3 млрд ₽; «Газовым технологиям» — 50% «Ачимгаза» за 4,7 млрд ₽, 25,01% '
        '«Ачим Девелопмент» за 2,8 млрд ₽ и 9% «Ачим сбыта» за 100 млн ₽.')
    law_appr = g['law']['appr']
    tail = ' Распоряжения правительства — № 873-р и № 865-р от 16 апреля 2026 года.'
    if tail.strip() not in law_appr:
        put(g, 'law.appr', law_appr, law_appr + tail)
    add_src(g, 'Neftegaz.RU', 'https://neftegaz.ru/news/Acquisitions/922073-posle-2-let-podgotovki-pravitelstvo-rasporyadilos-prodat-doli-wintershall-dea-i-omv-v-byvshikh-sp-s-/')
    add_src(g, 'Интерфакс', 'https://www.interfax.ru/business/1084425')


def absorb(data):
    D = {d['id']: d for d in data['deals']}
    added = 0
    for cid, field in sorted(set(CHANGED)):
        recs = [f for f in review.FIXES if f['id'] == cid and f['field'] == field]
        if not recs:
            continue
        marks = D[cid].setdefault('proofread_absorbed', {}).setdefault(field, [])
        for f in recs:
            if f.get('new') is None:
                continue
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
                added += 1
    return added


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    data = json.loads(raw)
    apply(data)
    n = absorb(data)
    print('полей изменено: %d; отпечатков FIXES добавлено: %d' % (len(set(CHANGED)), n))
    for cid, field in sorted(set(CHANGED)):
        print('  %s.%s' % (cid, field))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(DATA, encoding='utf-8').read() == raw, 'база изменилась во время прогона — перезапустите'
    open(DATA, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
