# -*- coding: utf-8 -*-
"""Вычитка базы, партия «c» (2 ноября 2026): то, что таблица FIXES не умеет.
Пара к pipeline/ingest/fixes/reread_2026_11_02_c.py (там — проза и структурные
поля с цитатами). Статьи сохранены save_source.py (data/inbox/triage/
sources_2026-11-02.json); продавцы и формы — pipeline/party_legal_names.py.

- g2b1ff5cb («Норникель»/БЕЛАЗ, СП): у СП оба участника — профилями (правило
  docs/card_parties.md «Создание СП»): buyer — «Норильский никель», target —
  новый профиль БЕЛАЗ (ОАО «БЕЛАЗ», Жодино, так его называет СБ); заметка
  no_profile.target снята. asset — коротко, без описания (правило владельца
  2 ноября 2026, п. 1). Отрасль — по предмету: СП делает и чинит подземную
  технику — «Машиностроение», вторая — «ГМК и добыча» (заказчик и место работы).
- gcbf6e44b (Совкомбанк): legal_short покупателя — МКАО «Совко Капитал
  Партнерс» (реестр: МКАО "СОВКО КАПИТАЛ ПАРТНЕРС"; регистр — как в
  Коммерсанте и в имени профиля).
- g2b62ae77 («Рубин»/«Эталон»): asset «здания…» → «здание…» (в лоте одно
  восьмиэтажное здание с участком; «здания» — родительный падеж из заголовка
  TAdviser); legal_short сторон — ПАО «Авиационная корпорация «Рубин»» (реестр:
  ПАО АК "РУБИН", скрипт имени не предложил) и АО «Концерн «Созвездие»» (у
  предложения скрипта не хватало второй закрывающей »); описание «Рубина»
  «производитель электроники для авиации» неверно — по TAdviser и РИА он делает
  комплектующие: гидравлику, взлетно-посадочные устройства, тормоза.
- g73dba9d6 (БЦ «Фрейм»): имя профиля покупателя — «ВИМ», как в источниках и в
  заголовке («Вим» — ошибка регистра), так же УК «ВИМ Сбережения» в описании;
  legal_short продавца — ООО «Форма» (ИНН 7729604691, 100% у ООО
  «ПИК-Инвестпроект»); пустая заметка этапа «Сделка завершена» — своими словами.
- g076af76a («Здоровье.ру»): legal_short предмета — ООО «Здоровье города»
  (реестр «ЗДОРОВЬЕ ГОРОДА»; предложение скрипта «Здоровье Города» — неверный
  регистр); описание профиля — по CNews/Mergers.ru (онлайн-консультаций с
  врачами в источниках нет); заметка этапа — своими словами вместо копии CNews;
  заметки приемки и party_evidence — под нового покупателя (АО «Зевс холдинг»)
  и пятерых продавцов (FIXES buyer_name/seller).

    python3 pipeline/archive/2026-11/fix_reread_2026_11_02_c.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))

BELAZ_ID = 'g2d33fa55'     # accept_card._new_profile_id(base, 'БЕЛАЗ')
CNEWS = 'https://www.cnews.ru/news/top/2026-09-22_byvshij_svinovod_i_postavshchik'
MERGERS_ZD = ('https://mergers.ru/news/Platforma-Zdoroveru-zakryla-sdelku-po-vykupu-rannih-investorov-i-privlekla-'
              'investicii-na-masshtabirovanie-novoj-biznes-modeli-87557')


def legal(comps, cid, value):
    assert comps[cid].get('legal_short') in (None, value), (cid, comps[cid].get('legal_short'))
    comps[cid]['legal_short'] = value


def apply(data):
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']

    # g2b1ff5cb — СП «Норникеля» и БЕЛАЗа
    nn = deals['g2b1ff5cb']
    assert nn.get('buyer') is None and nn.get('target') is None, (nn.get('buyer'), nn.get('target'))
    assert BELAZ_ID not in comps
    assert not any(c.get('name') in ('БЕЛАЗ', 'БелАЗ', 'Белаз') for c in comps.values())
    comps[BELAZ_ID] = {
        'name': 'БЕЛАЗ',
        'ind': 'Машиностроение',
        'desc': 'Белорусский производитель карьерных самосвалов и горной техники из Жодино. Юрлицо — ОАО «БЕЛАЗ», '
                'управляющая компания холдинга «БЕЛАЗ-ХОЛДИНГ».',
        'kpi': [],
        'legal_short': 'ОАО «БЕЛАЗ»',
    }
    assert comps['g2f93d858']['name'] == 'Норильский никель'
    legal(comps, 'g2f93d858', 'ПАО «ГМК «Норильский никель»»')
    nn['buyer'] = 'g2f93d858'
    nn['target'] = BELAZ_ID
    assert nn['asset'] == ('Совместное предприятие «Норникеля» и БЕЛАЗа для разработки и производства подземной '
                           'горной техники (на первом этапе — ремонт и восстановление машин)'), nn['asset']
    nn['asset'] = 'совместное предприятие «Норникеля» и БЕЛАЗа'
    assert nn['ind'] == 'ГМК и добыча' and not nn.get('industries')
    nn['ind'] = 'Машиностроение'
    nn['industries'] = ['Машиностроение', 'ГМК и добыча']
    notes = nn['accepted_notes']
    assert 'target' in notes.get('no_profile', {}), notes
    del notes['no_profile']['target']
    if not notes['no_profile']:
        del notes['no_profile']
    notes['no_inn'] = {'target': 'БЕЛАЗ — белорусское ОАО (Жодино), в ЕГРЮЛ России его нет'}
    notes['notes'] = ('Создание СП: участники — «Норильский никель» (buyer) и БЕЛАЗ (target), профилями; '
                      'продавца у СП нет. Соглашение подписано 7 сентября 2026 — статус «Подписана».')

    # gcbf6e44b — Совкомбанк
    assert deals['gcbf6e44b']['buyer'] == 'gsovcocp'
    legal(comps, 'gsovcocp', 'МКАО «Совко Капитал Партнерс»')

    # g2b62ae77 — «Рубин» / здание ВНИИ «Эталон»
    rb = deals['g2b62ae77']
    assert rb['asset'] == 'здания бывшего ВНИИ «Эталон» в центре Москвы', rb['asset']
    rb['asset'] = 'здание бывшего ВНИИ «Эталон» в Москве'
    pe = rb['party_evidence']['target'][0]
    assert pe['value'] == 'здания бывшего ВНИИ «Эталон» в центре Москвы'
    pe['value'] = rb['asset']
    assert rb['buyer'] == 'g1b7a92fe' and rb['seller_id'] == 'g6765f7ba'
    legal(comps, 'g1b7a92fe', 'ПАО «Авиационная корпорация «Рубин»»')
    legal(comps, 'g6765f7ba', 'АО «Концерн «Созвездие»»')
    assert comps['g1b7a92fe']['desc'] == 'Производитель электроники для авиации.', comps['g1b7a92fe']['desc']
    comps['g1b7a92fe']['desc'] = ('Разработчик и производитель комплектующих для авиационной техники: гидравлические '
                                  'системы и агрегаты, взлетно-посадочные устройства, тормоза. Завод в Балашихе.')

    # g73dba9d6 — БЦ «Фрейм»
    fr = deals['g73dba9d6']
    vim = comps['g59f4de1d']
    assert fr['buyer'] == 'g59f4de1d' and vim['name'] == 'ЗПИФ «Вим Недвижимость»', vim['name']
    vim['name'] = 'ЗПИФ «ВИМ Недвижимость»'
    assert 'под управлением УК «Вим сбережения»' in vim['desc'], vim['desc']
    vim['desc'] = vim['desc'].replace('под управлением УК «Вим сбережения»', 'под управлением УК «ВИМ Сбережения»')
    assert fr['seller_id'] == 'g437baf41'
    legal(comps, 'g437baf41', 'ООО «Форма»')
    ev = fr['events'][0]
    assert ev['kind'] == 'closed' and ev['note'] == '', ev
    ev['note'] = 'Фонд «ВИМ Недвижимость» купил у Forma строящийся бизнес-центр «Фрейм»; цену стороны не назвали.'

    # g076af76a — «Здоровье.ру»
    zd = deals['g076af76a']
    assert zd['target'] == 'g84357246'
    legal(comps, 'g84357246', 'ООО «Здоровье города»')
    tp = comps['g84357246']
    assert tp['desc'] == ('Сервис онлайн-консультаций с врачами; в 2023 году привлек 307 млн ₽ от Kama Flow и '
                          'венчурного клуба «Синдикат».'), tp['desc']
    tp['desc'] = ('Цифровая медицинская платформа: приложение для людей с хроническими заболеваниями, программы '
                  'здоровья и медицинские сервисы. Юрлицо — ООО «Здоровье города»; в 2023 году привлекло 307 млн ₽ '
                  'в раунде во главе с Kama Flow.')
    ev = zd['events'][0]
    assert ev['kind'] == 'closed' and ev['note'].startswith('В ИТ-компании «Здоровье города», которая развивает'), ev
    ev['note'] = ('«Зевс холдинг» Константина Клюки собрал 45,24% «Здоровье.ру»: ранние инвесторы вышли из капитала, '
                  'Kama Flow и «Аюр-Капитал» продали часть долей.')
    np_ = zd['accepted_notes']['no_profile']
    assert np_['buyer'].startswith('Константин Клюка — частный инвестор'), np_
    np_['buyer'] = ('покупатель — АО «Зевс холдинг» (100% у Константина Клюки, CNews); профиля в базе нет, '
                    'ИНН не сверен')
    assert np_['seller'].startswith('три продавца'), np_
    np_['seller'] = ('пять продавцов: Теймур Штернлиб, Дмитрий Васильев, ООО «Некстстеп», ООО «Аюр-Капитал» '
                     '(реестр, 3 сентября 2026) и ООО «КФ Венчурс» (третий этап, CNews); профилей в базе нет')
    pe = zd['party_evidence']
    # review.py --write уже мог переписать party_evidence вместе с buyer_name/seller
    assert pe['buyer'][0]['value'] in ('Константин Клюка', 'АО «Зевс холдинг»'), pe
    pe['buyer'] = [{'value': 'АО «Зевс холдинг»', 'field': 'buyer_name', 'method': 'human_review', 'url': CNEWS}]
    pe['seller'] = [{'value': 'Теймур Штернлиб, Дмитрий Васильев, ООО «Некстстеп», ООО «Аюр-Капитал» и ООО «КФ Венчурс»',
                     'field': 'seller', 'method': 'human_review', 'url': CNEWS}]
    assert ['Mergers.ru', MERGERS_ZD] not in zd['src']
    zd['src'] = zd['src'] + [['Mergers.ru', MERGERS_ZD]]


def main(argv):
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    apply(data)
    print('g2b1ff5cb участники СП, профиль БЕЛАЗ, asset, отрасль; gcbf6e44b legal_short; g2b62ae77 asset, '
          'legal_short ×2, описание «Рубина»; g73dba9d6 имя и описание ЗПИФ, legal_short, заметка этапа; '
          'g076af76a legal_short, описание, заметка этапа, заметки приемки, party_evidence, src')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(BASE, encoding='utf-8').read() == raw, 'база изменилась во время прогона — перезапустите'
    out = json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
    open(BASE, 'w', encoding='utf-8').write(out)
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
