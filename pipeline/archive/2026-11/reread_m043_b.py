# -*- coding: utf-8 -*-
"""Вычитка, марафон 12 ноября 2026, партия m043 (часть b): поля, которые таблица правок не берет.

g91b02f65 («Мать и дитя»/Мичуринский, 31): по пресс-релизу ГК MD Medical 17 июля 2023 года сделка
  закрыта, «общая сумма сделки составила 2 240 млн рублей» (2 840 млн — все вложения в проект с
  оборудованием). Было: 2024 год, сумма 2,8 млрд ₽, «недостроенное здание» в заголовке (купили
  готовый госпиталь). Продавец не найден — accepted_notes.
gc96f0c6b (ТПС/Columbus): продавец по ЕГРЮЛ ООО «МИРС» — Сергей Гордеев (вышел 07.06.2023), а не
  «структура ГК ПИК»; дата — день записи в реестре; описания профилей без неверного продавца и года.

Запуск: python3 pipeline/archive/2026-11/reread_m043_b.py [--write]
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


MDPR = 'https://www.mcclinics.ru/upload/iblock/b89/b898ab289e3e562f3b5f4a73cb7ac9ac.pdf'
VED_COL = 'https://www.vedomosti.ru/realty/news/2023/06/01/978111-tps-nedvizhimost-pokupaet-krupnii-torgovii-tsentr-columbus'
REG_MIRS = 'https://projectcompass.ru/api/companies/ge62941ed/fns'
RET23 = 'https://www.retail.ru/news/novym-vladeltsem-stolichnogo-tts-columbus-stanet-tps-nedvizhimost-28-marta-2023-227203'
RET20 = 'https://www.retail.ru/news/u-stolichnogo-tts-columbus-mozhet-smenitsya-vladelets-14-oktyabrya-2020-198638'


def set_desc(p, start, new):
    if p.get('desc') == new:
        return 0
    assert p['desc'].startswith(start), p['desc']
    p['desc'] = new
    return 1


def apply(data):
    deals = {d['id']: d for d in data['deals']}
    comp = data['companies']
    n = 0

    c = deals['g91b02f65']
    q_close = ('17 июля 2023 г. – Группа компаний «MD Medical» (ГК «MD Medical», «Группа» или «Компания»; МОЕХ: MDMG), '
               'один из лидеров на рынке частных медицинских услуг в России, объявляет о завершении сделки по покупке '
               'готового госпиталя в Москве.')
    n += setf(c, 'date', '2024', '2023-07-17', q_close, MDPR)
    if c.get('date_basis') != 'closing':
        c['date_basis'] = 'closing'
    if c.get('sum') != '2,24 млрд ₽':
        assert c['sum'] == '2 800 000 000 ₽' and c['eco']['sum'] == c['sum']
        c.setdefault('retracted', {}).setdefault('sum', []).append(c['sum'])
        c['sum'] = c['eco']['sum'] = '2,24 млрд ₽'
        for f in ('sum', 'eco.sum'):
            fact_edit_guard.log(c, f, '2,24 млрд ₽', 'Общая сумма сделки составила 2 240 млн рублей.', MDPR, BY)
        n += 1
    n += setf(c, 'title', 'ГК «Мать и дитя» приобрела недостроенное здание медицинского центра на Мичуринском проспекте',
              '«Мать и дитя» купила госпиталь на Мичуринском проспекте в Москве', q_close, MDPR)
    if MDPR not in [u for _l, u in c['src']]:
        c['src'].insert(0, ['ГК MD Medical (пресс-релиз)', MDPR])
        n += 1
    note = ('Продавец в пресс-релизе ГК MD Medical (17.07.2023) и его английской версии не назван; искали: '
            'пресс-релиз на mcclinics.ru, MarketScreener, Vademecum (в 2016 году здание числилось за ООО «Клиника-М» '
            'в банкротстве, в залоге у ЗАО «Гранд-Строй»), mamadeti.ru, веб-поиск по адресу и по «Клиника-М»/УМХЦ — '
            'кто продал госпиталь в 2023 году, не сообщалось')
    an = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    if an.get('seller') != note:
        an['seller'] = note
        n += 1
    n += set_desc(comp['g8d0573c5'], 'Недостроенное семиэтажное здание',
                  'Семиэтажный медицинский центр площадью 8 755 кв. м на Мичуринском проспекте, 31 в Москве; '
                  'с 2023 года — госпиталь MD Group «Мичуринский».')

    c = deals['gc96f0c6b']
    q_reg = '2023-06-07: вышел Гордеев Сергей Эдуардович 100.0%; вошло МКООО "ТПС РЕАЛ ЭСТЕЙТ ХОЛДИНГ ЛИМИТЕД" 100.0%'
    n += setf(c, 'seller', 'Структура ГК ПИК', 'Сергей Гордеев',
              'Собственником актива является основной акционер группы ПИК Сергей Гордеев .', VED_COL)
    n += setf(c, 'date', '2023', '2023-06-07', q_reg, REG_MIRS)
    if c.get('date_basis') != 'registry':
        c['date_basis'] = 'registry'
    n += setf(c, 'title', '«ТПС Недвижимость» купила торгово-развлекательный комплекс Columbus у структуры ГК ПИК',
              '«ТПС Недвижимость» купила ТРЦ Columbus у Сергея Гордеева',
              'Продавцом выступает владелец группы ПИК Сергей Гордеев.', RET23)
    n += add_src(c, 'Retail.ru', RET23)
    n += add_src(c, 'Retail.ru', RET20)
    n += set_desc(comp['g694c0790'], 'Структура холдинга ТПС Реал Эстейт',
                  'Владелец и управляющий торговых центров: «Хорошо!» и «Океания» в Москве, «Моремолл» и '
                  '«Галерея Краснодар» в Краснодаре.')
    n += set_desc(comp['ge62941ed'], 'Торгово-развлекательный комплекс, принадлежал',
                  'Торгово-развлекательный центр на Кировоградской улице на юге Москвы: 278 тыс. кв. м, открыт в 2015 году.')
    for cid, legal in (('g694c0790', 'АО «ТПС Недвижимость»'), ('ge62941ed', 'ООО «Мирс»')):
        if comp[cid].get('legal_short') != legal:
            assert not comp[cid].get('legal_short'), comp[cid].get('legal_short')
            comp[cid]['legal_short'] = legal
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
