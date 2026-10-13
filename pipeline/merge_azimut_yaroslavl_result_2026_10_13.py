# -*- coding: utf-8 -*-
"""Карточка `g39e9e9c2` («Azimut отель Ярославль» выставили на торги»,
собрана 4 сентября 2026) описывала только ОБЪЯВЛЕНИЕ аукциона. Сегодняшний
приток принёс исход: торги прошли 9 октября, актив ушёл по нижней границе
шкалы — и, как выяснили «Ведомости» (подтверждено 76.ru и YarNews через
цепочку СПАРК-Интерфакса), покупателем оказался сам оператор гостиницы,
Azimut Hotels, через структуру основателя сети Александра Клячина.

Ворота притока по ошибке завели на эту же новость ОТДЕЛЬНУЮ карточку
(`g4d3f5352`, черновик d20568834, draft.py/enrich.py не опознали слабое
текстовое совпадение с уже существующей карточкой) — это новый этап
известной сделки, не новая сделка; `g4d3f5352` удаляется из pending.json,
факты уходят в `g39e9e9c2`.

Почему не через таблицу FIXES (review.py): проза ниже — пересказ, а не
дословная цитата источника (review.py принимает правку только если НОВОЕ
значение поля целиком лежит одной цитатой в тексте на диске — не умеет
дописывание/переписывание существующей прозы, docs/card_editing.md,
«Когда review.py не подходит»). Правка — прямым скриптом с assert на
старое значение каждого поля, как предписано тем же документом.

Открытый риск, зафиксированный в law.appr: жалоба ЗАО «Дёма» в УФАС
Санкт-Петербурга на организатора торгов, рассмотрение по существу назначено
на 12 октября — исход на момент записи неизвестен. Статус ставится
«Закрыта» по прямому слову источников («продали», «торги прошли», итоговая
цена названа) — отдельная оговорка про жалобу не отменяет этого по правилу
docs/card_status_dates.md («что статус не двигает»: спорный процессуальный
вопрос — в контекст, а не в статус).

Источники (все дочитаны полностью, тексты в data/inbox/raw/2026-10-13-articles.jsonl):
  Ведомости  https://www.vedomosti.ru/realty/articles/2026/10/13/1236490-azimut-hotels-vikupaet-gostinitsu
  76.ru      https://76.ru/text/realty/2026/10/09/76690851/
  YarNews    https://www.yarnews.net/news/99961-prodazhej-otelya-v-yaroslavle-zajmetsya-piterskoe-ufas/
  YarCube    https://yarcube.ru/newsletter/v-yaroslavle-otel-na-moskovskom-prospekte-kupili-pochti-za-400-millionov

Запуск:
    python3 merge_azimut_yaroslavl_result_2026_10_13.py            # сухой прогон
    python3 merge_azimut_yaroslavl_result_2026_10_13.py --write    # применить
"""
import json
import os
import sys

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import enrich  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g39e9e9c2'
PENDING_DUP_ID = 'g4d3f5352'

VEDOMOSTI = ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2026/10/13/1236490-azimut-hotels-vikupaet-gostinitsu']
S76 = ['76.ru', 'https://76.ru/text/realty/2026/10/09/76690851/']
YARNEWS = ['YarNews', 'https://www.yarnews.net/news/99961-prodazhej-otelya-v-yaroslavle-zajmetsya-piterskoe-ufas/']
YARCUBE = ['YarCube', 'https://yarcube.ru/newsletter/v-yaroslavle-otel-na-moskovskom-prospekte-kupili-pochti-za-400-millionov']

OLD_TITLE = '«Azimut отель Ярославль» выставили на торги'
NEW_TITLE = 'Отель «Азимут» в Ярославле ушёл на торгах его собственному оператору'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'
OLD_DATE = '2026-09-04'
NEW_DATE = '2026-10-09'
NEW_SUM = '361,9 млн ₽'

OLD_VAL = ('Гостиница продаётся посредством публичного предложения — аукциона, где '
           'стоимость лота шаг за шагом снижается. Нижний порог цены установлен на '
           'отметке 361,9 млн рублей.')
NEW_VAL = ('Торги шли через публичное предложение — формат, где цена лота снижается '
           'по шагам до тех пор, пока кто-то не согласится купить по текущей отметке. '
           'Нижней границей было 361,9 млн ₽, и именно по этой цене отель ушёл '
           'единственному допущенному участнику — ООО «Отель Олимпик»; вторую заявку, '
           'от ООО «Огни города» из Химок, отклонили за недостающие или неверно '
           'оформленные документы.')

OLD_CONTEXT = ('Областное министерство имущественных отношений выставило на продажу '
               'гостиницу «Azimut отель Ярославль» на Московском проспекте. Начальная '
               'цена — 723,9 млн ₽.')
NEW_CONTEXT = ('Торги состоялись 9 октября 2026 года — о результате в своём Max-канале '
               'сообщил губернатор Ярославской области Михаил Евраев. Здание построили '
               'в 2008 году на средства правительства Москвы к тысячелетию города '
               '(тогда оно называлось «Святой Георгий»), а спустя десять лет регион '
               'получил его в собственность. С 2021 года гостиницу по 25-летнему '
               'договору занимает сеть Azimut Hotels — и, как выяснили «Ведомости», '
               'подтверждают данные СПАРК-Интерфакса, выкупила актив именно эта сеть: '
               'у компании-победителя, ООО «Отель Олимпик», единственный учредитель — '
               'МКООО «Азимут Групп», а этой структурой в конечном счёте владеет '
               'основатель сети Александр Клячин. Сама сеть от комментариев отказалась.')

