# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m225 (вторая часть): тип, дата по реестру, сумма-оценка, итог торгов.

Чего не умеет review.py: тип и статус без слова-подтверждения в одной цитате, дата по ЕГРЮЛ,
сумма «Не раскрыта», год без дня, снятие источника 404, предмет и доля описанием, места поиска.

g812a7b3b (Arzamas Capital / NGR Softlab): по ЕГРЮЛ (ООО «Энджиар Софтлаб», ИНН 7730252130) 24 сентября
  2026 года вошло АО «Арзамас Капитал» с 26%, доля Сергея Шерстобитова — 90 → 66,6%, Дмитрия Пудова —
  10 → 7,4% (до сделки 90/10 — SecPost). Обе доли уменьшились ровно на 26% своей величины — так выглядит
  и увеличение капитала, и пропорциональная продажа; Пудов говорит о привлечении инвестора. 26% без
  контроля — «Инвестиция», продавца не пишем. «≈800 млн ₽» — оценка аналитика «Финама» Леонида
  Делицына (она остается в eco.val), не цена сделки.
g1e37f107 (Fonte / «Самолет»): Fonte Capital заявила, что 18 сентября 2026 года фонд продал весь пакет
  около 18% и вышел из капитала (National Business); карточка описывала только снижение до 5%.
  18% без контроля — «Инвестиция», как у покупки этого пакета в июле.
gf145d639 (корпус ледокола «Арктика»): единственная заявка — ООО «Авиавторресурс», торги признаны
  несостоявшимися, комиссия решила заключить с ним договор (Би-порт, протокол на ГИС «Торги»).
  День протокола ни в одной статье не назван — дата годом. NewsRoom24 отвечает 404.
gb3ae9e94 (ночлежный дом в Астрахани): первая статья — АБН 24, 1 октября 2026 года; в лот входит
  еще одно здание 560 кв. м (РИА), расхождения в площади нет.
g6600b6a4 (казармы в Павловске): в eco.val лежали задаток, шаг и состояние зданий — не оценка; снято
  (задаток и шаг — в law.terms, состояние — в контекст через write_card.py).
g45b335fe: один источник; где еще искали — accepted_notes.searched.

    python3 pipeline/archive/2026-11/reread_oneoff_m225b.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m225b', '2026-11-12'
SP = 'https://secpost.ru/arzamas-capital-usilivaet-ib-portfel-posle-microolap-investor-vlozhilsya-v-ngr-softlab'
NB = 'https://nationalbusiness.kz/news/kazahstanskiy-investor-vishel-iz-kapitala-popavshey-pod-sanktsii-rossiyskoy-kompanii-bb760a/'
BPORT = 'https://b-port.com/news/367211'
AB1 = 'https://abnews.ru/ug/news/astrakhan/2026/10/1/zdanie-astrahanskoj-nochlezhki-xix-veka-prodayut-vmeste-s-zemelnym-uchastkom'
RIA_A = 'https://realty.ria.ru/20261006/astrahan-2122692433.html'
EGRUL_NGR = ('ЕГРЮЛ, ООО «Энджиар Софтлаб» (ИНН 7730252130): 2026-09-24 joined АО «Арзамас Капитал» (None → 26.0); '
             '2026-09-24 Шерстобитов Сергей Петрович 90.0 → 66.6; 2026-09-24 Пудов Дмитрий Геннадьевич — 7.4')
Q_NGR = ('Российский ИБ-вендор NGR Softlab привлек стратегического инвестора: 26% компании получила Arzamas Capital, '
         'следует из данных «Контур.Фокуса».')
Q_FONTE = ('18 сентября 2026 года частная компания Fonte Inceptia Alpha Fund OEIC Limited завершила сделку по продаже '
           'принадлежащего ей пакета порядка 18% обыкновенных голосующих акций')
Q_ARKT = ('Сам аукцион признали несостоявшимся из-за участия только одного претендента. При этом комиссия постановила '
          'заключить договор с ООО «Авиавторресурс» по цене не менее начальной (минимальной).')

