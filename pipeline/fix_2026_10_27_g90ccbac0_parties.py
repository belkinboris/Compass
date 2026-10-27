"""5Yes! (g90ccbac0): стороны сделки названы юрлицами и людьми (27 октября 2026).

Владелец: «почему в сделке 5Yes не видно ни кто продавец, ни кто таргет, ни
кто нормальное общество покупатель? …до формирования черновика карты нужно
делать проверку и поиск всех обществ, участвующих в сделке». Карточка вышла с
покупателем-брендом без ИНН, без продавца и с предметом «бренд» — хотя
Коммерсантъ прямо писал «стала владельцем ООО «Полигрин»».

Что найдено (источники в `src` карточки):
  * предмет — ООО «Полигрин» (ИНН 7713476211, ОГРН 1207700223972), владелец
    бренда 5Yes!; выручка за 2025 год — 521 млн ₽ (Mergers.ru);
  * покупатель — ООО «Группа Логика Молока» (ИНН 1655498011, ОГРН 1231600049196):
    по истории участников ЕГРЮЛ (datanewton) 23 октября 2026 года стало
    единственным участником ООО «Полигрин» (100%); ИНН прочитан методом `egr`
    api-fns.ru по ОГРН;
  * продавцы — четыре участника-физлица, вышедшие из ООО «Полигрин» той же
    записью: Анна Давидова (50,4%), Рудольф Захарьяев (25%), Екатерина
    Бушкина (19,6%), Евгений Дубровский (5%);
  * консультант — Atomic Capital (Mergers.ru: инвестиционный консультант
    сделки; сама Atomic Capital в своем канале писала, что сопровождала
    продавцов).

    python3 pipeline/fix_2026_10_27_g90ccbac0_parties.py            # сухой прогон
    python3 pipeline/fix_2026_10_27_g90ccbac0_parties.py --write    # затем facts_derive.py --write
"""
import hashlib
import re
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DEAL = 'g90ccbac0'
BUYER = 'g53717e9e'
DAY = '2026-10-27'
# Mergers.ru — агрегатор: рядом с первоисточником он не источник (test_aggregator_is_not_a_fact_source…),
# выручку и факт закрытия дает New Retail.
MERGERS = ['New Retail', 'https://new-retail.ru/novosti/retail/logika_moloka_priobrela_brend_rastitelnykh_napitkov_5yes/']
EGRUL = ['ЕГРЮЛ: история участников ООО «Полигрин»', 'https://datanewton.ru/contragents/1207700223972/history/timeline']
ATOMIC = ['Atomic Capital (Telegram)', 'https://t.me/atomic_capital_channel/587']
SELLERS = 'Анна Давидова (50,4%), Рудольф Захарьяев (25%), Екатерина Бушкина (19,6%), Евгений Дубровский (5%)'


def target_id(base):
    cid = 'g' + hashlib.sha1('ООО «Полигрин»|1'.encode('utf-8')).hexdigest()[:8]
    assert cid not in base['companies'], cid
    return cid


def plan(base):
    deal = next(d for d in base['deals'] if d['id'] == DEAL)
    assert deal['buyer'] == BUYER and not deal.get('seller') and not deal.get('seller_id') \
        and not deal.get('target') and not deal.get('asset_id'), 'карточка уже менялась'
    assert base['companies'][BUYER]['name'] == 'Логика молока'
    return deal, target_id(base)


