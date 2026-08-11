# -*- coding: utf-8 -*-
"""Тридцать четвёртая партия: 8 описаний. Кандидаты по числу связанных
сделок среди профилей без описания — каждый проверен по тексту его
собственных сделок в базе (урок CLAUDE.md про «Акрон Холдинг»).

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 8 профилям.

Запуск:
    python3 pipeline/write_company_descriptions_batch34.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch34.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

DESCRIPTIONS = {
    'gfbb048c1': 'Холдинг, в 2024 году купил переработчика отработанных '
                 'шин в резиновую крошку ООО «Премио Крамб».',
    'gfb9f744d': 'Агрегатор автобусных билетов Unitiki; среди '
                 'совладельцев — Андрей Еськин, партнёр Романа '
                 'Абрамовича.',
    'gfb7fe495': 'Туристический сервис YouTravel.me; раунд возглавил '
                 'фонд Starta VC при участии Mission Gate и других '
                 'соинвесторов.',
    'gfb49ca35': 'Хостинг-провайдер; в 2020 году купил петербургского '
                 'конкурента Infobox (ООО «Национальные коммуникации»).',
    'gfa66a7fc': 'Разработчик платформы мониторинга социальных медиа; '
                 'Series A возглавил фонд «Восход» (якорный инвестор — '
                 'группа «Интеррос»).',
    'gf922fd85': 'Инвестиционная структура, связанная с Артёмом Чайкой '
                 'через УК «Дальний Восток»; купила долю в иркутском '
                 'производителе тест-полосок «МедТехСервис».',
    'gf8d55310': 'Кондитерская фабрика в Челябинске; в 2023 году 95% '
                 'долей выкупил предприниматель Акульчев.',
    'gf82563fe': 'Российский агротех-стартап; в 2023 году получил 30 '
                 'млн рублей от фонда Malina VC.',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

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
        print('  ОПИСАНИЕ %-12s %-30s %s' % (cid, str(c.get('name'))[:30], text[:50]))
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