NGR_STRUCT = ('По ЕГРЮЛ, 24 сентября 2026 года АО «Арзамас Капитал» получило 26% ООО «Энджиар Софтлаб»; доля Сергея '
              'Шерстобитова уменьшилась с 90% до 66,6%, Дмитрия Пудова — с 10% до 7,4%. Обе доли сократились '
              'пропорционально; купил ли инвестор доли у участников или вошел через увеличение уставного капитала, '
              'источники не сообщают.')
NGR_SELLER = ('Продавца нет в источниках: по ЕГРЮЛ доли Шерстобитова (90 → 66,6%) и Пудова (10 → 7,4%) уменьшились '
              'пропорционально, что бывает и при увеличении капитала, а сооснователь говорит о привлечении инвестора. '
              'Где искали: TAdviser (карточка компании), SecPost (статья о сделке), ЕГРЮЛ (история участников) — о '
              'покупке долей у участников ничего (вычитка m225).')
FONTE_SEARCHED = ['nationalbusiness.kz (заявление Fonte Capital: продажа завершена 18.09.2026)',
                  'dvizhenie.ru/media/9326 (пересказ Forbes: конечный покупатель не раскрыт)',
                  'cre.ru/news/105987 (со ссылкой на «Ведомости» и СПАРК)', 'mperspektiva.ru', 'elitetrader.ru (в выдаче)',
                  'WebSearch «Fonte Inceptia Alpha Fund сократил долю Самолет» — покупатель пакета нигде не назван '
                  '(вычитка m225, 13.11.2026)']
ARKT_BUYER = ('ООО «Авиавторресурс», Люберцы (Би-порт; основной вид деятельности — производство драгоценных и цветных '
              'металлов). ИНН в открытых статьях не назван: Би-порт, «Первый технический», atomic-energy.ru, '
              'portnews.ru, dp.ru (по выдаче поиска) — профиль не заводили (вычитка m225).')
SHADRINSK_SEARCHED = ['ura.news/news/1053132310', 'WebSearch «Шадринск особняк Треуховых торги итоги продан Дом.РФ»',
                      'oblast45.ru/publication/81583 (не открылся)', 'rutorgi.com (выдача поиска — лот приватизации в Шадринске)',
                      'prousadbi.ru (выдача поиска — история дома купца Треухова)', 'tbankrot.ru (выдача поиска) — '
                      'других статей об этом лоте и итогов торгов 9 октября нет (вычитка m225, 13.11.2026)']


