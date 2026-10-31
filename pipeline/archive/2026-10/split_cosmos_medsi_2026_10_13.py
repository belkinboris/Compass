"""Разделить «IPO Cosmos Hotel Group и «Медси» компании АФК «Система»» (gcf05509a).

13 октября 2026 Артем: «Здесь все намешано… пусть делит карточки, сейчас
предлагает одну большую карту с айпио космоса и медси… Медси — гостиницы и
туризм…». В одной карточке жили три истории: планы IPO Cosmos Hotel Group,
планы IPO «Медси» и состоявшаяся покупка Альфа-Банком 4,85% «Медси» у АФК
«Система» (пришла этапом «closed», отсюда пост «Предмет: Cosmos Hotel Group и
сеть клиник «Медси», Статус: Обсуждается, Отрасль: Гостиницы и туризм»).

- gcf05509a становится карточкой IPO Cosmos Hotel Group: только Cosmos,
  отрасль «Гостиницы и туризм», без этапа о «Медси» и без октябрьских
  источников про «Медси».
- Покупка 4,85% «Медси» — новая карточка M&A в очереди притока
  (pending.json): приток проведет приемку и пришлет пост в консоль.
Тексты — из уже прочитанных полей gcf05509a, разнесены по компаниям.
Без --write — сухой прогон."""
import json, sys
from datetime import datetime, timezone
DATA, PENDING = 'static/data/deals_promoted.json', 'static/data/pending.json'
OLD, NEW = 'gcf05509a', 'g4d7b2e19'
MEDSI_SRC = ['https://www.vedomosti.ru/finance/articles/2026/10/13/1236493-alfa-bank-stal-aktsionerom-medsi',
             'https://www.kommersant.ru/doc/9025051', 'https://tass.ru/ekonomika/28208415',
             'https://www.vedomosti.ru/investments/news/2026/10/13/1236580-aktsii-virosli',
             'https://vc.ru/money/3191949-alfabank-aktsioner-seti-klinik-medsii']


