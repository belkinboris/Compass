# -*- coding: utf-8 -*-
"""Сорок третья партия: испорченная ссылка `target` (Уфабурмаш) + 7 описаний.

НАЙДЕНО. У сделки g67b98f28 («Бурсервис» приобрел 51% акций
«Уфабурмаша») поле `target` ссылалось на профиль g9fbbbd54 «Михаил
Данилов» — человека, а не купленную компанию. Сам текст сделки прямо
объясняет: «оставшиеся 49% сохранились за Михаилом Даниловым» — то есть
Данилов совладелец/продавец доли, а не предмет сделки. Профиля
«Уфабурмаш» в базе не было вовсе (человек стоял на его месте). Родня
урока CLAUDE.md про ЛСР/Domina Пулково: «стороной сделки может быть
записан профиль совсем другой сущности» — только здесь испорчено поле
`target`, а не `seller`.

ЧТО ДЕЛАЕТ.
1. Создаёт профиль «ООО «Уфабурмаш»» (уфимский производитель бурового
   инструмента), переносит на него `target` сделки g67b98f28.
2. Ставит `seller` той же сделки на g9fbbbd54 «Михаил Данилов» — он
   действительно продавец/совладелец по тексту сделки, профиль человека
   не переименовывается и не удаляется, просто занимает верную роль.
3. Проставляет описания 7 профилям, прочитанным по своим единственным
   связанным сделкам.

Запуск:
    python3 pipeline/fix_ufaburmash_target_and_describe_batch43.py            # сухой прогон
    python3 pipeline/fix_ufaburmash_target_and_describe_batch43.py --write    # записать
"""
import hashlib
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

DANILOV_ID = 'g9fbbbd54'
DEAL_ID = 'g67b98f28'
NEW_SEED = 'ООО «Уфабурмаш», буровой инструмент, Бурсервис 2026'
NEW_NAME = 'ООО «Уфабурмаш»'
NEW_DESC = ('Уфимский производитель бурового инструмента (долота PDC, '
            'элементы бурильных колонн); выручка 409 млн ₽ (2025). В '
            '2026 году 51% купил «Бурсервис», 49% остались за прежним '
            'совладельцем.')

DESCRIPTIONS = {
    'gcdf5803f': 'Сыктывкарский производитель пиломатериалов; в 2022 '
                 'году вместе со «Слотексом» купил фабрики IKEA в '
                 'России (Ленинградская, Кировская, Новгородская '
                 'области).',
    'g006e1e6c': 'ИТ-компания с выручкой около 780 млн ₽ (2025); в '
                 '2026 году 30% купила ГК «Урбантех», контроль (70%) '
                 'остался у продавца «Нетлайн».',
    'g83d157e5': 'Производитель картонной упаковки и вкладышей для '
                 'лекарств в Обнинске (с 2017 года, около 100 '
                 'сотрудников); в 2026 году куплен ГК «Свеза».',
    'g62e73b64': 'Производитель мороженого; в 2026 году выкупил 100% '
                 'Йошкар-Олинского хладокомбината, чтобы нарастить '
                 'производственные мощности.',
    'g65d37f0f': 'Структура угольной группы «Каракан Инвест»; в 2026 '
                 'году купила 85% «Группы Русская энергия», владеющей '
                 '«Воркутауглем».',
    'g504a7eab': 'В 2026 году купила у «Транслома» финтех-сервис '
                 '«Вториум»; аналитики оценивали актив от 640 млн ₽.',
    'g6bb3fdf8': 'Лизинговая компания; в 2026 году купила российский '
                 'бизнес немецкого производителя складской техники '
                 'Jungheinrich.',
}


def new_id(seed, existing):
    cid = 'g' + hashlib.sha1(seed.encode('utf-8')).hexdigest()[:8]
    assert cid not in existing, 'коллизия id: %s' % cid
    return cid


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    deals = data['deals']
    by_id = {d['id']: d for d in deals}

    # --- 1. исправление испорченной ссылки target ---
    danilov = comps[DANILOV_ID]
    assert danilov['name'] == 'Михаил Данилов', 'профиль Данилова уже изменён'
    deal = by_id[DEAL_ID]
    assert deal['target'] == DANILOV_ID, 'target сделки уже не Данилов'
    assert deal.get('seller') is None, 'seller сделки уже заполнен'
    assert deal.get('seller_id') is None, 'seller_id сделки уже заполнен'
    assert deal['title'].startswith('«Бурсервис»'), 'сделка не та'

    existing_ids = set(comps.keys())
    existing_names = {c.get('name') for c in comps.values()}
    assert NEW_NAME not in existing_names, 'имя нового профиля уже занято'
    nid = new_id(NEW_SEED, existing_ids)
    print('НОВЫЙ ПРОФИЛЬ  %-12s %s' % (nid, NEW_NAME))
    print('ПЕРЕНОС TARGET  %s: %s -> %s' % (DEAL_ID, DANILOV_ID, nid))
    print('SELLER  %s: seller_id -> %s (Михаил Данилов), seller -> текстом' % (DEAL_ID, DANILOV_ID))

    if write:
        comps[nid] = {'name': NEW_NAME, 'ind': 'Нефть и газ', 'desc': NEW_DESC}
        deal['target'] = nid
        deal['seller_id'] = DANILOV_ID
        deal['seller'] = danilov['name']

    # --- 2. описания ---
    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  ОПИСАНИЕ %-12s %-40s %s' % (cid, str(c.get('name'))[:40], text[:50]))
        if write:
            c['desc'] = text
        wrote += 1

    print('\nОписаний записано: %d' % wrote)
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

    real = sum(1 for v in comps.values()
               if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
    print('Всего профилей с описанием: %d из %d (%d%%)'
          % (real, len(comps), round(100 * real / len(comps))))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