def setf(c, path, old, new, quote, url, log=True):
    """Поле по пути 'a.b'; old — ожидаемое старое значение; вернуть 1, если правка сделана."""
    keys = path.split('.')
    obj = c
    for k in keys[:-1]:
        obj = obj[k]
    if obj.get(keys[-1]) == new:
        return 0
    assert obj.get(keys[-1]) == old, (c['id'], path, obj.get(keys[-1]))
    obj[keys[-1]] = new
    if log:
        fact_edit_guard.log(c, path, new, quote, url, BY, DAY)
    return 1


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    # NGR Softlab
    c = by['g812a7b3b']
    n += setf(c, 'type', 'M&A', 'Инвестиция', Q_NGR, SP)
    if c['date'] != '2026-09-24':
        n += setf(c, 'date', '2026-09-29', '2026-09-24', EGRUL_NGR, '')
        c['date_basis'] = 'registry'
        for ev in c.get('events') or []:
            if ev.get('date') == '2026-09-29':
                ev['date'] = '2026-09-24'
    if c['sum'] != 'Не раскрыта':
        old = c['sum']
        assert old == '≈800 млн ₽ (по оценке)' and c['eco']['sum'] == old, old
        q = ('По оценке аналитика ФГ «Финам» Леонида Делицына, стоимость 26% в NGR Softlab оценивается в 800 млн '
             'рублей. — оценка аналитика, не цена сделки.')
        c['sum'] = c['eco']['sum'] = 'Не раскрыта'
        c.setdefault('retracted', {}).setdefault('sum', []).append(old)
        fact_edit_guard.log(c, 'sum', 'Не раскрыта', q, SP, BY, DAY)
        fact_edit_guard.log(c, 'eco.sum', 'Не раскрыта', q, SP, BY, DAY)
        n += 1
    n += setf(c, 'eco.share',
              'После сделки структура собственности NGR Softlab: Сергей Шерстобитов (через Angara Security) — 66,6%, '
              'Arzamas Capital — 26%, Дмитрий Пудов — 7,4%.', '26% доли в ООО «Энджиар Софтлаб»', EGRUL_NGR, '')
    n += setf(c, 'law.struct', '—', NGR_STRUCT, EGRUL_NGR, '')
    an = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    if an.get('seller') != NGR_SELLER:
        an.pop('buyer', None)
        an.pop('target', None)
        an['seller'] = NGR_SELLER
        n += 1
    # Fonte / «Самолет»
    c = by['g1e37f107']
    n += setf(c, 'type', 'M&A', 'Инвестиция', Q_FONTE, NB)
    n += setf(c, 'title', 'Казахстанский фонд Fonte Capital сократил долю в «Самолете» с 15% до менее 5%',
              'Fonte Capital продал 18% акций «Самолета»', Q_FONTE, NB)
    n += setf(c, 'asset', 'пакет акций ГК «Самолет» (доля сокращена с 15% до менее 5%)',
              'около 18% акций ПАО «ГК «Самолет»»', Q_FONTE, NB)
    n += setf(c, 'eco.share', '—', 'Около 18% акций ПАО «ГК «Самолет»»', Q_FONTE, NB)
    n += setf(c, 'eco.sum', '—', 'Не раскрыта', 'Сумма сделки и причины сокращения пакета не раскрываются.',
              'https://cre.ru/news/105987')
    ev = c['events'][0]
    if ev.get('date') != '2026-09-18':
        assert ev['date'] == '2026-09-30', ev
        ev['date'] = '2026-09-18'
        ev['note'] = ('Fonte Capital сообщила, что фонд завершил продажу пакета около 18% акций и полностью вышел из '
                      'капитала «Самолета».')
        ev['source'] = ['National Business', NB]
        n += 1
    if (c.get('accepted_notes') or {}).get('searched') != FONTE_SEARCHED:
        c.setdefault('accepted_notes', {})['searched'] = FONTE_SEARCHED
        n += 1
    # Корпус ледокола «Арктика»
    c = by['gf145d639']
    n += setf(c, 'status', 'Обсуждается', 'Закрыта', Q_ARKT, BPORT)
    if c['date'] != '2026':
        n += setf(c, 'date', '2026-09-30', '2026',
                  Q_ARKT + ' — день протокола в статьях не назван (Би-порт, 16 октября 2026 года).', BPORT)
    keep = [s for s in c['src'] if 'newsroom24.ru' not in s[1]]
    if len(keep) != len(c['src']):
        c['src'] = keep
        n += 1
    an = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    if an.get('buyer') != ARKT_BUYER:
        an['buyer'] = ARKT_BUYER
        n += 1
    # Ночлежный дом в Астрахани
    c = by['gb3ae9e94']
    if c['date'] != '2026-10-01':
        n += setf(c, 'date', '2026-10-02', '2026-10-01',
                  '17:05, 1 октября 2026. Двухэтажное кирпичное здание на улице Максаковой, 3 выставили на торги с '
                  'начальной стоимостью 48,7 млн рублей.', AB1)
        for e in c.get('events') or []:
            if e.get('date') == '2026-10-02':
                e['date'] = '2026-10-01'
    n += setf(c, 'asset', 'здание бывшего городского ночлежного дома в Астрахани: около 2,7 тыс. кв. м, участок 0,27 га',
              'бывший городской ночлежный дом на улице Максаковой, 3 в Астрахани (2,7 тыс. кв. м), еще одно здание '
              '560 кв. м и участок 0,27 га',
              'Как уточняется в материалах торгов, в состав лота также входит еще одно здание площадью 560 квадратных '
              'метров и земельный участок площадью 0,27 гектара.', RIA_A)
    # Казармы в Павловске
    c = by['g6600b6a4']
    if c['eco'].get('val') != '—':
        assert c['eco']['val'].startswith('Начальная цена лота — 170,67 млн ₽, задаток'), c['eco']['val']
        c['eco']['val'] = '—'
        n += 1
    # Особняк Треуховых
    c = by['g45b335fe']
    if (c.get('accepted_notes') or {}).get('searched') != SHADRINSK_SEARCHED:
        c.setdefault('accepted_notes', {})['searched'] = SHADRINSK_SEARCHED
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