OLD_STRUCT = ('Но дважды сделать это не удалось. Теперь власти предпримут очередную '
              'попытку. Согласно данным лота цена составляет 723 миллиона рублей. '
              'Однако цена отсечения — 361 миллион. Иными словами, максимальная сумма '
              'будет снижаться. При проведении торгов посредством публичного '
              'предложения начальная цена будет уменьшаться на фиксированный шаг, '
              'однако она не может опуститься ниже минимальной цены. Сделка будет '
              'заключена с первым участником, который согласится купить лот на любом '
              'из шагов понижения — сообщила министр имущественных отношений '
              'Ярославской области Елена Ермолова. Сами торги должны состояться '
              '9 октября.')
NEW_STRUCT = ('Организатором торгов выступил Российский аукционный дом по поручению '
              'министерства имущественных отношений региона. Первая попытка продать '
              'лот (6 августа) не состоялась из-за отсутствия заявок; вторую, '
              'назначенную на 4 сентября по той же стартовой цене, источники не '
              'описывают как успешную — к публичному предложению перешли уже после неё.')

OLD_APPR = '—'
NEW_APPR = ('Пока шли торги, ЗАО «Дёма» потребовало у организатора акты проверки '
            'пожарной безопасности гостиницы; ООО «Отель в Ярославле», управляющее '
            'зданием, отказалось их раскрыть, сославшись на коммерческую тайну. '
            'Получив отказ, «Дёма» обратилось в питерское УФАС и попросило '
            'остановить продажу; рассмотрение жалобы по существу назначили на '
            '12 октября 2026 года, исход на момент записи неизвестен.')

BUYER_COMPANY_ID = 'g05c33d81'  # Azimut Hotels


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    card = by_id.get(CARD_ID)
    if card is None:
        print('ОТКАЗ: карточки %s нет в базе' % CARD_ID)
        return 1

    assert card.get('title') == OLD_TITLE, card.get('title')
    assert card.get('status') == OLD_STATUS, card.get('status')
    assert card.get('date') == OLD_DATE, card.get('date')
    assert card.get('sum') is None, card.get('sum')
    assert card.get('buyer') is None, card.get('buyer')
    assert card['eco']['val'] == OLD_VAL
    assert card['eco']['context'] == OLD_CONTEXT
    assert card['law']['struct'] == OLD_STRUCT
    assert card['law']['appr'] == OLD_APPR
    assert not card.get('events')

    new_event = {
        'kind': 'closed', 'date': NEW_DATE, 'title': 'Сделка завершена',
        'note': ('Торги прошли 9 октября: единственный допущенный участник, ООО '
                  '«Отель Олимпик», получил гостиницу по нижней границе шкалы — '
                  '361,9 млн ₽ при стартовой цене 723,9 млн ₽; единственный учредитель '
                  'компании — структура основателя Azimut Hotels Александра Клячина.'),
        'source': list(VEDOMOSTI),
    }
    prior = enrich.prior_stage_event(card, new_event)

    print('ПРАВКА %s' % CARD_ID)
    print('  title  : %r -> %r' % (OLD_TITLE, NEW_TITLE))
    print('  status : %r -> %r' % (OLD_STATUS, NEW_STATUS))
    print('  date   : %r -> %r' % (OLD_DATE, NEW_DATE))
    print('  sum    : %r -> %r' % ('—', NEW_SUM))
    print('  buyer  : None -> %r (Azimut Hotels)' % BUYER_COMPANY_ID)
    print('  events : +%s' % (([prior] if prior else []) + ['closed %s' % NEW_DATE]))
    print('  src    : +%s' % [S76[0], YARNEWS[0], YARCUBE[0], VEDOMOSTI[0]])
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    card['title'] = NEW_TITLE
    card['status'] = NEW_STATUS
    card['date'] = NEW_DATE
    card['sum'] = NEW_SUM
    card['buyer'] = BUYER_COMPANY_ID
    card['eco']['val'] = NEW_VAL
    card['eco']['context'] = NEW_CONTEXT
    card['law']['struct'] = NEW_STRUCT
    card['law']['appr'] = NEW_APPR

    events = []
    if prior:
        events.append(prior)
    events.append(new_event)
    card['events'] = events

    existing_urls = {s[1] for s in card.get('src', []) if len(s) > 1}
    for src in (VEDOMOSTI, S76, YARNEWS, YARCUBE):
        if src[1] not in existing_urls:
            card.setdefault('src', []).append(list(src))
            existing_urls.add(src[1])

    pe = card.setdefault('party_evidence', {})
    pe['buyer'] = [{'value': 'Azimut Hotels', 'field': 'buyer',
                    'method': 'registry_chain_confirmed_by_outlets',
                    'url': VEDOMOSTI[1]}]

    # Карточку перечитываем прямо перед записью — чужой пуш не затирается.
    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_by_id = {d['id']: d for d in fresh['deals']}
    fresh_card = fresh_by_id[CARD_ID]
    assert fresh_card.get('title') == OLD_TITLE, 'карточку кто-то уже поправил — перечитайте'
    idx = fresh['deals'].index(fresh_card)
    fresh['deals'][idx] = card

    # Параллельно убираем дублирующий черновик из pending.json: эти факты
    # теперь живут в g39e9e9c2, а не в отдельной карточке.
    pending = json.load(open(PENDING, encoding='utf-8'))
    before = len(pending['cards'])
    pending['cards'] = [c for c in pending['cards'] if c['id'] != PENDING_DUP_ID]
    removed = before - len(pending['cards'])

    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено. Из pending.json убрано карточек: %d.' % removed)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