def apply(base):
    deal, tid = plan(base)
    base['companies'][tid] = {
        'name': 'Полигрин', 'ind': 'Пищепром и напитки',
        'desc': 'Владелец бренда растительных напитков 5Yes! (премиум-сегмент: кофейни, рестораны, бариста). '
                'По данным New Retail, выручка за 2025 год — 521 млн ₽ (на 70% больше, чем годом раньше). С 23 октября 2026 года — '
                'в составе группы «Логика молока».',
        'kpi': [],
        'ownership': [{'name': 'Логика молока', 'id': BUYER, 'share': '100%', 'as_of': '2026-10-23', 'source': EGRUL}],
    }
    base['match_keys'][tid] = ['полигрин', 'ооо «полигрин»', '5yes!']
    buyer = base['companies'][BUYER]
    buyer['desc'] = ('Группа «Логика молока» (головная компания — ООО «Группа Логика Молока»; до 2023 года бизнес '
                     'работал как «Данон Россия», затем Health & Nutrition) — производитель молочной продукции, '
                     'мороженого, детского питания и растительных напитков; собственный растительный бренд — Planto. '
                     'Строит в Самаре цех по выпуску растительных напитков мощностью 17 тыс. тонн в год.')
    base['match_keys'].setdefault(BUYER, [])
    for alias in ('логика молока', 'группа логика молока', 'ооо «группа логика молока»'):
        if alias not in base['match_keys'][BUYER]:
            base['match_keys'][BUYER].append(alias)
    deal['target'] = tid
    deal['asset'] = 'ООО «Полигрин» — владелец бренда растительных напитков 5Yes!'
    deal['seller'] = SELLERS
    deal['date'] = '2026-10-23'
    deal['date_basis'] = 'registry'
    eco = deal.setdefault('eco', {})
    eco['share'] = ('100% ООО «Полигрин»: по записи в ЕГРЮЛ от 23 октября 2026 года единственным участником '
                    'общества стало ООО «Группа Логика Молока», четыре прежних участника вышли из общества.')
    eco['target_fin'] = 'По данным New Retail, выручка ООО «Полигрин» за 2025 год — 521 млн ₽, на 70% больше, чем годом раньше.'
    law = deal.setdefault('law', {})
    law['struct'] = ('Покупатель — ООО «Группа Логика Молока» (ИНН 1655498011), головная компания группы; '
                     'продавцы — четыре участника-физлица ООО «Полигрин» (Анна Давидова 50,4%, Рудольф Захарьяев 25%, '
                     'Екатерина Бушкина 19,6%, Евгений Дубровский 5%), вышедшие из общества 23 октября 2026 года. '
                     'Команда 5Yes! остается в компании.')
    law['adv'] = [['Инвестиционный консультант', 'Atomic Capital',
                   'Atomic Capital в своем Telegram-канале сообщила, что сопровождала продавцов; '
                   'Mergers.ru называет ее инвестиционным консультантом сделки']]
    deal['events'] = (deal.get('events') or []) + [
        {'kind': 'registered', 'date': '2026-10-23', 'title': 'Смена участника в ЕГРЮЛ',
         'note': '100% ООО «Полигрин» перешли к ООО «Группа Логика Молока»; четыре участника-физлица вышли из общества.',
         'source': EGRUL},
        {'kind': 'announced', 'date': '2026-10-26', 'title': 'Сделка объявлена',
         'note': '«Логика молока» сообщила о завершении сделки; сумма не раскрывается.', 'source': MERGERS},
    ]
    for s in (MERGERS, EGRUL, ATOMIC):
        if s not in deal['src']:
            deal['src'].append(s)
    notes = deal.get('accepted_notes') or {}
    notes.pop('no_profile', None)
    notes.pop('no_inn', None)
    notes['notes'] = ((notes.get('notes') or '') + ' ' if notes.get('notes') else '') + \
        ('27 октября 2026: стороны найдены по истории участников ЕГРЮЛ (datanewton) и api-fns.ru — '
         'покупатель ООО «Группа Логика Молока», предмет ООО «Полигрин», продавцы — четыре физлица.')
    deal['accepted_notes'] = notes
    return tid


def main(argv):
    write = '--write' in argv
    base = json.load(open(DATA, encoding='utf-8'))
    deal, tid = plan(base)
    print('Карточка %s «%s»: предмет → новый профиль %s «Полигрин», продавцы → %s, покупатель %s получает ИНН 1655498011.'
          % (DEAL, deal['title'][:50], tid, SELLERS[:30] + '…', BUYER))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh = json.load(open(DATA, encoding='utf-8'))
    tid = apply(fresh)
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    registry_rows([
        (BUYER, '1655498011',
         'ООО «Группа Логика Молока» ИНН 1655498011 (ОГРН 1231600049196) — покупатель 5Yes! (%s): история '
         'участников ЕГРЮЛ ООО «Полигрин» (datanewton) 23 октября 2026 года показала его единственным '
         'участником; ИНН прочитан методом egr api-fns.ru по ОГРН. Операционное АО «Эйч энд Эн» '
         '(7714626332) — профиль g8cf40802, не этот.' % DEAL),
        (tid, '7713476211',
         'ООО «Полигрин» ИНН 7713476211 (ОГРН 1207700223972) — предмет 5Yes! (%s): Коммерсантъ назвал общество '
         'владельцем бренда, история участников ЕГРЮЛ (datanewton) подтвердила смену участника 23 октября 2026 года.' % DEAL),
    ])
    print('Записано: профиль %s, реестр ФНС — две строки. Дальше: python3 pipeline/facts_derive.py --write' % tid)
    return 0


def registry_rows(rows):
    """Строки `confirmed` в конец REGISTRY — тем же блоком, что пишет приемка
    (accept_card.add_registry_row), но с настоящей причиной: ИНН здесь не из
    совпадения имени, а из истории участников ЕГРЮЛ."""
    path = os.path.join(ROOT, 'pipeline', 'fns_registry.py')
    src = open(path, encoding='utf-8').read()
    marker = "\n\ndef by_company_id() -> dict[str, dict]:"
    assert marker in src, 'не нашли конец REGISTRY в fns_registry.py'
    lines = ['', '', '# Стороны 5Yes! (%s) — %s (pipeline/fix_2026_10_27_g90ccbac0_parties.py).' % (DEAL, DAY), 'REGISTRY += [']
    rows = [r for r in rows if not re.search(r'"company_id": ["\']%s["\']' % r[0], src)]
    if not rows:
        return                                  # повторный прогон: строки уже в реестре
    for cid, inn, reason in rows:
        lines += ['    {"company_id": %r, "decision": "confirmed", "inn": %r,' % (cid, inn),
                  '     "reason": %r,' % reason, '     "date": %r},' % DAY]
    lines.append(']')
    open(path, 'w', encoding='utf-8').write(src.replace(marker, '\n'.join(lines) + marker, 1))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
