# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m225 (первая часть): торги «Дом.РФ» и «Русгидро».

Чего не умеет review.py: снять чужой источник, дату по дню первого объявления (дня нет прописью
в цитате), сменить продавца-профиль на юрлицо текстом, переписать предмет описанием адреса,
снять неподтвержденную прозу, записать места поиска.

g5aabf462 (усадьба «Караул»): источники РИА от 6 и 23 октября 2026 года — о других лотах «Дом.РФ»
  (усадьба в Нижнем Тагиле, усадьба Михалковых в Рыбинске), сняты. Торги объявлены раньше статьи РИА:
  «ОнлайнТамбов» 22 сентября 2026 года («Фото: ГИС Торги», заявки — с 23 сентября).
gfbcdc000 (офис на Архитектора Власова): продает не ПАО «РусГидро», а входящая в группу компания
  «Сервиснедвижимость Русгидро» (РИА, BigpowerNews со ссылкой на «Ведомости»); ИНН ее не нашли.
  История здания (1964 год, покупка «ГидроОГК» в 2007 году) — ни в одной открытой статье, снята.
g49431b3c (особняк Штиглица): источники РИА от 7, 8 и 19 октября 2026 года — о других лотах
  (Челябинск, конюшни в Петергофе, Барнаул), сняты.
g29877b3a, ga24ad083: один источник; где еще искали — accepted_notes.searched.

    python3 pipeline/archive/2026-11/reread_auctions_m225.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_auctions_m225', '2026-11-12'
OT = 'https://www.onlinetambov.ru/news/eksklyuzivno/usadbu-chicherinykh-karaul-vystavili-na-torgi-za-2-5-mln-rubley/'
RIA_R = 'https://realty.ria.ru/20260930/rusgidro-2121149379.html'

DROP_SRC = {
    'g5aabf462': ['https://realty.ria.ru/20261006/tagil-2122504803.html',
                  'https://realty.ria.ru/20261023/rybinsk-2126479489.html'],
    'g49431b3c': ['https://realty.ria.ru/20261007/cheljabinsk-2122817369.html',
                  'https://realty.ria.ru/20261008/imperatorskiekonyushni-2123346365.html',
                  'https://realty.ria.ru/20261019/barnaul-2125338606.html'],
}
DATES = {
    'g5aabf462': ('2026-09-30', '2026-09-22',
                  '22.09.2026 09:25. Дом.РФ выставил на торги объект культурного наследия – Усадьбу «Караул»… '
                  'Заявки от участников будут приниматься с 23 сентября по 26 октября.', OT),
}
SELLER = ('gfbcdc000', '«Русгидро»', 'gd1eadb78', '«Сервиснедвижимость Русгидро»',
          'Входящая в "Русгидро" компания "Сервиснедвижимость Русгидро" выставила на продажу офис на юго-западе '
          'Москвы, сообщается на сайте Российского аукционного дома.',
          'Продавец — ООО «Сервиснедвижимость РусГидро», дочерняя компания ПАО «РусГидро» (РИА, BigpowerNews). '
          'ИНН не найден: WebSearch «Сервиснедвижимость РусГидро» ИНН, rusprofile, cbonds (список компаний группы), '
          'сайт РАД (объявление), статьи РИА, «Ведомостей», BigpowerNews — реквизитов нет (вычитка m225).')
ASSET = ('gfbcdc000', 'офис на юго-западе Москвы',
         'административное здание на улице Архитектора Власова, 51 в Москве (7,3 тыс. кв. м)',
         'Лот представляет собой административное здание по адресу: улица Архитектора Власова, 51. В ЕГРН оно '
         'оформлено как три отдельных помещения суммарной площадью 7,3 тысячи квадратных метров.')
STRUCT_OLD = ('Здание 1964 года постройки было куплено предшественником РусГидро — «ГидроОГК» (переименована в '
              'РусГидро в 2008 году) — под штаб-квартиру еще в 2007 году; служило штаб-квартирой вплоть до переезда '
              'группы в Красноярск в 2025 году.')
SEARCHED = {
    'g29877b3a': ['realty.ria.ru/20260925/korpus-2120231320.html', 'WebSearch: «Коновалова 2» корпус АГУ аукцион итоги',
                  'astrakhan.aif.ru (10.04.2026 — о другом здании АГУ, ул. Водников, 20А)',
                  'brief24.ru (апрель 2026 — о другом здании АГУ)', 'земля.дом.рф (архив торгов)',
                  'abnews.ru и РИА о других лотах «Дом.РФ» в Астрахани — других статей об этом лоте и итогов '
                  'аукциона 30 октября нет (вычитка m225, 13.11.2026)'],
    'ga24ad083': ['realty.ria.ru/20261001/beloretsk-2121471717.html',
                  'WebSearch: «Белорецк дом купца Недоспасова аукцион Пушкина 25»',
                  'WebSearch: «Недоспасов Белорецк особняк торги Дом.РФ 4,09 млн»',
                  'realty.rbc.ru (выдача поиска — только другие лоты «Дом.РФ»)',
                  'земля.дом.рф (архив торгов)',
                  'realty.yandex.ru (объявления Белорецка) — других статей об этом лоте и итогов аукциона '
                  '30 октября нет (вычитка m225, 13.11.2026)'],
}


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, urls in DROP_SRC.items():
        c = by[cid]
        keep = [s for s in c['src'] if s[1] not in urls]
        if len(keep) != len(c['src']):
            assert any(s[1].startswith('http') for s in keep)
            c['src'] = keep
            n += 1
    for cid, (old, new, quote, url) in DATES.items():
        c = by[cid]
        if c['date'] == new:
            continue
        assert c['date'] == old, (cid, c['date'])
        c['date'] = new
        for ev in c.get('events') or []:
            if ev.get('date') == old and ev.get('kind') == 'negotiations':
                ev['date'] = new
        fact_edit_guard.log(c, 'date', new, quote, url, BY, DAY)
        n += 1
    cid, old, old_id, new, quote, note = SELLER
    c = by[cid]
    if c.get('seller') != new:
        assert c.get('seller') == old and c.get('seller_id') == old_id, (c.get('seller'), c.get('seller_id'))
        c['seller'] = new
        c.pop('seller_id', None)
        c['seller_src'] = 'text'
        c.setdefault('retracted', {}).setdefault('seller', []).append(old)
        c.setdefault('accepted_notes', {}).setdefault('no_profile', {})['seller'] = note
        fact_edit_guard.log(c, 'seller', new, quote, RIA_R, BY, DAY)
        n += 1
    cid, old, new, quote = ASSET
    c = by[cid]
    if c.get('asset') != new:
        assert c.get('asset') == old, c.get('asset')
        c['asset'] = new
        fact_edit_guard.log(c, 'asset', new, quote, RIA_R, BY, DAY)
        n += 1
    c = by['gfbcdc000']
    if c['law'].get('struct') != '—':
        assert c['law'].get('struct') == STRUCT_OLD, c['law'].get('struct')
        c['law']['struct'] = '—'
        n += 1
    for cid, places in SEARCHED.items():
        c = by[cid]
        if (c.get('accepted_notes') or {}).get('searched') != places:
            c.setdefault('accepted_notes', {})['searched'] = places
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
    sys.exit(main('--write' in sys.argv[1:]))
