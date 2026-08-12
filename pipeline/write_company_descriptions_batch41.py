# -*- coding: utf-8 -*-
"""Сорок первая партия: 7 описаний. Кандидаты по числу связанных
сделок среди профилей без описания — каждый проверен по тексту его
собственных сделок в базе (урок CLAUDE.md про «Акрон Холдинг»). Двум
из семи (`gea803245`, `gea6b7460`) признак `lot` уже проставлен
прошлым прогоном — здесь только описания.

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 7 профилям.

Запуск:
    python3 pipeline/write_company_descriptions_batch41.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch41.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

DESCRIPTIONS = {
    'gfd1d67e3': 'Компания, связанная с кемеровским девелопером «Мера»; '
                 'в 2024 году купила у Сбербанка 13 торговых комплексов '
                 '«Сибирские городки».',
    'geb0ac573': 'Российский бизнес Goldman Sachs (включая долю в '
                 'HeadHunter); при реструктуризации продан '
                 'топ-менеджерам банка.',
    'geaeb1582': 'Операционная компания сети магазинов детских товаров '
                 '«Кораблик»; в 2023 году 5% долю купил Олег Сохацкий, '
                 'бенефициар поставщика игрушек МТК «Алиса».',
    'ge9ceb16e': 'Владелец АО «Племенной Завод «Комсомолец»» (188 тыс. '
                 'га сельхозземель в Забайкалье); в 2023 году продан '
                 'фонду Глеба Фетисова.',
    'ge99563a8': 'Энергосбытовая компания в Челябинске, связана с '
                 'застройщиком «Голос.Девелопмент»; в 2023 году продана '
                 '«Россети Урал».',
    'gea803245': 'Производитель салатов Ultra Fresh (два юрлица '
                 'группы «Салатерия»), поставляет продукцию '
                 '«Макдоналдс»; в 2024 году выкуплен фондом «Бумеранг '
                 'капитал».',
    'gea6b7460': 'Дистрибьютор алкогольной продукции с сетью '
                 'алкомаркетов «Мир вкуса» (31 точка); в 2023 году '
                 'куплен Виктором Шкуренко у Натальи Уснунц.',
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
