# -*- coding: utf-8 -*-
"""Тридцать восьмая партия: 7 описаний. Кандидаты по числу связанных
сделок среди профилей без описания — каждый проверен по тексту его
собственных сделок в базе (урок CLAUDE.md про «Акрон Холдинг»).

Пропущен кандидат `gefa621db` («Академ-Онлайн») — источник сделки не
называет род занятий компании, только рыночный контекст делового
туризма; писать описание значило бы гадать.

Заодно: `gefc0d1df` «ООО «ПК-ТЕРМОСНАБ» и ООО «ТЕРМОКЛИП»» — лот из
двух юрлиц (Технониколь купила оба одной сделкой), признака `lot` не
было — тот же класс, что уже чинили в партии 36 (CLAUDE.md, «Лоту
вместо разбиения ставится признак `lot`»). Проставлен.

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 7 профилям, добавляет
признак `lot` одному из них.

Запуск:
    python3 pipeline/write_company_descriptions_batch38.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch38.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

DESCRIPTIONS = {
    'gefdf55a9': '13 торговых комплексов; в 2024 году проданы '
                 'Сбербанком фирме «Онлайн финанс», связанной с '
                 'кемеровским девелопером «Мера».',
    'gefc0d1df': 'Производитель систем механического крепления '
                 'теплоизоляции; в 2024 году куплен «Технониколь».',
    'gef3d0da0': 'Дистрибутор молочной продукции; в 2024 году купил '
                 '25% производителя сыров «Гранд Премьер» (ГК «Moloko '
                 'Group»).',
    'geeda3c70': 'Надеждинский мусорный полигон в Омском районе; в '
                 '2023 году продан на торгах предпринимателю Дмитрию '
                 'Уколову.',
    'geebb5d31': 'Страховая компания (бывшая «АИГ страховая '
                 'компания»); в 2023 году контроль получили ЛУКОЙЛ и '
                 'фонд «Газпромбанк — Фрезия».',
    'geeb40253': 'Инвестор, выигравший конкурс на управление курортом '
                 '«Архыз» за 24,2 млрд рублей.',
    'gf0a760bf': 'Структура, связанная с Кириллом Демченко; в 2024 '
                 'году купила деловой квартал «Даниловская мануфактура» '
                 '(110 000 кв. м) у «КР Плюс».',
}


LOT_ID = 'gefc0d1df'
LOT_NAME = 'ООО «ПК-ТЕРМОСНАБ» и ООО «ТЕРМОКЛИП»'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

    lot = comps[LOT_ID]
    assert lot['name'] == LOT_NAME, 'имя %s уже другое: %r' % (LOT_ID, lot['name'])
    assert not lot.get('lot'), 'признак lot у %s уже стоит' % LOT_ID
    print('  ПРИЗНАК lot -> True (%s)' % LOT_ID)
    if write:
        lot['lot'] = True

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
