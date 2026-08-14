# -*- coding: utf-8 -*-
"""Пятьдесят третья партия: инвестор вместо цели инвестиции (Startup Lab)
+ 12 описаний.

НАЙДЕНО. Профиль `ge37cdddd` «Startup Lab» стоит `target` сделки
g00e9c766 («hotellab.io привлёк $200 тыс. в seed-раунде от Startup Lab
и Iskra Ventures») — но по заголовку и тексту «Startup Lab» это ОДИН ИЗ
ИНВЕСТОРОВ, а получатель инвестиции (предмет сделки) — hotellab.io.
Родня уже чинившегося класса «раунд/тип сделки вместо имени компании»
(партии 45–46, 49–50, 52), только здесь в `target` попало имя не
предмета, а стороны сделки. Переименован на месте (тот же id, та же
единственная сделка) в «hotellab.io» — отдельного профиля для него в
базе не было.

Плюс 12 описаний обычным G2-кандидатам.

Запуск:
    python3 pipeline/fix_hotellab_name_and_describe_batch53.py            # сухой прогон
    python3 pipeline/fix_hotellab_name_and_describe_batch53.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

RENAMES = {
    'ge37cdddd': ('Startup Lab', 'hotellab.io'),
}
NEW_ALIASES = {
    'ge37cdddd': ['hotellab.io', 'hotellab'],
}

DESCRIPTIONS = {
    'gf0644c08': 'Игровой разработчик (Nexters Global); в 2021 году '
                 'привлёк $50 млн PIPE-инвестиции от Mubadala и VPE '
                 'Capital при слиянии со SPAC и выходе на Nasdaq под '
                 'тикером GDEV.',
    'ga7a23344': 'Туристический стартап; в 2021 году привлёк $1 млн от '
                 'OKS Group, Sistema VC и Almaz Capital.',
    'g152f9c1d': 'Проект добычи и экспорта СПГ на Сахалине; в 2023 '
                 'году долю Shell (27,5%) выкупил «Газпром» за 94,8 '
                 'млрд ₽.',
    'g9b99dcb8': 'Разработчик RPA-платформы для автоматизации бизнес-'
                 'процессов; в 2021 году привлёк $20 млн в раунде '
                 'Series A под руководством Baring Vostok.',
    'ga0570221': 'Платформа для цифрового искусства Snark.art; в 2021 '
                 'году закрыла seed-раунд на $1,5 млн во главе с '
                 'Alphemy Capital.',
    'g5a8d6013': 'Платёжный сервис (ООО «А3»); в 2025 году 80% купил '
                 'фонд Brio Capital у прежнего единственного владельца '
                 'Артура Хримяна.',
    'g47fde1f7': 'Холдинг сенатора Арсена Канокова; в 2022 году вместе '
                 'с Тимати и Антоном Пинским выкупил активы Starbucks '
                 'в России для ребрендинга в Stars Coffee.',
    'g67ef3e91': 'Сеть медицинских лабораторий; в 2023 году купила 90% '
                 'петербургской лаборатории «ФораЛаб» за 50 млн ₽.',
    'g3b3340d2': 'Девелоперская структура ПИК; в 2021 году купила 50% '
                 '«Сигма Холдинг» у экс-топ-менеджера ПИК Владислава '
                 'Свиблова.',
    'ga0f611d6': 'СП Сбера и Mail.ru Group (сервисы доставки и '
                 'логистики); в 2021 году партнёры докапитализировали '
                 'его на 12,2 млрд ₽ в равных долях.',
    'g5ef5049d': 'Структура Льва Кветного (АО «Новоросцемент»); в 2021 '
                 'году купила у банка «Траст» бывшие цементные заводы '
                 '«Интеко» и горные предприятия.',
    'g7ddc4da3': 'Приложение для медитации и сна Mo Meditation; в 2021 '
                 'году привлекло $1 млн от Дмитрия Гришина и '
                 'бизнес-ангелов.',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    mk = data['match_keys']

    for cid, (old, new) in RENAMES.items():
        assert comps[cid]['name'] == old, 'профиль %s уже переименован' % cid
        existing_names = {c.get('name') for c in comps.values()}
        assert new not in existing_names, 'имя %r уже занято' % new
        print('ПЕРЕИМЕНОВАНИЕ  %-12s %r -> %r' % (cid, old, new))
        if write:
            comps[cid]['name'] = new
            mk[cid] = NEW_ALIASES[cid]

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
