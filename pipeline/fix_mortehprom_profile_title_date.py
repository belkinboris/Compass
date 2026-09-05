# -*- coding: utf-8 -*-
"""«МорТехПром» (карточка gmortehprom2026): профиль компании, привязка
предмета, верная доля в заголовке и дата сделки.

ПОЧЕМУ. Владелец 5 сентября 2026: «ООО «МорТехПром» почему-то не вижу
отчётность финансовую. Это потому что я не залогинен?» — нет: у карточки не
было профиля компании вовсе (предмет записан текстом), а отчётность живёт на
странице компании и требует подтверждённого ИНН в pipeline/fns_registry.py.
Приток 5 сентября (коммит 83e4456) профиль `gmortehprom` завёл и привязал
к карточке через `asset_id` (второй, равноправный с `target` способ
указать предмет — интерфейс читает `target || asset_id`; первая версия
этого скрипта проставила ещё и `target`, и test_one_company_holds_one_role
_in_a_deal справедливо поймал одну компанию в двух ролях). Чего у профиля
не было: ИНН в реестре — отсюда и пустая отчётность — и псевдонимов
(`match_keys`). Здесь — псевдонимы и уточнённое описание; строка реестра —
рядом (fns_registry.py, decision=confirmed), отчётность подтянет сайт при
старте после деплоя.

ЧТО ПОДТВЕРЖДЕНО ЧТЕНИЕМ.
- tbank.ru/business/contractor/legal/1147847042837: ООО «МОРТЕХПРОМ», ИНН
  7802850485, ОГРН 1147847042837, зарегистрировано 7 февраля 2014 года,
  «196650, г Санкт-Петербург, г Колпино, ул Финляндская, д 23», действует;
  ОКВЭД 25.99 «Производство прочих готовых металлических изделий, не
  включенных в другие группировки»; учредители — Шаров Роман Анатольевич
  70% («изменение доли 4 августа»), Рябов Константин Владимирович 30%;
  руководитель — Шаров с 17 декабря 2025 года; выручка 2025 — 9,67 млн ₽,
  чистая прибыль −16,79 млн ₽. У РБК Компании тот же ИНН значится за ООО
  «Айтаком» (ОГРН совпадает) — прежнее имя того же юрлица, не тёзка.
- dp.ru/a/2026/09/04/vladelci-promklastera-v-kolpino: «Роман Шаров приобрёл
  40% долей компании у бывшего генерального директора», «Роману Шарову
  принадлежат 70% "МорТехПрома"», «Константину Рябову — 30%», «с 4 августа
  2026 года 70% компании принадлежат Роману Шарову», «компания изготавливает
  алюминиевые и композитные корпуса пультов управления корабельными
  системами, выполняет для них электромонтажные работы, а также производит
  металлоконструкции для нефтегазовой сферы», «появилась в Петербурге в
  2014 году».

ЧТО ЧИНИТСЯ ПОПУТНО. Заголовок говорил «довёл долю до 100%» — по источнику
и реестру у Шарова 70%, единственными владельцами стали двое (Шаров и
Рябов), это уже верно сказано в `events[0].note`. Дата стояла годом
(«2026»); источник называет 4 августа 2026 года — день, с которого доля
принадлежит Шарову, он и ставится датой сделки и датой этапа «Сделка
завершена» (там стояла дата новости). Смена заголовка и дня — не работа
review.py (см. CLAUDE.md про год в дате), потому одноразовый скрипт с
assert на исходное состояние. Пост в канале ушёл с прежним заголовком —
править его или нет, решает владелец.

Запуск: python3 pipeline/fix_mortehprom_profile_title_date.py
        python3 pipeline/fix_mortehprom_profile_title_date.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gmortehprom2026'
COMPANY_ID = 'gmortehprom'
COMPANY = {
    'name': 'ООО «МорТехПром»',
    'ind': 'Машиностроение',
    'desc': (
        'Петербургский производитель корпусов пультов управления корабельными '
        'системами из алюминия и композита (с электромонтажом) и '
        'металлоконструкций для нефтегазовой сферы; основан в 2014 году, '
        'площадка — в Колпино. С августа 2026 года принадлежит владельцам '
        'промышленного кластера в Колпино: Роману Шарову (70%) и Константину '
        'Рябову (30%).'
    ),
    'kpi': ['Профиль', 'Автоматический'],
}
COMPANY_KEYS = ['ооо мортехпром', 'мортехпром']

OLD_TITLE = 'Роман Шаров довёл долю в «МорТехПроме» до 100%, выкупив оставшиеся 40% у Сергея Бескровного'
NEW_TITLE = 'Роман Шаров выкупил 40% «МорТехПрома» у Сергея Бескровного и довёл долю до 70%'
OLD_DATE, NEW_DATE = '2026', '2026-08-04'
OLD_EVENT_DATE = '2026-09-05'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    profile = data['companies'].get(COMPANY_ID)
    assert profile and profile.get('name') == COMPANY['name'], profile
    assert not data['match_keys'].get(COMPANY_ID), data['match_keys'].get(COMPANY_ID)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)
    assert deal.get('asset_id') == COMPANY_ID and deal.get('target') is None, (deal.get('asset_id'), deal.get('target'))
    assert deal['title'] == OLD_TITLE, deal['title']
    assert deal['date'] == OLD_DATE, deal['date']
    events = deal.get('events') or []
    assert len(events) == 1 and events[0].get('kind') == 'closed' and events[0].get('date') == OLD_EVENT_DATE, events

    print('=== профиль (уже есть, приток 83e4456) ===\n', COMPANY_ID, profile)
    print(' desc -> %s' % COMPANY['desc'])
    print('=== match_keys ===\n', COMPANY_KEYS)
    print('=== %s (asset_id уже -> %s) ===' % (DEAL_ID, COMPANY_ID))
    print(' title  -> %s' % NEW_TITLE)
    print(' date   -> %s (было %s); events[0].date -> %s (было %s)' % (NEW_DATE, OLD_DATE, NEW_DATE, OLD_EVENT_DATE))

    if write:
        profile['desc'] = COMPANY['desc']
        data['match_keys'][COMPANY_ID] = COMPANY_KEYS
        deal['title'] = NEW_TITLE
        deal['date'] = NEW_DATE
        events[0]['date'] = NEW_DATE
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
