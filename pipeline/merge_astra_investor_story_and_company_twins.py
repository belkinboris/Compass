# -*- coding: utf-8 -*-
"""Астра: два профиля одной компании и два репортажа одного сюжета.

ПРОФИЛИ-БЛИЗНЕЦЫ. `g098592a3` («ГК «Астра»») и `g431a713e` («ПАО «Группа
Астра»») — одна и та же компания до и после IPO (TAdviser прямо пишет:
«Группа Астра (ранее ГК Астра)»). Автоматическая кампания слияния
профилей-близнецов (12 пар, 16 августа) искала ФОНЕТИЧЕСКИЕ совпадения —
эта пара под неё не попадала, потому что имя не опечатка и не вариант
написания, а настоящее переименование после выхода на биржу. `g431a713e`
собрал больше сделок (4 против 2) — остаётся живым профилем.

ДВА РЕПОРТАЖА ОДНОГО СЮЖЕТА. `g9d9e7ab6` (РБК Pro, 19 января 2026:
«Астра» рассматривает продажу до 20% стратегическому инвестору, назван
«Росатом») и `g98a85532` (Forbes, дата в карточке 19 марта — по CNews,
источник заявляет о том же процессе позже, к апрелю 2026: тот же процесс,
но список кандидатов расширился — 1С и «Росатом» и банки) — это НЕ два
сюжета, а один и тот же ещё не закрытый переговорный процесс, увиденный
дважды с разницей в 2-3 месяца. Подтверждено живым поиском: ни на август
2026 сделка ни с одним из кандидатов не закрыта («Астра отчиталась за
1 кв. 2026», обзоры рынка мая-июня 2026 обсуждают её как ОТКРЫТЫЙ вопрос).
Оставлен более ранний `g9d9e7ab6` (правило площадки: новые факты правят
ПЕРВЫЙ пост, а не создают второй), `g98a85532` слит в него.

ОТДЕЛЬНО ВНУТРИ `g98a85532`. Его `eco.context` нёс факт про Дениса
Фролова (мажоритарный акционер) — тот продаёт СВОИ 10-15% акций холдингу
Т1 для погашения личных долгов. Это РЕАЛЬНАЯ, но ДРУГАЯ сделка (секондари,
не привлечение капитала в саму компанию); своей карточки у неё пока нет
(объявлена в мае 2026 несколькими независимыми изданиями — Ведомости,
Anti-Malware, smart-lab, — но новой карточки без полного прохода через
приток заводить не стали). Факт переносится в объединённую карточку
КОНТЕКСТОМ, явно помеченным как отдельная от истории сделка — не
сливается с фактами о самой компании.

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. Оба слияния — структурные (id, target, src),
а не дополнение поля по цитате уже привязанного источника; это тот же
класс правки, что merge_vtb_otkrytie_office_rwb_wildberries_dup.py и
fix_azbuka_vkusa_second_dup_and_describe_batch91.py. У `g98a85532` в
`pipeline/ingest/fixes/batch_deep_2026_r5.py` была запись FIXES на поле
`eco.context` — карточка исчезает, запись снимается вместе с ней (тот же
шаг, что уже был обязателен при слиянии Ростелекома и ВТБ/RWB).

ЗАПУСК:
    python3 pipeline/merge_astra_investor_story_and_company_twins.py            # сухой прогон
    python3 pipeline/merge_astra_investor_story_and_company_twins.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')

# --- профили-близнецы ---
CO_DUP = 'g098592a3'
CO_LIVE = 'g431a713e'
CO_DUP_NAME = 'ГК «Астра»'
CO_LIVE_NAME = 'ПАО «Группа Астра»'

# --- дубль карточек ---
DEAL_KEEP = 'g9d9e7ab6'
DEAL_DROP = 'g98a85532'

NEW_TITLE = '«Группа Астра» ведёт переговоры о продаже до 20% капитала стратегическому инвестору'

NEW_SUM = '10,4–10,7 млрд ₽ (по капитализации, оценка для 20% пакета)'

NEW_ECO_VAL = ('10,7 млрд руб. исходя из рыночной капитализации 53,7 млрд '
               'руб. на январь 2026 года; к весне того же года при '
               'капитализации около 52,0 млрд руб. оценка для 20% пакета '
               'составляла 10,4 млрд руб.')

NEW_ECO_CONTEXT = ('В январе 2026 года первым названным кандидатом был '
                    '«Росатом» — как стратегический партнёр для интеграции '
                    'решений в инфраструктурные проекты. К весне 2026 года '
                    'в переговоры вошёл также 1С — крупнейший российский '
                    'разработчик ERP-систем, а «Росатом» и несколько '
                    'крупнейших банков остаются в числе заинтересованных '
                    'сторон. Отдельно от этого: мажоритарный акционер '
                    '«Группы Астра» Денис Фролов ведёт переговоры о продаже '
                    '10–15% СОБСТВЕННЫХ акций IT-холдингу Т1 — это сделка '
                    'о личном пакете акционера, а не о привлечении капитала '
                    'в саму компанию.')

NEW_EXTRA = ('«Группа Астра» рассматривает привлечение стратегического '
             'инвестора на до 20% акционерного капитала. Первым в '
             'переговорах в январе 2026 года был назван «Росатом»; к весне '
             '2026 года список расширился до 1С и нескольких банков. Ни '
             'одна из сторон сделку не подтвердила, переговоры продолжаются.')

FORBES_SRC = ['Forbes', 'https://www.forbes.ru/tekhnologii/557460-astral-noe-putesestvie-1s-mozet-vojti-v-kapital-razrabotcika-astra-linux']


def main(argv):
    write = '--write' in argv
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    deals = data['deals']
    mk = data['match_keys']
    mc = data['merged_companies']
    merged = data['merged']

    # --- проверки исходного состояния ---
    assert CO_DUP in comps and comps[CO_DUP]['name'] == CO_DUP_NAME
    assert CO_LIVE in comps and comps[CO_LIVE]['name'] == CO_LIVE_NAME
    assert CO_DUP not in mc, 'запись в merged_companies уже есть'

    keep = next(d for d in deals if d['id'] == DEAL_KEEP)
    drop = next(d for d in deals if d['id'] == DEAL_DROP)
    assert keep['target'] == CO_DUP, 'target %s уже не указывает на дубль' % DEAL_KEEP
    assert drop['target'] == CO_LIVE, 'target %s уже не тот, что ожидали' % DEAL_DROP
    assert DEAL_DROP not in merged, 'запись в merged уже есть'

    other_deal = next(d for d in deals if d['id'] == 'g83bd07f6')
    assert other_deal['buyer'] == CO_DUP, 'buyer g83bd07f6 уже не указывает на дубль'

    fixes_path = os.path.join(ROOT, 'ingest', 'fixes', 'batch_deep_2026_r5.py')
    fixes_src = open(fixes_path, encoding='utf-8').read()
    assert "dict(id='g98a85532', field='eco.context'" in fixes_src, \
        'запись FIXES на g98a85532.eco.context не найдена — уже снята?'

    print('КОМПАНИИ: %s (%s) -> %s (%s)' % (CO_DUP, CO_DUP_NAME, CO_LIVE, CO_LIVE_NAME))
    print('  переставить target/buyer у %s, %s' % (DEAL_KEEP, 'g83bd07f6'))
    print('СДЕЛКИ: %s слит в %s (один и тот же процесс, два репортажа)' % (DEAL_DROP, DEAL_KEEP))
    print('  запись FIXES на %s.eco.context снимается ОТДЕЛЬНОЙ правкой '
          'ingest/fixes/batch_deep_2026_r5.py (карточка исчезает)' % DEAL_DROP)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    # --- слияние профилей-близнецов ---
    del comps[CO_DUP]
    mc[CO_DUP] = CO_LIVE
    dup_keys = mk.pop(CO_DUP, [])
    for key in dup_keys:
        if key not in mk[CO_LIVE]:
            mk[CO_LIVE].append(key)
    keep['target'] = CO_LIVE
    other_deal['buyer'] = CO_LIVE

    # --- слияние сделок ---
    keep['title'] = NEW_TITLE
    keep['sum'] = NEW_SUM
    keep['eco']['sum'] = NEW_SUM
    keep['eco']['val'] = NEW_ECO_VAL
    keep['eco']['context'] = NEW_ECO_CONTEXT
    keep['extra'] = NEW_EXTRA
    if not any(s[1] == FORBES_SRC[1] for s in keep['src']):
        keep['src'].append(FORBES_SRC)

    deals.remove(drop)
    merged[DEAL_DROP] = DEAL_KEEP

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')

    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
