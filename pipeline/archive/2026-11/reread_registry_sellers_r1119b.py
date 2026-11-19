# -*- coding: utf-8 -*-
"""Вычитка 19 ноября 2026, партия r1119b: продавцы и даты по истории участников ЕГРЮЛ, вилка оценки,
первоисточник, точность прозы.

Чего не умеет review.py: дата по реестру (дня нет в статье прописью), продавец из истории участников,
смена стороны текстом на профиль, перестановка источников, правка прозы по реестру.

Доказательства (история участников — datanewton.ru/api/v2/history?ogrn=<ОГРН>&attributes=OWNERS):
gf475c186 («Ланта», ОГРН 1036891210146): 2025-10-20 Васильев (49%) и Зайцев (51%) вышли, Российская
  Федерация — 100%; дата — день записи. «Ъ» 8513184: «в доход государства были обращены и другие
  активы на 2,4 млрд руб.» — 2,4 млрд это прочие активы, а не «доля вместе с имуществом на сумму более»;
  «Ъ» 8039562: «Парк-Отель “Берендей”»… «осуществило легализацию 291,6 млн руб.» — легализация, не вывод.
g7ccf80f9 (ООО «Интернест-Холдинг», ОГРН 1079847126743): 2024-12-17 вышли Антон Воскресенский (32%),
  Никита Невенчанный (32%), ООО «Компания ВК» (20%), Роман Филиппов (16%); вошли ООО «КЕХ Екоммерц»
  (99,9%) и ООО «Авито Холдинг». Оценка Бурмистрова — «в диапазоне 2−2,5 млрд руб.»
  (Sostav), вилка остается вилкой (docs/card_money.md, 18 ноября 2026); ADPASS и Oborot — «от 500 млн
  до 2,5 млрд». Sostav пересказывает РБК («сообщает РБК», статья РБК закрыта, 401), Интерфакс — первая
  рука (сообщение «Авито» и ЕГРЮЛ) — первым в src.
gca6c1eff (ООО «Квадро Холдинг», ОГРН 1164704061390): 2024-09-19 Юрий Савичев (13%) вышел, 2024-09-27
  МКООО «Кьютиай Партнерс Лтд» (87%) вышла, ООО «Юнитайл Холдинг» — 100%. Proxima Capital Group в реестре
  не стоит: она контролировала бизнес («Ъ» 7181682) — остается в eco.context (docs/card_parties.md,
  «Покупатель и продавец в схеме — те, кто в реестре», 11 ноября 2026). Дата — 27 сентября (100%).
ge292671d: eco.share был «—»; ЕГРЮЛ (ОГРН 1065018027106) 2024-07-16: Лукин (100%) вышел.
gc3452fa6: extra называл газету «Ъ» (пресс-язык) — фраза об отказе отвечать снята.
gca6c1eff: eco.target_fin повторял фразу «Ъ» (8+ слов) — пересказ.
ge292671d, g1ce3ddfc: день карточки — день записи в ЕГРЮЛ (2024-07-16, 2024-06-05) — date_basis registry.
g64141daa (ООО «Клиентский сервис», ОГРН 1177746429410): 2025-05-06 вышли ООО «Самолет-Резерв» (75,68%),
  Дарья Воронова (14,05%), Кирилл Воронов (10,27%); Интерфакс 1025082 называет тех же.
g1ce3ddfc (ОГРН 1235400034451): продавец 1% по ЕГРЮЛ — ООО «Минеральные воды Боржоми».
gc9a9d929: «Ъ» 7432236 пересказывает «Ведомости» («сообщил „Ведомостям“ представитель компании») —
  статья «Ведомостей» 15.01.2025 открыта и ставится первой.

    python3 pipeline/archive/2026-11/reread_registry_sellers_r1119b.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402
from review import fix_fingerprint  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_registry_sellers_r1119b', '2026-11-19'
DN = 'https://datanewton.ru/api/v2/history?ogrn=%s&startDate=2000-01-01&attributes=OWNERS'

LANTA_STRUCT_OLD = ('Октябрьский районный суд Тамбова удовлетворил иск Генпрокуратуры и обратил в доход государства '
                    '100% долей ООО «Ланта» вместе с имуществом на сумму более 2,4 млрд ₽. Продажу доли организует '
                    'ПАО «Банк ПСБ» от имени государства: прием заявок с 16 по 23 марта 2026 года, торги 24 марта '
                    'на площадке «Фабрикант».')
LANTA_STRUCT_NEW = ('Октябрьский районный суд Тамбова удовлетворил иск Генпрокуратуры и обратил в доход государства '
                    '100% долей ООО «Ланта»; кроме них, государству перешли другие активы ответчиков на 2,4 млрд ₽. '
                    'Продажу доли организует ПАО «Банк ПСБ» от имени государства: прием заявок с 16 по 23 марта '
                    '2026 года, торги 24 марта на площадке «Фабрикант».')
LANTA_CTX_OLD = 'и через «Берендей» вывели около 292 млн ₽'
LANTA_CTX_NEW = 'и через парк-отель «Берендей» легализовали около 292 млн ₽'

INTERNEST_SELLER = 'Антон Воскресенский, Никита Невенчанный, ООО «Компания ВК» и Роман Филиппов'
INTERNEST_STRUCT = ('По ЕГРЮЛ, 17 декабря 2024 года из ООО «Интернест-Холдинг» вышли все прежние участники: '
                    'Антон Воскресенский и Никита Невенчанный (по 32%), ООО «Компания ВК» (20%) и Роман Филиппов '
                    '(16%). 99,9% получило ООО «КЕХ Екоммерц», остальное — ООО «Авито Холдинг».')
INTERNEST_Q = ('ЕГРЮЛ, ООО «Интернест-Холдинг» (ОГРН 1079847126743), 2024-12-17: Воскресенский Антон '
               'Владимирович 32.0%, Филиппов Роман Александрович 16.0%, Невенчанный Никита Львович 32.0%, '
               'ООО «Компания ВК» 20.0% -> вышли; ООО «КЕХ Екоммерц» 99.9%')
INTERNEST_VAL_OLD = 'Глава «INFOLine Аналитики» Михаил Бурмистров оценивает сделку в 2–2,5 млрд ₽.'
INTERNEST_VAL_NEW = ('Глава «INFOLine Аналитики» Михаил Бурмистров оценивает сделку в 2–2,5 млрд ₽; по другим '
                     'экспертным оценкам — от 500 млн до 2,5 млрд ₽.')

QUADRO_SELLER = 'МКООО «Кьютиай Партнерс Лтд» и Юрий Савичев'
QUADRO_Q = ('ЕГРЮЛ, ООО «Квадро Холдинг» (ОГРН 1164704061390): 2024-09-19 Савичев Юрий Александрович 13.0% -> '
            'вышел, ООО «Юнитайл Холдинг» 13.0%; 2024-09-27 МКООО «Кьютиай Партнерс Лтд» 87.0% -> вышла, '
            'ООО «Юнитайл Холдинг» 100.0%')
QUADRO_STRUCT_OLD = ('По данным СПАРК, формально передано пока 13% компании — в «Юнитайле» это объяснили '
                     'техническими этапами сделки.')
QUADRO_STRUCT_NEW = (QUADRO_STRUCT_OLD + ' По ЕГРЮЛ, 13% ООО «Квадро Холдинг» перешли от Юрия Савичева '
                     '19 сентября 2024 года, остальные 87% — от МКООО «Кьютиай Партнерс Лтд» 27 сентября; с этого '
                     'дня ООО «Юнитайл Холдинг» владеет 100%.')

DOMI_STRUCT_OLD = 'До этого 75,68% принадлежали ООО «Самолет-Резерв».'
DOMI_STRUCT_NEW = ('До этого 75,68% принадлежали ООО «Самолет-Резерв», 14,05% — гендиректору платформы Дарье '
                   'Вороновой, 10,27% — Кириллу Воронову.')
DOMI_SELLER = '«Самолет», Дарья Воронова и Кирилл Воронов'
DOMI_Q = ('ЕГРЮЛ, ООО «Клиентский сервис» (ОГРН 1177746429410), 2025-05-06: Воронова Дарья Александровна '
          '14.0514%, Воронов Кирилл Владимирович 10.2683%, ООО «Самолет-Резерв» 75.6803% -> вышли; '
          'ООО «Технояк» 99.99%. Интерфакс: «до 6 мая ООО "Самолет-Резерв" владело 75,68%… Еще 14,05% '
          'принадлежало гендирктору "Платформы Домиленд" Дарье Вороновой, 10,26% - Кириллу Воронову»')

DDX_EXTRA_OLD = ' Банк, управляющая компания и сеть на вопросы «Ъ» не ответили.'
DDX_EXTRA_NEW = ''
DDX_EXTRA_FULL_OLD = ('АО «ААА Управление капиталом», которое через ООО «ГПБ-проект» и ООО «Финпроект» принадлежит '
                      'Газпромбанку, получило 11,1% ООО «Илон», управляющего сетью фитнес-клубов DDX Fitness.' + DDX_EXTRA_OLD)

QUADRO_FIN_OLD = ('По данным СПАРК, выручка ООО «Квадро Холдинг» в 2023 году составила 47,7 млн ₽, а у «Квадро Декора» '
                  'снизилась на 5% год к году, до 1,8 млрд ₽. Обе компании в 2023 году закончили год с убытком.')
QUADRO_FIN_NEW = ('По данным СПАРК, в 2023 году выручка «Квадро Декора» сократилась на 5%, до 1,8 млрд ₽, а у '
                  'ООО «Квадро Холдинг» составила 47,7 млн ₽. Обе компании закончили 2023 год с убытком.')
REGISTRY_DAY = {'ge292671d': '2024-07-16', 'g1ce3ddfc': '2024-06-05'}

CHECKED = {
    'gf475c186': 'История участников ЕГРЮЛ (datanewton, ОГРН 1036891210146): 20.10.2025 Александр Васильев (49%) '
                 'и Александр Зайцев (51%) вышли, 100% — Российская Федерация; изъятие, продажи доли нет.',
    'ga75a4d0a': 'История участников ЕГРЮЛ (datanewton, ОГРН 1207700193282): 20.06.2025 Роман и Шеке Фероян '
                 '(по 50%) вышли, ООО «812 Капитал» — 100%; продажа долей, продавцы — Ферояны.',
    'g7ccf80f9': 'История участников ЕГРЮЛ (datanewton, ОГРН 1079847126743): 17.12.2024 вышли Воскресенский и '
                 'Невенчанный (по 32%), ООО «Компания ВК» (20%), Филиппов (16%); вошли «КЕХ Екоммерц» (99,9%) и '
                 '«Авито Холдинг» — продажа долей.',
    'gca6c1eff': 'История участников ЕГРЮЛ (datanewton, ОГРН 1164704061390): 19.09.2024 Юрий Савичев (13%) вышел, '
                 '27.09.2024 МКООО «Кьютиай Партнерс Лтд» (87%) вышла, ООО «Юнитайл Холдинг» — 100%; продажа долей.',
    'ge292671d': 'История участников ЕГРЮЛ (datanewton, ОГРН 1065018027106): 16.07.2024 Эдуард Лукин (100%) вышел, '
                 'вошли Анна Васильева (80,5%) и Максим Волков (19,5%) — продажа доли.',
    'g1ce3ddfc': 'История участников ЕГРЮЛ (datanewton, ОГРН 1235400034451): 05.06.2024 ООО «Компания Чистая вода» '
                 '(99%) и ООО «Минеральные воды Боржоми» (1%) вышли, ТД «Усть-Каменский» — 100%; продажа долей.',
    'gc3452fa6': 'История участников ЕГРЮЛ (party_legal_names.py, ООО «Илон»): 31.01.2024 доли прежних участников '
                 'уменьшились на одну девятую, вошло АО «ААА Управление капиталом» — вход через капитал, продавца нет.',
    'g64141daa': 'История участников ЕГРЮЛ (datanewton, ОГРН 1177746429410): 06.05.2025 вышли ООО «Самолет-Резерв» '
                 '(75,68%), Дарья Воронова (14,05%), Кирилл Воронов (10,27%); вошли «Технояк» и «Яндекс.Доставка '
                 'Холдинг» — продажа долей.',
    'gad4a5636': 'История участников ЕГРЮЛ (datanewton, ОГРН 1153668017030): на ноябрь 2026 года «Ангстрема» среди '
                 'участников нет (Сергей Послухаев, ООО «Центральный дом мебели» и др.) — сделка не закрыта.',
}


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0

    c = by['gf475c186']
    if c['date'] != '2025-10-20':
        assert c['date'] == '2025', c['date']
        c['date'] = '2025-10-20'
        c['date_basis'] = 'registry'
        fact_edit_guard.log(c, 'date', '2025-10-20',
                            'ЕГРЮЛ, ООО «Ланта» (ОГРН 1036891210146), 2025-10-20: Васильев Александр Сергеевич 49.0% '
                            'и Зайцев Александр Викторович 51.0% -> вышли; Российская Федерация 100.0%',
                            DN % '1036891210146', BY, DAY)
        n += 1
    if c['law']['struct'] != LANTA_STRUCT_NEW:
        assert c['law']['struct'] == LANTA_STRUCT_OLD, c['law']['struct']
        c['law']['struct'] = LANTA_STRUCT_NEW
        n += 1
    if LANTA_CTX_OLD in c['eco']['context']:
        c['eco']['context'] = c['eco']['context'].replace(LANTA_CTX_OLD, LANTA_CTX_NEW)
        n += 1
    c['accepted_notes']['no_profile']['seller'] = (
        'Продавца нет: изъятие по суду. По истории участников ЕГРЮЛ (datanewton, ОГРН 1036891210146) до '
        '20.10.2025 долями владели Александр Зайцев (51%) и Александр Васильев (49%), с 20.10.2025 — '
        'Российская Федерация (100%).')

    c = by['g7ccf80f9']
    if c.get('seller') != INTERNEST_SELLER:
        assert c.get('seller') is None, c.get('seller')
        c['seller'] = INTERNEST_SELLER
        c['seller_src'] = 'registry'
        c['accepted_notes']['no_profile'].pop('seller', None)
        if not c['accepted_notes']['no_profile']:
            c['accepted_notes'].pop('no_profile')
        fact_edit_guard.log(c, 'seller', INTERNEST_SELLER, INTERNEST_Q, DN % '1079847126743', BY, DAY)
        n += 1
    if c['law']['struct'] != INTERNEST_STRUCT:
        assert c['law']['struct'] == '—', c['law']['struct']
        c['law']['struct'] = INTERNEST_STRUCT
        n += 1
    new_sum = '2–2,5 млрд ₽ (по оценке)'
    if c['sum'] != new_sum:
        assert c['sum'] == '2,5 млрд ₽ (по оценке)' and c['eco']['sum'] == '2,5 млрд ₽ (по оценке)', c['sum']
        c['sum'] = new_sum
        c['eco']['sum'] = new_sum
        q = ('Стоимость сделки официально не раскрывается. Глава «INFOLine Аналитики» Михаил Бурмистров '
             'оценивает ее в диапазоне 2−2,5 млрд руб.')
        url = 'https://www.sostav.ru/publication/avito-kupil-reklamnye-servisy-adriver-i-soloway-72080.html'
        fact_edit_guard.log(c, 'sum', new_sum, q, url, BY, DAY)
        fact_edit_guard.log(c, 'eco.sum', new_sum, q, url, BY, DAY)
        n += 1
    if c['eco']['val'] != INTERNEST_VAL_NEW:
        assert c['eco']['val'] == INTERNEST_VAL_OLD, c['eco']['val']
        c['eco']['val'] = INTERNEST_VAL_NEW
        n += 1
    if c['src'][0][1] != 'https://www.interfax.ru/business/998257':
        i = [s[1] for s in c['src']].index('https://www.interfax.ru/business/998257')
        c['src'].insert(0, c['src'].pop(i))
        n += 1

    c = by['gca6c1eff']
    if c.get('seller') != QUADRO_SELLER:
        assert c.get('seller') == 'Proxima Capital Group' and c.get('seller_id') == 'gdae3e3d7', c.get('seller')
        c['seller'] = QUADRO_SELLER
        c['seller_src'] = 'registry'
        del c['seller_id']
        c.setdefault('retracted', {}).setdefault('seller', []).append('Proxima Capital Group')
        fact_edit_guard.log(c, 'seller', QUADRO_SELLER, QUADRO_Q, DN % '1164704061390', BY, DAY)
        n += 1
    new_title = 'Unitile купил Quadro Decor'
    if c['title'] != new_title:
        assert c['title'] == 'Unitile купил Quadro Decor у Proxima Capital Group', c['title']
        c['title'] = new_title
        fact_edit_guard.log(c, 'title', new_title, 'Продавец по ЕГРЮЛ — не Proxima Capital Group: ' + QUADRO_Q,
                            DN % '1164704061390', BY, DAY)
        n += 1
    if c['date'] != '2024-09-27':
        assert c['date'] == '2024', c['date']
        c['date'] = '2024-09-27'
        c['date_basis'] = 'registry'
        fact_edit_guard.log(c, 'date', '2024-09-27', QUADRO_Q, DN % '1164704061390', BY, DAY)
        n += 1
    if c['eco']['target_fin'] != QUADRO_FIN_NEW:
        assert c['eco']['target_fin'] == QUADRO_FIN_OLD, c['eco']['target_fin']
        c['eco']['target_fin'] = QUADRO_FIN_NEW
        n += 1
    if c['law']['struct'] != QUADRO_STRUCT_NEW:
        assert c['law']['struct'] == QUADRO_STRUCT_OLD, c['law']['struct']
        c['law']['struct'] = QUADRO_STRUCT_NEW
        n += 1

    c = by['ge292671d']
    new_share = '100% доли в ООО «Тетра»'
    if c['eco']['share'] != new_share:
        assert c['eco']['share'] == '—', c['eco']['share']
        c['eco']['share'] = new_share
        fact_edit_guard.log(c, 'eco.share', new_share,
                            'До смены собственника единственным собственником ООО «Тетра» был Эдуард Лукин. ЕГРЮЛ '
                            '(ОГРН 1065018027106), 2024-07-16: Лукин Эдуард Игоревич 100.0% -> вышел; Васильева '
                            'Анна Викторовна 80.5%, Волков Максим Викторович 19.5%',
                            'https://www.kommersant.ru/doc/7214484', BY, DAY)
        n += 1

    c = by['gc3452fa6']
    if DDX_EXTRA_OLD in c['extra']:
        c['extra'] = c['extra'].replace(DDX_EXTRA_OLD, DDX_EXTRA_NEW)
        n += 1

    c = by['g64141daa']
    if c.get('seller') != DOMI_SELLER:
        assert c.get('seller') == 'Самолет' and c.get('seller_id') == 'g12111389', c.get('seller')
        c['seller'] = DOMI_SELLER
        fact_edit_guard.log(c, 'seller', DOMI_SELLER, DOMI_Q, DN % '1177746429410', BY, DAY)
        n += 1
    if DOMI_STRUCT_OLD in c['law']['struct']:
        c['law']['struct'] = c['law']['struct'].replace(DOMI_STRUCT_OLD, DOMI_STRUCT_NEW)
        n += 1

    c = by['g1ce3ddfc']
    new_seller = 'ООО «Компания Чистая вода» и ООО «Минеральные воды Боржоми»'
    if c.get('seller') != new_seller:
        assert c.get('seller') == 'ООО «Компания Чистая вода» и ООО «Минводы Боржоми»', c.get('seller')
        c['seller'] = new_seller
        fact_edit_guard.log(c, 'seller', new_seller,
                            'ЕГРЮЛ, ООО «Карачинская звезда» (ОГРН 1235400034451), 2024-06-05: ООО «Компания Чистая '
                            'вода» 99.0% и ООО «Минеральные воды Боржоми» (ОГРН 1107746833127) 1.0% -> вышли; ООО '
                            '«Торговый дом Усть-Каменский» 100.0%',
                            DN % '1235400034451', BY, DAY)
        n += 1

    c = by['gc9a9d929']
    ved = ['Ведомости', 'https://www.vedomosti.ru/business/articles/2025/01/15/'
                        '1086226-odin-iz-stareishih-alkogolnih-brendov-rossii-smenil-vladeltsa']
    if c['src'][0][1] != ved[1]:
        assert ved[1] not in [s[1] for s in c['src']]
        c['src'].insert(0, ved)
        n += 1

    # Записи таблицы правок до этой вычитки, чье значение здесь переписано по реестру: отпечаток —
    # в proofread_absorbed (review.already_applied), иначе тест таблицы правок видит их неприменными.
    for cid, field, value in (('gca6c1eff', 'seller', 'Proxima Capital Group'),
                              ('gca6c1eff', 'title', 'Unitile купил Quadro Decor у Proxima Capital Group'),
                              ('gc3452fa6', 'extra', DDX_EXTRA_FULL_OLD)):
        fp = fix_fingerprint(value)
        lst = by[cid].setdefault('proofread_absorbed', {}).setdefault(field, [])
        if fp not in lst:
            lst.append(fp)
            n += 1

    for cid, day in REGISTRY_DAY.items():
        c = by[cid]
        assert c['date'] == day, (cid, c['date'])
        if c.get('date_basis') != 'registry':
            c['date_basis'] = 'registry'
            n += 1

    for cid, why in CHECKED.items():
        notes = by[cid].setdefault('accepted_notes', {}).setdefault('checked', {})
        if notes.get('registry_owners') != why:
            notes['registry_owners'] = why
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
