# -*- coding: utf-8 -*-
"""«Амбер Талвис»: предмет становится профилем, дата — днём торгов, этапов два.

ЧТО ЧИНИТ. Владелец 9 сентября 2026 разобрал эту карточку по косточкам и был
прав в каждом пункте: «кто в здравом уме может подумать, что это разные
сделки… очевидно же, что это две вехи (два этапа) одной сделки — сначала
выставили на торги, затем купили»; «вторая новость почему-то не пишет про
предмет нормально и его нет на схеме».

Дубль уже слит (`pipeline/merge_specs/2026-09-09-amber-talvis.json`). Этот
скрипт закрывает остальное, по одному пункту замечания:

  * ПРЕДМЕТ НЕ БЫЛ СВЯЗАН НИ С ЧЕМ. `target` пуст, в `asset` — только текст.
    В ЕГРЮЛ ровно одно АО «Амбер Талвис» (ИНН 6831000321, ОГРН 1026801156409,
    Тамбовская область — сходится с карточкой: производственная площадка в
    рабочем посёлке Новая Ляда под Тамбовом). Заводится профиль
    `gambertalvis`, `target` указывает на него — теперь предмет кликабелен, а
    финансовый блок ФНС появится на его странице сам.
  * ПОКУПАТЕЛЬ СТОЯЛ ТЕКСТОМ, хотя профиль «ГК Росспиртпром» (`g130b6d10`) в
    базе есть с самого начала. `buyer` указывает на него, `buyer_name`
    снимается (у покупателя либо профиль, либо текст — `test_buyer_is_named_
    once`). ИНН 7730605160: гендиректор Дронов Андрей Михайлович и регистрация
    в Татарстане совпадают с `eco.context` карточки дословно.
  * «ПРЕДМЕТ / ДОЛЯ» НЕ НАЗЫВАЛ ПРЕДМЕТ. Там стояло «Ранее «Росспиртпрому»
    принадлежало 25,5% тамбовской компании. Таким образом, по итогам аукциона
    доля достигла 98,37%» — это история доли, а не ответ на вопрос «что
    купили». Сам ответ лежал в соседнем поле, `law.struct`: «На торги было
    выставлено 62 486 акций предприятия, или 72,87% от их общего количества».
    Он и ставится первым предложением — перенос внутри карточки, ни одного
    нового числа. Поле ставила таблица `FIXES`, поэтому правка дописывает
    отпечаток в `proofread_absorbed` (иначе `test_review_table_is_applied_
    and_not_pending` справедливо покраснеет — урок CLAUDE.md о ручном
    пересказе поля, которое ставила таблица).
  * ДАТА БЫЛА ДНЁМ ПУБЛИКАЦИИ, А НЕ ДНЁМ СДЕЛКИ. Стояло 12 августа — день
    выхода статьи TAdviser; торги прошли 10 августа, и это сказано в самой
    карточке: «электронные торги прошли на площадке Росэлторг 10 августа».
    Тот же класс, что уже записан в CLAUDE.md («Дата новости — не дата
    сделки»); `review.py` менять дату не умеет, поэтому одноразовый скрипт.
  * ЭТАП БЫЛ ОДИН, И ТОТ О ТОМ, КОГДА МЫ УЗНАЛИ. Стояло «Сделка завершена»
    от 12 августа с текстом «в середине августа 2026 года стало известно,
    что…» — то есть дата публикации и точка зрения редакции, а не событие
    сделки; блок «Ход сделки» при одном этапе вдобавок не рисуется вовсе
    (`timelineHtml` требует минимум двух строк). Этапов становится два, и оба
    про сделку: 18 июня — выставлено на торги (первый аукцион не состоялся,
    заявок не поступило), 10 августа — продано на повторных торгах по цене
    отсечения. Это второе подряд замечание владельца об одном и том же
    (первое было на ТРК «Родник»/«Алмаз»).

ФАКТЫ ТОЛЬКО ИЗ САМОЙ КАРТОЧКИ: `assert` перед записью требует, чтобы каждое
число из текста этапов и нового «Предмета / доли» уже встречалось в карточке
(после слияния она несёт и то, что было в удалённой).

Запуск:
    python3 pipeline/fix_amber_talvis_parties_and_milestones.py          # сухой
    python3 pipeline/fix_amber_talvis_parties_and_milestones.py --write
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'pipeline' / 'ingest'))

import review  # noqa: E402  — fix_fingerprint для отпечатка вычитки

DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'

DEAL_ID = 'g63c7d1bb'
TARGET_ID = 'gambertalvis'
BUYER_ID = 'g130b6d10'          # ГК Росспиртпром, уже есть в базе

OLD_DATE = '2026-08-12'
NEW_DATE = '2026-08-10'
OLD_BUYER_NAME = '«Росспиртпром»'

OLD_SHARE = ('Ранее «Росспиртпрому» принадлежало 25,5% тамбовской компании. '
             'Таким образом, по итогам аукциона доля достигла 98,37%.')
NEW_SHARE = ('72,87% акций АО «Амбер Талвис» — 62 486 акций, выставленных '
             'единым лотом. Ранее «Росспиртпрому» принадлежало 25,5% '
             'тамбовской компании. Таким образом, по итогам аукциона доля '
             'достигла 98,37%.')

TARGET_PROFILE = {
    'name': 'Амбер Талвис',
    'ind': 'Пищепром и напитки',
    'desc': ('Тамбовский производитель этилового спирта; производственная '
             'площадка в рабочем посёлке Новая Ляда. До 2026 года 72,87% '
             'акций принадлежали государству и были включены в план '
             'приватизации, остальное — «Росспиртпрому» и миноритариям.'),
    'kpi': ['Профиль', 'Прочитан'],
}
TARGET_KEYS = ['амбер талвис']

EVENTS = [
    {
        'kind': 'announced',
        'date': '2026-06-18',
        'title': 'Актив выставлен на торги',
        'note': ('Росимущество выставило на аукцион 72,87% акций АО «Амбер '
                 'Талвис». Начальная цена лота — 3,89 млрд ₽, задаток — '
                 '777,5 млн ₽. Аукцион 18 июня не состоялся: заявок не '
                 'поступило.'),
        'source': ['Торги.гов',
                   'https://torgi.gov.ru/new/public/lots/lot/21000030950000001156_1'],
    },
    {
        'kind': 'closed',
        'date': '2026-08-10',
        'title': 'Сделка завершена',
        'note': ('Повторные торги прошли публичным предложением: цена '
                 'отсечения — вдвое ниже начальной. Единственным участником '
                 'стал «Росспиртпром», выкупивший пакет за 1,94 млрд ₽ и '
                 'доведший долю в компании до 98,37%.'),
        'source': ['Ведомости',
                   'https://www.vedomosti.ru/business/articles/2026/08/11/1220271-aktiv-yuriya-sheflera'],
    },
]

NUM = re.compile(r'\d[\d\s ]*(?:[.,]\d+)?')


def digits(text):
    return {re.sub(r'[\s ]', '', m.group(0)).rstrip('.,') for m in NUM.finditer(text)}


def main(write=False):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    deal = next((d for d in data['deals'] if d['id'] == DEAL_ID), None)
    assert deal, 'карточки %s нет в базе' % DEAL_ID

    assert deal.get('date') == OLD_DATE, deal.get('date')
    assert deal.get('buyer') is None, deal.get('buyer')
    assert deal.get('buyer_name') == OLD_BUYER_NAME, deal.get('buyer_name')
    assert deal.get('target') is None, deal.get('target')
    events_now = deal.get('events') or []
    assert len(events_now) == 1 and events_now[0].get('date') == OLD_DATE \
        and events_now[0].get('kind') == 'closed', events_now
    assert not events_now[0].get('id'), 'этап уже уходил в канал — перенос не предусмотрен'
    assert (deal.get('eco') or {}).get('share') == OLD_SHARE, (deal.get('eco') or {}).get('share')
    assert TARGET_ID not in data['companies'], 'профиль %s уже есть' % TARGET_ID
    assert BUYER_ID in data['companies'], 'профиля «Росспиртпром» нет'
    assert data.get('merged', {}).get('c46d3e581') == DEAL_ID, \
        'сначала слияние дубля c46d3e581 (pipeline/merge_duplicate_deals_batch.py)'

    have = digits(json.dumps(deal, ensure_ascii=False))
    for text, what in [(NEW_SHARE, 'предмет')] + [(e['note'] + ' ' + e['title'], e['kind']) for e in EVENTS]:
        invented = sorted(x for x in digits(text) if x not in have)
        assert not invented, 'в тексте (%s) есть числа, которых нет в карточке: %s' % (what, invented)
    for ev in EVENTS:
        assert ev['source'][1] in json.dumps(deal, ensure_ascii=False), \
            'источник этапа не из карточки: %s' % ev['source'][1]

    print('=== профиль предмета %s ===' % TARGET_ID)
    print(json.dumps(TARGET_PROFILE, ensure_ascii=False, indent=1))
    print('=== карточка %s ===' % DEAL_ID)
    print(' дата:     %s -> %s (день торгов, а не публикации)' % (OLD_DATE, NEW_DATE))
    print(' покупатель: текст %r -> профиль %s' % (OLD_BUYER_NAME, BUYER_ID))
    print(' предмет:  нет -> профиль %s' % TARGET_ID)
    print(' «Предмет / доля»:\n   было:  %s\n   стало: %s' % (OLD_SHARE, NEW_SHARE))
    print(' этапы: было 1 (%s, «%s»), станет 2:' % (events_now[0]['date'], events_now[0]['title']))
    for e in EVENTS:
        print('   %s · %s · %s' % (e['date'], e['kind'], e['title']))
        print('     ', e['note'])

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    data['companies'][TARGET_ID] = TARGET_PROFILE
    data.setdefault('match_keys', {})[TARGET_ID] = TARGET_KEYS

    deal['date'] = NEW_DATE
    deal['buyer'] = BUYER_ID
    deal.pop('buyer_name', None)
    deal['target'] = TARGET_ID
    deal['eco']['share'] = NEW_SHARE
    deal.setdefault('proofread_absorbed', {}).setdefault('eco.share', []).append(
        review.fix_fingerprint(OLD_SHARE))
    deal['events'] = EVENTS

    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    print('\nЗаписано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
