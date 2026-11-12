# -*- coding: utf-8 -*-
"""Вычитка, марафон 12 ноября 2026, партия m030: правки, которые не ложатся в таблицу FIXES.

Что и почему:
  * gb70b4830 — описание профиля «Владимирского стандарта» называло выручку ГАП «Ресурс» «около 100 млрд ₽»
    (ни один источник этого не пишет) и пересказывало сделку: переписано родом занятий.
  * gefb52584 — продавец по истории участников ЕГРЮЛ ООО «Трансхим» (ИНН 7107136141): 08.08.2024 вышли
    ООО «Дезимпэкс» (50%) и АО «Новопесчанское» (50%); в схеме стоял продюсер Александр Достман —
    бенефициар «Дезимпэкса», а не участник. Дата: 100% у ООО «Оптима Инвест» — запись 21.08.2024
    («Ъ»: «в конце августа»), а не 1 августа. Цитата реестра — в fact_log.
  * ga3e353b1 — продавец снят таблицей правок (Кравцов сохранил 50%); где искали — в accepted_notes.
  * ge292671d — отрасль «Пищепром и напитки» → «Потребительские товары» (туалетная бумага, салфетки):
    отрасль — классификация по предмету, а не факт статьи (docs/card_parties.md, «Отрасль»).
  * g59fbdbf8 — продавцом стояла ЯТЭК (учредитель ЯГПК в 2017 году); по ЕГРЮЛ долю 09.07.2024 передало
    ООО «Глобал Метал Трейдинг», державшее ее с 28.06.2024 (до него — ООО «А-ТЭК»). EastRussia называет ЯТЭК —
    эта версия оставлена в контексте.
  * g941f2b2b — дата 9 июля 2024 без опоры (Интерфакс 11.07: «в июле завершило»): дня нет — дата годом
    (docs/card_status_dates.md); где искали продавца — в accepted_notes.
  * gfe151394 — продавец снят таблицей правок (по реестру Файзуленова вышла из общества в 2022 году) — почему, в
    accepted_notes; описание профиля ООО «Кэрифай» пересказывало сделку — переписано родом занятий.

Запуск: python3 pipeline/archive/2026-11/reread_oneoff_m030.py [--write]
Без ключа — сухой прогон. База перечитывается прямо перед записью; повторный запуск — «уже применено».
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка m030, 12.11.2026'
REG = 'https://projectcompass.ru/api/companies/%s/fns'


def card_edits(by, comps, log):
    c = by['gefb52584']
    if c.get('seller') != 'ООО «Дезимпэкс» и АО «Новопесчанское»':
        assert c.get('seller') == 'Александр Достман', c.get('seller')
        c['seller'] = 'ООО «Дезимпэкс» и АО «Новопесчанское»'
        c.setdefault('retracted', {}).setdefault('seller', []).append('Александр Достман')
        c.setdefault('party_evidence', {})['seller'] = {
            'url': REG % c['target'],
            'quote': 'ЕГРЮЛ, ООО «Трансхим» (ИНН 7107136141): 2024-08-08 вышли АО «Новопесчанское» (ИНН 3128085589, 50%) '
                     'и ООО «Дезимпэкс» (ИНН 9728003356, 50%); вошло ООО «Оптима Инвест» (ИНН 7705993897)'}
        fact_edit_guard.log(c, 'seller', c['seller'], c['party_evidence']['seller']['quote'], REG % c['target'], BY)
        log.append('gefb52584 seller')
    if c.get('date') != '2024-08-21':
        assert c.get('date') == '2024-08-01', c.get('date')
        c['date'] = '2024-08-21'
        fact_edit_guard.log(c, 'date', '2024-08-21',
                            'ЕГРЮЛ, ООО «Трансхим»: 2024-08-21 доля ООО «Оптима Инвест» 50% → 100%; «Ъ» 30.09.2024: '
                            '«ООО «Оптима Инвест» в конце августа получило 100% долей в ООО «Трансхим»»',
                            REG % c['target'], BY)
        log.append('gefb52584 date')

    c = by['ga3e353b1']
    np = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    if 'seller' not in np:
        np['seller'] = ('Продавец не назван: «Ъ» (25.12.2023) пишет, что гендиректор и владелец Алексей Кравцов сохранил '
                        '50%, а кто продал вторую половину — нет; искали: Коммерсантъ 6425675 и 6878096, CNews, '
                        'Mobile-review, Habr, реестр (АО «Крафтвэй Корпорэйшн ПЛС» — акционеров не раскрывает, '
                        'учредители Алексей Кравцов и Алексей Кудрявцев)')
        c['accepted_notes']['searched'] = ('Коммерсантъ 6425675 и 6878096, CNews (zoom.cnews.ru 649252), Mobile-review, '
                                           'поиск «Kraftway Росатом 50% Кравцов», реестр ФНС')
        log.append('ga3e353b1 accepted_notes')

    c = by['ge292671d']
    if c.get('ind') != 'Потребительские товары':
        assert c.get('ind') == 'Пищепром и напитки', c.get('ind')
        c['ind'] = 'Потребительские товары'
        log.append('ge292671d ind')

    c = by['gfe151394']
    np = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    if 'seller' not in np:
        np['seller'] = ('Продавец по реестру не установлен: RB.ru и АСН называют продавцом основательницу Анастасию '
                        'Файзуленову, но по истории участников ЕГРЮЛ ООО «Кэрифай» (ИНН 9715353018) она вышла из '
                        'общества 19.07.2022; на 16.07.2024 участником числилась Наталья Захарова (6,06%), остальная '
                        'доля принадлежала самому обществу. Искали: RB.ru, АСН, сайт LIFE.клиники, реестр ФНС, поиск '
                        '«Checkme Капитал Life продажа»')
        log.append('gfe151394 accepted_notes')
    p = comps.get('g97dbce60') or {}
    new = 'Сервис управления здоровьем Checkme: медицинские услуги через собственное приложение; основан в 2020 году Анастасией Файзуленовой.'
    if p and p.get('desc') != new:
        assert 'Капитал Life' in (p.get('desc') or ''), p.get('desc')
        p['desc'] = new
        log.append('g97dbce60 desc')

    c = by['g59fbdbf8']
    if c.get('seller') != 'ООО «Глобал Метал Трейдинг»':
        assert c.get('seller_id') == 'gf053d096', c.get('seller_id')
        c.setdefault('retracted', {}).setdefault('seller', []).append(c.get('seller'))
        c['seller'], c['seller_id'] = 'ООО «Глобал Метал Трейдинг»', None
        c.setdefault('party_evidence', {})['seller'] = {
            'url': REG % c['target'],
            'quote': 'ЕГРЮЛ, ООО «Якутский газоперерабатывающий комплекс» (ИНН 1435320551): 2024-06-28 100% перешли от '
                     'ООО «А-ТЭК» (ИНН 9703110701) к ООО «Глобал Метал Трейдинг» (ИНН 7707469343); 2024-07-09 — от '
                     'ООО «Глобал Метал Трейдинг» к ООО «Нордголд Развитие» (ИНН 7743387128)'}
        fact_edit_guard.log(c, 'seller', c['seller'], c['party_evidence']['seller']['quote'], REG % c['target'], BY)
        log.append('g59fbdbf8 seller')

    c = by['g941f2b2b']
    if c.get('date') != '2024':
        assert c.get('date') == '2024-07-09', c.get('date')
        c['date'] = '2024'
        fact_edit_guard.log(c, 'date', '2024',
                            'Интерфакс, 11.07.2024: «ООО "Логин Дело" … в июле завершило сделку по приобретению '
                            'контрольного пакета АО "Корсаковский морской торговый порт"» — дня закрытия нет ни в одном '
                            'источнике, АО: владельцы в ЕГРЮЛ не указаны', 'https://www.interfax.ru/russia/970352', BY)
        log.append('g941f2b2b date')
    np = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    if 'seller' not in np:
        np['seller'] = ('Продавец 64,26% акций не назван: Интерфакс 970352 и 971076, PortNews 365299, сайт Сергея '
                        'Шишкарева (shishkarev.ru), Интерфакс-англ. (interfax.com 104315 в выдаче), поиск «Корсаковский '
                        'морской торговый порт владелец акций до продажи» и «КМТП Корсаков акционер 2024»; АО — '
                        '«владельцы компании в ЕГРЮЛ не указаны» (Интерфакс)')
        log.append('g941f2b2b accepted_notes')

    p = comps['g5d742e72']
    new = 'Производитель колбас, сосисок и полуфабрикатов из Радужного Владимирской области; с 2024 года входит в ГАП «Ресурс».'
    if p.get('desc') != new:
        assert 'около 100 млрд' in (p.get('desc') or ''), p.get('desc')
        p['desc'] = new
        log.append('g5d742e72 desc')


def main(write):
    old = json.load(open(DATA, encoding='utf-8'))
    data = json.load(open(DATA, encoding='utf-8'))
    by = {c['id']: c for c in data['deals']}
    log = []
    card_edits(by, data['companies'], log)
    if not log:
        print('уже применено')
        return 0
    print('правки:', ', '.join(log))
    if not write:
        print('Сухой прогон. Запись — --write.')
        return 0
    mass_edit_guard.check(old, data)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
