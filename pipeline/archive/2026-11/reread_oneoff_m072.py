# -*- coding: utf-8 -*-
"""Разовые правки вычитки, марафон 12 ноября 2026, партия m072: то, что не ложится в FIXES.

Что: дата годом там, где дня события нет ни в одном источнике (review.py принимает только
ГГГГ-ММ-ДД), заметки accepted_notes (где искали), снятие/привязка сторон и прочее — по списку OPS.
Почему: см. докстроку pipeline/ingest/fixes/reread_2026_11_12_m072.py (поиск и причины по карточкам).
Каждая правка — assert на старое значение; уже примененная пропускается; правка факта — с
fact_edit_guard.log (цитата источника). Без ключа — сухой прогон, запись — по --write.

    python3 pipeline/archive/2026-11/reread_oneoff_m072.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка 12 ноября 2026, партия m072'
KEEP = object()

# (id, поле через точку, старое, новое, цитата или None, адрес)
OPS = [
    ('cdfe91cd0', 'date', '2022-08-09', '2022',
     '«Росатом» досрочно реализовал опцион на приобретение 19% в ГК «Дело». По результатам сделки основной акционер группы Сергей Шишкарев будет владеть 51% акций компании',
     'https://www.kommersant.ru/doc/5503749'),
    ('cd47c5acc', 'seller', 'Alshaya Group', 'Рино Инвестментс Лимитед',
     'ЕГРЮЛ, история участников ООО «Монэкс трейдинг» (ИНН 7710323601): 2022-11-22 вышла КОМПАНИЯ "РИНО ИНВЕСТМЕНТС ЛИМИТЕД" (100%), вошли АО "МФК ДЖАМИЛЬКО" (99,99%) и КОМПАНИЯ «ЛОСФОРД ТРЕЙДИНГ ЛТД» (0,01%)',
     'https://projectcompass.ru/api/companies/g21f05aad/fns'),
    ('cd47c5acc', 'seller_id', 'gbe4a66ce', None,
     'ЕГРЮЛ, история участников ООО «Монэкс трейдинг» (ИНН 7710323601): 2022-11-22 вышла КОМПАНИЯ "РИНО ИНВЕСТМЕНТС ЛИМИТЕД" (100%); Alshaya Group — группа, в которую входила компания («Монэкс трейдинг» входила в кувейтскую Alshaya Group, Сноб)',
     'https://projectcompass.ru/api/companies/g21f05aad/fns'),
    ('cd47c5acc', 'accepted_notes.no_profile.seller', None,
     'Продавец по ЕГРЮЛ — иностранная компания «Рино Инвестментс Лимитед» (вышла из участников 22.11.2022, 100%), холдинг Alshaya Group; российского ИНН у нее нет, профиль не заводится. Искали: ЕГРЮЛ (party_legal_names.py), New Retail, Retail.ru, Сноб, Sostav, Forbes (капча).',
     None, None),
    ('c1659a21f', 'date', '2022-07-31', '2022',
     'According to the other source, the deal is still in its final stages, and work on the new brand will begin after all formalities have been completed.',
     'https://interfax.com/newsroom/top-stories/82048/'),
    ('cc846f75c', 'status', None, 'Закрыта',
     'Теперь БКИ "Эквифакс" владеют Ибрагим Загидулин и Елизавета Чайка, сообщает РБК. Они разделили поровну 50%, которые раньше принадлежали Equifax Luxembourg. Смена собственников зарегистрирована в ЕГРЮЛ 5 августа.',
     'https://www.dp.ru/a/2022/08/08/Bjuro_kreditnih_istorij_Eq'),
    ('c65f082d8', 'date', '2022-08-11', '2025',
     'GREENWICH, Conn. – July 31, 2025 – Atlas Holdings ("Atlas") today announced the formation of the Orion Steel Companies following the completion of the previously announced acquisition of EVRAZ Inc. NA and EVRAZ Inc. NA Canada',
     'https://www.atlasholdingsllc.com/news/atlas-completes-acquisition-of-steelmaker-evraz-north-america-forms-orion-steel-and-appoints-doug-matthews-ceo/'),
    ('c65f082d8', 'eco.sum', 'Авансовый платеж $50 млн и отложенный платеж до $450 млн, выплачиваемый при достижении определенных показателей бизнесом после закрытия продажи.', 'До $500 млн',
     'Вознаграждение за продажу включает авансовый платеж в размере $50 млн и до $450 млн условного отложенного вознаграждения.',
     'https://finance.mail.ru/article/evraz-poluchil-licenziyu-ofsi-na-prodazhu-severoamerikanskogo-biznesa-66796307/'),
    ('cccedc36b', 'sum', '1,8 млрд ₽', 'Не раскрыта',
     'Сумма сделки и конкретные условия "слияния" компаний не сообщаются.',
     'https://www.ruscable.ru/news/2025/05/26/ETM_prisoedinyaet_biznes_AVS-Elektro_a_Russkij_Sve/'),
    ('cccedc36b', 'eco.sum', '1,8 млрд ₽', 'Не раскрыта',
     'Сумма сделки и конкретные условия "слияния" компаний не сообщаются.',
     'https://www.ruscable.ru/news/2025/05/26/ETM_prisoedinyaet_biznes_AVS-Elektro_a_Russkij_Sve/'),
    ('cccedc36b', 'retracted', None, {'sum': ['1,8 млрд ₽']}, None, None),
    ('c788bf9cc', 'date', '2023-08-10', '2023',
     'Договоренность о сделке так и не была достигнута, говорят собеседники и предполагают, что есть и другие претенденты на покупку актива.',
     'https://rb.ru/news/yango-israel-deal/'),
    ('cc846f75c', 'buyer_name', 'Ибрагим Загидулин и Елизавета Чайка', 'Ибрагим Загидулин и Виолетта Чайка',
     "ЕГРЮЛ, история участников ООО «БКИ «Эквифакс»» (ИНН 7813199667): 2022-08-04 вышла ЧАСТНАЯ КОМПАНИЯ С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ \"ЭКВИФАКС ЛЮКСЕМБУРГ (№3) С.А.Р.Л.\" (50%); 2022-08-05 вошли Загидулин Ибрагим Сабирович (25%) и Чайка Виолетта Владимировна (25%)", 'https://projectcompass.ru/api/companies/geed37a89/fns'),
    ('cc846f75c', 'title', 'Equifax выходит из состава участников БКИ «Эквифакс»', 'Ибрагим Загидулин и Виолетта Чайка купили 50% БКИ «Эквифакс»',
     "ЕГРЮЛ, история участников ООО «БКИ «Эквифакс»» (ИНН 7813199667): 2022-08-04 вышла ЧАСТНАЯ КОМПАНИЯ С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ \"ЭКВИФАКС ЛЮКСЕМБУРГ (№3) С.А.Р.Л.\" (50%); 2022-08-05 вошли Загидулин Ибрагим Сабирович (25%) и Чайка Виолетта Владимировна (25%)", 'https://projectcompass.ru/api/companies/geed37a89/fns'),
    ('cc846f75c', 'law.struct', 'БКИ «Эквифакс» перешло к Ибрагиму Загидулину и Елизавете Чайке: они поровну разделили 50%, которые раньше принадлежали Equifax Luxembourg.', 'Equifax Luxembourg вышла из БКИ «Эквифакс», а ее 50% поровну получили Ибрагим Загидулин и Виолетта Чайка. В статьях о сделке Чайку называют Елизаветой, в реестре участников она записана как Виолетта Владимировна.', None, None),
    ('c01524a40', 'date', '2026-02-25', '2026',
     'Объединенная команда юристов АБ ЕПАМ обеспечила комплексное юридическое сопровождение покупки производственной площадки в Московской области для ведущего российского производителя кондитерского рынка ОАО «Хлебпром».',
     'https://epam.ru/ru/news/view/komanda-ab-epam-obespechila-soprovozhdenie-sdelki-po-pokupke-proizvodstvennoj-ploshadki-dlya-oao-hlebprom'),
    ('c01524a40', 'accepted_notes.no_profile.seller', None,
     'Продавец не назван: сообщение АБ ЕПАМ (25.02.2026) продавца, адреса и цены не дает. Искали: поиск «Хлебпром купил производственную площадку» (RU), new-retail.ru (продажа VIRIDIAN завода FOODCODE «Хлебпрому» в январе 2024 года — связь с этой сделкой не подтверждена), декларация МЧС 2025 года (объект «Хлебпрома» в Волоколамске), 360.ru, retail.ru, сайт ЕПАМ.',
     None, None),
    ('c01524a40', 'asset', None, 'Производственная площадка в Московской области',
     'Объединенная команда юристов АБ ЕПАМ обеспечила комплексное юридическое сопровождение покупки производственной площадки в Московской области для ведущего российского производителя кондитерского рынка ОАО «Хлебпром».',
     'https://epam.ru/ru/news/view/komanda-ab-epam-obespechila-soprovozhdenie-sdelki-po-pokupke-proizvodstvennoj-ploshadki-dlya-oao-hlebprom'),
]
FACT_FIELDS = ('date', 'status', 'sum', 'eco.sum', 'title', 'buyer', 'buyer_name', 'seller', 'seller_id',
               'target', 'asset', 'asset_id', 'eco.share', 'law.adv', 'eco.finadv')


def get(card, path):
    cur = card
    for p in path.split('.'):
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


def put(card, path, value):
    parts = path.split('.')
    cur = card
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    if value is None:
        cur.pop(parts[-1], None)
    else:
        cur[parts[-1]] = value


def main(argv):
    write = '--write' in argv
    raw = open(DATA, encoding='utf-8').read()          # перечитываем прямо перед записью
    old_data = json.loads(raw)
    data = json.loads(raw)
    by = {d['id']: d for d in data['deals']}
    import fact_edit_guard
    changed = 0
    for cid, field, old, new, quote, url in OPS:
        card = by[cid]
        cur = get(card, field)
        if cur == new:
            print('уже применено: %s %s' % (cid, field))
            continue
        assert cur == old, '%s %s: ожидали %r, в базе %r' % (cid, field, old, cur)
        put(card, field, new)
        if quote and (field in FACT_FIELDS):
            fact_edit_guard.log(card, field, new, quote, url, BY)
        changed += 1
        print('ПРАВИМ %s %s: %r -> %r' % (cid, field, str(old)[:60], str(new)[:60]))
    if not write:
        print('Сухой прогон, правок: %d. Запись — с ключом --write.' % changed)
        return 0
    if changed:
        import mass_edit_guard
        mass_edit_guard.check(old_data, data, 'reread')
        json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано правок: %d' % changed)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