def cosmos(x):
    assert x['title'].startswith('IPO Cosmos Hotel Group и «Медси»'), x['title']
    medsi_event = [e for e in x.get('events') or [] if e.get('id') == OLD + '-closed']
    assert len(medsi_event) == 1
    src = [s for s in x['src'] if s[1] not in MEDSI_SRC]
    medsi_src = [s for s in x['src'] if s[1] in MEDSI_SRC]
    assert len(medsi_src) == 5, medsi_src
    old_val = x['eco']['val']
    x.update({
        'title': 'АФК «Система» готовит IPO Cosmos Hotel Group',
        'target': 'ga5682bdc', 'ind': 'Гостиницы и туризм', 'industries': ['Гостиницы и туризм'],
        'asset': 'акции Cosmos Hotel Group', 'src': src,
        'events': [e for e in x['events'] if e.get('id') != OLD + '-closed'],
    })
    x.pop('discovery_src', None)
    x['eco'] = {
        'sum': 'Не раскрыта',
        'share': 'До IPO АФК «Система» продаст миноритарный пакет Cosmos Hotel Group одному инвестору; '
                 'по условиям term sheet у него есть опция нарастить долю в течение двух лет. Инвестор не назван.',
        'val': '—',
        'target_fin': 'Cosmos Hotel Group: 100 отелей, 5 брендов; выручка за 2025 год — 20,9 млрд ₽ (+20%); '
                      'OIBDA — 7,3 млрд ₽ (+27%); рентабельность по OIBDA — 35%.',
        'fin': 'Средства от IPO/pre-IPO будут направлены преимущественно в развитие компании (cash-in).',
        'rationale': 'АФК «Система» намерена сохранить контроль в Cosmos Hotel Group. Компания ведет переговоры о '
                     'международной экспансии (страны СНГ, Куба, Оман, Индонезия, Саудовская Аравия).',
        'context': '16 апреля 2026 года основатель АФК «Система» Владимир Евтушенков объявил на Биржевом форуме '
                   'Московской биржи о планах IPO двух дочерних компаний — Cosmos Hotel Group и «Медси». К ПМЭФ в '
                   'июне 2026 года по обоим активам были подписаны term sheet на pre-IPO. После закрытия pre-IPO '
                   'сделок корпорация планирует перейти к подготовке полноценных биржевых размещений.',
        'finadv': '—'}
    x['law'] = {'struct': 'Pre-IPO с последующим IPO: один инвестор по подписанному term sheet.',
                'appr': 'Публично не сообщалось',
                'adv': [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались']],
                'terms': 'Подписан term sheet на pre-IPO; у инвестора опция увеличить долю в течение двух лет.'}
    x.pop('extra', None)
    return medsi_event[0], medsi_src, old_val


def medsi_card(event, src, val, interfax):
    e = {k: event[k] for k in ('kind', 'date', 'note', 'source')}
    e.update({'title': 'Сделка завершена', 'id': NEW + '-closed'})
    return {
        'id': NEW, 'date': '2026-10-13',
        'title': 'Альфа-Банк купил 4,85% «Медси» у АФК «Система»',
        'buyer': 'ga2cfae5b', 'seller': 'АФК «Система»', 'seller_id': 'gc2792a44', 'seller_src': 'text',
        'target': 'gae376dd7', 'asset': '4,85% акций «Медси»',
        'ind': 'Здравоохранение', 'type': 'M&A', 'kind': 'acquisition', 'status': 'Закрыта',
        'sum': 'Не раскрыта', 'themes': ['IPO / SPO'],
        'eco': {
            'sum': 'Не раскрыта',
            'share': 'АФК «Система» продала Альфа-Банку 4,85% акций «Медси»; у «Системы» остается 90,64%. Это первый '
                     'названный участник pre-IPO-раунда «Медси», о трех инвесторах которого объявили в июне 2026 года; '
                     'по данным источника «Ведомостей», в раунд вошел и один из фондов «Сколково» — его доля не раскрыта.',
            'val': val,
            'target_fin': '«Медси» — 138 клиник на конец 2025 года; выручка за 2025 год — 61,4 млрд ₽ (+22%), '
                          'скорректированная OIBDA — 13,2 млрд ₽, чистая прибыль — 5,2 млрд ₽, чистый долг/OIBDA — 0,2x. '
                          'В первом полугодии 2026 года выручка «Медси» выросла на 14,2%, до 34,5 млрд ₽, чистая прибыль '
                          'превысила 3 млрд ₽ (+14,3%); доля на рынке коммерческой медицины — 3,5%.',
            'fin': '—',
            'rationale': 'В АФК «Система» сделку назвали «закономерным шагом в подготовке компании к возможному выходу на '
                         'биржу в среднесрочной перспективе». В Альфа-Банке объяснили покупку стратегией набирать '
                         'преимущественно миноритарные пакеты в «компаниях с растущим бизнесом».',
            'context': '16 апреля 2026 года основатель АФК «Система» Владимир Евтушенков объявил о планах IPO «Медси» и '
                       'Cosmos Hotel Group; к ПМЭФ в июне по «Медси» был подписан term sheet на pre-IPO с консорциумом '
                       'из трех российских инвесторов. Доля «Системы» может снизиться и дальше: зарегистрирована '
                       'допэмиссия «Медси» на 12,6 млн акций по закрытой подписке — если инвесторы выкупят ее целиком, '
                       'у «Системы» останется 78–79%. Аналитик Aspring Capital Темир Азизбек оценивает итоговый объем '
                       'таких пакетов у Альфа-Банка в 50 млрд ₽.',
            'finadv': '—'},
        'law': {'struct': 'Продажа пакета акций в рамках pre-IPO «Медси».', 'appr': 'Публично не сообщалось',
                'adv': [['Юридический консультант АФК «Система» (продавца)', 'White Square',
                         'Сопровождение АФК «Система» в продаже 4,85% акций группы «Медси» Альфа-Банку. '
                         'Источник: https://t.me/LawFirms/11525']],
                'terms': '—'},
        'src': src + [interfax],
        'discovery_src': [['Телеграм-канал @LawFirms', 'https://t.me/LawFirms/11525']],
        'events': [e], 'from_ingest': True, 'added': '2026-10-13',
        'pending_since': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }


def apply(data, pending):
    x = next(d for d in data['deals'] if d['id'] == OLD)
    assert NEW not in {d['id'] for d in data['deals']} and NEW not in {c['id'] for c in pending['cards']}
    interfax = next(s for s in x['src'] if 'forumspb/1093768' in s[1])
    event, src, val = cosmos(x)
    card = medsi_card(event, src, val, interfax)
    pending['cards'].append(card)
    print('Cosmos:', x['title'], '| источников', len(x['src']), '| этапов', len(x['events']))
    print('Новая в очередь:', card['id'], card['title'], '| источников', len(card['src']))


d0, p0 = json.load(open(DATA, encoding='utf-8')), json.load(open(PENDING, encoding='utf-8'))
apply(d0, p0)
if '--write' in sys.argv:
    data, pending = json.load(open(DATA, encoding='utf-8')), json.load(open(PENDING, encoding='utf-8'))
    apply(data, pending)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1); f.write('\n')
    with open(PENDING, 'w', encoding='utf-8') as f:
        json.dump(pending, f, ensure_ascii=False, indent=1)   # без перевода строки в конце — как в файле
    print('записано')
