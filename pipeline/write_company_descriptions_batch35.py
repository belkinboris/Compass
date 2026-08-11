# -*- coding: utf-8 -*-
"""Тридцать пятая партия: 8 описаний. Кандидаты по числу связанных
сделок среди профилей без описания — каждый проверен по тексту его
собственных сделок в базе (урок CLAUDE.md про «Акрон Холдинг»).

Отдельно проверено: `gf6193c38` «АО «СХП «Колос»»» — не тот же
«Колос», что кондитерская фабрика в Челябинске (`gf8d55310`, описана в
партии 34): разные id, разные сделки, ни одного общего поля. Общее —
только слово «Колос» («колос пшеницы»), популярное у агропредприятий
по всей стране; это не коллизия профилей, а совпадение имени.

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 8 профилям.

Запуск:
    python3 pipeline/write_company_descriptions_batch35.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch35.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

DESCRIPTIONS = {
    'gf6193c38': 'Сельскохозяйственное предприятие; в 2023 году '
                 'купило 50% производителя яблок и голубики «Колос '
                 'Кубани».',
    'gf7b06b4d': 'Платформа для автоматизации бизнес-процессов (RPA); '
                 'в 2024 году MTS AI выкупила 16% у основателя Михаила '
                 'Иванова.',
    'gf5e58704': 'Гостиничный оператор; в 2024 году выкупила у '
                 'аэропорта Домодедово комплекс «Аэротель» (299 '
                 'номеров), которым управляла по аренде с 2012 года.',
    'gf3f11590': 'Железнодорожные грузовые активы «Деметра-холдинга» '
                 '(49% «Транслеса» и 100% «Грузовой компании»); в 2023 '
                 'году проданы оператору «Атлант».',
    'gf3e0918b': 'Челябинская розничная сеть; в 2023 году продана '
                 '«Ленте» местными предпринимателями Игорем Бобиным и '
                 'Дмитрием Бухариным.',
    'gf3a496bd': 'Белгородская компания; в 2024–2025 годах Денис '
                 'Избрехт увеличил долю с 49% до 73,35%.',
    'gf87d9961': 'Производитель салатов и салатных миксов для '
                 'фастфуда (Burger King, «Вкусно — и точка», Додо '
                 'Пицца); в 2025 году 85% выкупил «Бумеранг агроинвест».',
    'gf8741ab4': 'Российский брокер и банк, бывший бизнес Freedom '
                 'Holding в стране; в 2023 году полностью выкуплен '
                 'Максимом Повалишиным.',
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
