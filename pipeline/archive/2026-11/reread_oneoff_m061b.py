# -*- coding: utf-8 -*-
"""Вычитка, партия m061, часть b (марафон 12 ноября 2026): правки, которые review.py не принимает.

Проза, «≈», дата годом, тип «Продажа с торгов», профили. Каждая правка факта — с цитатой
(fact_edit_guard.log). Тексты статей сохранены save_source.save(..., day='2026-11-12_m061').

    python3 pipeline/archive/2026-11/reread_oneoff_m061b.py [--write]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
os.environ.pop('REVIEW_ONLY', None)   # нужны ВСЕ записи таблицы правок: их отпечатки уходят в proofread_absorbed
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402
import review  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DAY, BY = '2026-11-12', 'reread_oneoff_m061b'
FIXES = review.load_fixes()

DN = 'https://datanewton.ru/contragents/%s/history/timeline'


def absorb(card, field, new):
    """Прежние записи таблицы правок на это поле признаются примененными (docs/card_editing.md)."""
    marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
    for r in FIXES:
        if r.get('id') == card['id'] and r.get('field') == field and r.get('new') is not None and r['new'] != new:
            fp = review.fix_fingerprint(r['new'])
            if fp not in marks:
                marks.append(fp)
    if not marks:
        card['proofread_absorbed'].pop(field)
    if not card['proofread_absorbed']:
        card.pop('proofread_absorbed')


def put(card, field, old, new, quote=None, url=None):
    """Поле: assert на старое (точно или началом — «старт:...»), запись, отпечатки, цитата факта."""
    cur = fact_edit_guard.get(card, field)
    if cur == new:
        return
    if isinstance(old, str) and old.startswith('старт:'):
        assert isinstance(cur, str) and cur.startswith(old[6:]), (card['id'], field, cur)
    else:
        assert cur == old, (card['id'], field, cur)
    if '.' in field:
        head, tail = field.split('.', 1)
        card.setdefault(head, {})[tail] = new
    elif new is None:
        card.pop(field, None)
    else:
        card[field] = new
    absorb(card, field, new)
    if field in fact_edit_guard.FACT_FIELDS:
        assert quote and url, (card['id'], field)
        fact_edit_guard.log(card, field, new, quote, url, BY, DAY)


def drop_src(card, url):
    before = len(card['src'])
    card['src'] = [s for s in card['src'] if s[1] != url]
    if len(card['src']) != before:
        marks = card.setdefault('proofread_absorbed', {}).setdefault('src', [])
        fp = review.fix_fingerprint(url)
        if any(r.get('id') == card['id'] and r.get('field') == 'src' and r['new'][1] == url for r in FIXES) \
                and fp not in marks:
            marks.append(fp)
        if not marks:
            card['proofread_absorbed'].pop('src')
        if not card['proofread_absorbed']:
            card.pop('proofread_absorbed')


def add_src(card, label, url, first=False):
    if any(s[1] == url for s in card['src']):
        return
    if first:
        card['src'].insert(0, [label, url])
    else:
        card['src'].append([label, url])


def note(card, role, text):
    card.setdefault('accepted_notes', {}).setdefault('no_profile', {})[role] = text


def retract(card, field, value):
    lst = card.setdefault('retracted', {}).setdefault(field, [])
    if value not in lst:
        lst.append(value)


def legal(comps, cid, short):
    if comps[cid].get('legal_short') != short:
        comps[cid]['legal_short'] = short




# ---------------------------------------------------------------------------------------------

KOM_MCST = 'https://www.kommersant.ru/doc/5813229'
HABR = 'https://habr.com/ru/news/846946/'
WWW1 = ('https://www1.ru/news/2026/02/12/u-razrabotcika-processorov-elbrus-smenilsia-gendirektor-posle-sluxov-o-'
        'sryve-srokov-gosoboronzakaza.html')


def mcst(card, comps):
    q = ('в начале 2023 года покупкой «МЦСТ» интересовалось НПО «Критические информационные системы» (структура '
         '«Росатома»), но сделка так и не состоялась')
    put(card, 'title', 'Росатом вел переговоры о покупке АО МЦСТ (разработчик процессоров Эльбрус), но стороны не '
        'договорились', 'Покупка МЦСТ структурой Росатома не состоялась', q, HABR)
    qs = 'НПО «Критические информационные системы» (НПО КИС, структура «Росатома») приобретает 100% акций АО МЦСТ'
    put(card, 'eco.share', '—', '100% акций АО «МЦСТ»', qs, KOM_MCST)
    t = comps['g8880b809']
    if not t.get('legal_short'):
        t['legal_short'] = 'АО «МЦСТ»'
    put(card, 'eco.target_fin', 'старт:Свежие финансовые',
        'МЦСТ не раскрывает отчетность с 2018 года: тогда выручка составила 2,08 млрд ₽, чистая прибыль — 40 млн ₽.')
    put(card, 'law.struct', 'Госкорпорация учредила НПО КИС в октябре 2022 года.',
        'По данным источника на рынке микроэлектроники, НПО КИС, созданное «Росатомом» в октябре 2022 года, '
        'получало 100% акций АО «МЦСТ», и сделка была безденежной.')
    put(card, 'eco.context', 'старт:НПО «Критические',
        'МЦСТ разрабатывает процессоры «Эльбрус» и с сентября 2022 года находится под санкциями США. Состав '
        'акционеров компания не раскрывает; по неофициальным данным, контрольный пакет принадлежит основателю '
        'Александру Киму, в декабре 2021 года он это подтверждал.\n\n'
        'Переговоры о покупке, по неофициальным данным, шли с лета 2021 года: владельцы просили слишком высокую цену, '
        'а после предпродажного аудита представители «Росатома» были готовы управлять компанией, но не платить. '
        'Человек, близкий к акционерам МЦСТ, интерес «Росатома» отрицал; в «Росатоме» от комментариев '
        'отказались. Сделка в итоге не состоялась.\n\n'
        'В сентябре 2024 года Минпромторг ввел на МЦСТ внешнее управление, управляющей организацией стал НПЦ '
        '«Элвис»; собственность при этом не переходит. К концу 2025 года внешнее управление сняли для последующей '
        'продажи компании, а с 23 января 2026 года МЦСТ руководит Андрей Пименов из «Элвиса» вместо Александра Кима.')
    put(card, 'extra', 'старт:Покупатель, НПО КИС',
        'Интерес «Росатома» к МЦСТ стал известен еще в конце 2021 года; НПО КИС тогда же присматривалось и к другим '
        'активам в электронике, в том числе к Kraftway.')
    note(card, 'seller', 'Продавец не назван: акционеры АО «МЦСТ» не раскрыты, источники («Коммерсантъ», Habr, '
         'www1.ru) лишь по неофициальным данным называют владельцем контрольного пакета Александра Кима; сделка не '
         'состоялась, поэтому продавца по реестру нет.')
    add_src(card, 'Habr', HABR)


KOM_RM = 'https://www.kommersant.ru/doc/5783313'
KOM_BV = 'https://www.kommersant.ru/doc/7313000'


def rusmoloko(card, comps):
    q = ('ООО «Дебаркадер» экс-губернатора Тверской области Дмитрия Зеленина 16–20 января стало победителем торгов '
         'по продаже долей в нескольких структурах агрохолдинга «Русское молоко», следует из реестра сведений о '
         'банкротстве. На торги выставлялись доли ЗАО «Вашъ финансовый попечитель»')
    card['type'] = 'Продажа с торгов'
    put(card, 'title', 'Дмитрий Зеленин приобрел доли в агрохолдинге «Русское молоко»',
        '«Дебаркадер» купил на торгах доли в компаниях агрохолдинга «Русское молоко»', q, KOM_RM)
    qp = ('По итогам торгов «Дебаркадер» может получить по более 19% в АО «Рузское молоко» и АО «АПК "Космодемьянский"», '
          'около 3% АО «Раисино», около 17% ОАО «Тучковский» и почти 48% ООО «Прогресс» примерно за 34 млн руб.')
    put(card, 'sum', 'Не раскрыта', '≈34 млн ₽', qp, KOM_RM)
    put(card, 'eco.sum', 'Не раскрыта', '≈34 млн ₽', qp, KOM_RM)
    put(card, 'eco.share', 'старт:Если торги пройдут',
        'Почти 48% ООО «Прогресс», более 19% АО «Рузское молоко» и АО «АПК «Космодемьянский»», около 17% ОАО '
        '«Тучковский» и около 3% АО «Раисино»', qp, KOM_RM)
    put(card, 'seller', 'старт:ЗАО «Вашъ финансовый попечитель» (', 'Вашъ финансовый попечитель', q, KOM_RM)
    s = comps['gf7be561f']
    if not s.get('legal_short'):
        s['legal_short'] = 'ОАО «Вашъ финансовый попечитель»'
    put(card, 'eco.target_fin', 'старт:В 2021 АО',
        'АО «Рузское молоко», которое управляет молочным заводом холдинга, за 2021 год получило выручку 553,64 млн ₽ '
        'и чистый убыток 92,85 млн ₽.')
    put(card, 'eco.rationale', 'старт:Торги по долям',
        'По неофициальным данным, земли «Русского молока» лежат недалеко от границ Тверской области и могли '
        'заинтересовать Дмитрия Зеленина для расширения его аграрного бизнеса.')
    put(card, 'law.struct', '—',
        'Доли ЗАО «Вашъ финансовый попечитель», признанного банкротом в 2021 году, продавались на торгах в деле о '
        'банкротстве 16–20 января 2023 года; второй участник торгов — ООО «Формула бизнеса». В агрохолдинге считают, '
        'что о переходе долей говорить рано: у совладельцев «Прогресса» есть преимущественное право выкупа, а на '
        'сделки наложены ограничения приставами.')
    put(card, 'eco.context', 'старт:Против Василия',
        '«Русское молоко» Василия Бойко-Великого управляет в Подмосковье 23,5 тыс. га сельхозземель, фермами на '
        '4 тыс. голов и молочным заводом мощностью 50 тонн продукции в сутки. Дмитрий Зеленин возглавляет '
        'Ассоциацию менеджеров России и совладеет тверским производителем овощей «Саначино Агро».\n\n'
        'Против Бойко-Великого возбудили уголовное дело о хищении средств банка «Кредит-экспресс», акционером '
        'которого он был; в январе 2023 года Арбитражный суд Москвы признал его банкротом. Позже его приговорили '
        'к 6,5 года колонии за растрату, в ноябре 2024 года он обжаловал приговор в Верховном суде.')
    put(card, 'extra', 'старт:Структура бывшего',
        'Юристы допускают, что смена совладельцев приведет к корпоративному конфликту, а Илья Жарский из Veta '
        'считает, что купленные пакеты позволят влиять на ключевые решения, но контроля над холдингом не дадут.')
    retract(card, 'seller', 'ЗАО «Вашъ финансовый попечитель» (признано банкротом в 2021 году; связано с основателем '
            '«Русского молока» Василием Бойко-Великим)')


KOM_SMP = 'https://www.kommersant.ru/doc/5757183'
KOM_SMP2 = 'https://www.kommersant.ru/doc/5757280'
KOM_SMP3 = 'https://www.kommersant.ru/doc/6252083'
KOM_MOB = 'https://www.kommersant.ru/doc/7419918'


def smp(card, comps):
    q = ('ПСБ сообщил, что получил контроль над СМП-банком, выкупив акции у Аркадия и Бориса Ротенбергов. … В '
         'периметр сделки вошли СМП-банк и его дочерние структуры, включая находящийся в процессе финансового '
         'оздоровления Мособлбанк, «СМП-Страхование», «СМП Факторинг» и «Тяжпромлизинг».')
    put(card, 'title', 'ПСБ приобрел СМП-банк и его дочерние структуры',
        'ПСБ купил СМП-банк у Аркадия и Бориса Ротенбергов', q, KOM_SMP2)
    put(card, 'eco.share', 'старт:Группа СМП-банка',
        'Контрольный пакет акций АО «СМП Банк» с дочерними АО «Мособлбанк», ООО «СМП-Страхование», «СМП Факторинг» '
        'и «Тяжпромлизинг»', q, KOM_SMP2)
    put(card, 'eco.rationale', 'старт:Сам ПСБ объяснял',
        'ПСБ объяснил покупку своей стратегией: банк хочет масштабировать универсальную модель, получить новых '
        'клиентов и регионы, а клиентам предложить страховые услуги.')
    put(card, 'eco.context', 'старт:Продавцами акций',
        'Продавцами были Аркадий и Борис Ротенберги: по последним открытым данным за 2018 год, им принадлежало '
        '49,995% и 43,2% акций банка. Сменили ли владельцев доли миноритариев, неизвестно.\n\n'
        'ПСБ планировал присоединить СМП-банк к 1 января 2024 года, и позже банк вошел в ПСБ. Мособлбанк, который '
        'СМП-банк санировал с 2014 года, остался отдельным банком: в декабре 2024 года Банк России решил, что ПСБ '
        'выйдет из его оздоровления, а санацию продолжит АСВ.')
    put(card, 'extra', 'старт:ПСБ официально подтвердил',
        'По данным источников, ПСБ заплатил за группу сумму, близкую к ее капиталу: в 2022 году ни один банк, '
        'сменивший владельца, не был продан так дорого, и эксперты называют сделку нерыночной.')


VC = 'https://vc.ru/services/552174-avito-rabota-kupila-kontrolnyy-paket-v-kazahstanskom-servise-chat-botov-hr-messenger'
KOM_AV = 'https://www.kommersant.ru/doc/5695608'
BIRCH = 'https://t.me/s/BIRCHLEGAL/339'


def hrm(card, comps):
    qd = 'Сделка была закрыта в начале декабря 2022 года.'
    put(card, 'date', '2023', '2022', qd, BIRCH)
    q = 'Доля Авито в компании составит 62,75%. Сделка осуществлена через холдинговую структуру группы Авито — ООО «Авито Холдинг».'
    put(card, 'eco.share', 'старт:Доля Авито', '62,75% HR Messenger', q, KOM_AV)
    put(card, 'eco.rationale', 'старт:HR Messenger автоматизирует',
        '«Авито Работа» объясняет покупку стратегией автоматизации найма: сервис добавляет ей технологии чат-ботов, '
        'которые общаются с кандидатами в популярных мессенджерах.')
    put(card, 'eco.context', 'старт:С запуска в 2018',
        'HR Messenger — сервис из Казахстана: его чат-боты в мессенджерах тестируют кандидатов и '
        'назначают собеседования, а работодатель подключается к общению только на последнем этапе. По данным '
        'компании, в 2022 году через него откликнулись и прошли отбор более 4 млн соискателей в России.\n\n'
        'С запуска в 2018 году сервис, по данным Crunchbase, привлек $1,7 млн без учета последних вложений; '
        '$1,2 млн из них в 2021 году вложил «Авито», размер полученной тогда доли не раскрывали.')
    put(card, 'extra', 'старт:Куплен контрольный пакет',
        'Команда HR Messenger сохранит операционную независимость, компанию по-прежнему возглавит основатель '
        'Руслан Абдулганиев.')
    note(card, 'seller', 'Кто продал долю, источники не называют: «Коммерсантъ» (сообщение «Авито»), vc.ru и '
         'Telegram-канал Birch Legal пишут только о доле «Авито» после сделки (62,75%); HR Messenger — казахстанская '
         'компания, в ЕГРЮЛ ее нет, казахстанский реестр участников ТОО открыто долей не показывает.')
    add_src(card, 'BIRCH LEGAL (Telegram)', 'https://t.me/BIRCHLEGAL/339')

PLAN = {
    'ge6f87428': mcst,
    'gbfe2ee65': rusmoloko,
    'g2bb8cf3a': smp,
    'gbac532cf': hrm,
}


def apply(data):
    by = {d['id']: d for d in data['deals']}
    for cid, fn in PLAN.items():
        card = by[cid]
        if any(e.get('by') == BY for e in card.get('fact_log') or []):
            continue          # уже применено: повторный запуск ничего не меняет
        fn(card, data['companies'])


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    apply(data)
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    by = {d['id']: d for d in data['deals']}
    for cid in PLAN:
        print(cid, by[cid]['title'], by[cid]['date'], by[cid].get('sum'))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
