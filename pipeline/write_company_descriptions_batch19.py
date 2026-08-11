# -*- coding: utf-8 -*-
"""Девятнадцатая партия описаний профилей: чем компания занимается.

ЧТО СЛОМАНО. После восемнадцати партий настоящее описание есть у 575
профилей из 1856 (31%). Кандидатов этой партии искали по узнаваемости
имени среди профилей без описания — каждый проверен по тексту его
собственной сделки в базе (урок CLAUDE.md про «Акрон Холдинг»).

Отдельная находка при чтении контекста: у ДВУХ профилей одной сделки
(«Холдинг «Адамант» купил два стекольных завода AGC в России») стояла
отрасль «ГМК и добыча» — ни холдинг «Адамант» (петербургский девелопер
торговой недвижимости, приобретение стекольных заводов для него —
диверсификация, а не основной бизнес), ни сами заводы (производство
листового стекла) не имеют отношения к горной добыче. Отрасль
унаследовалась от заголовка сделки, а не от рода занятий сторон — тот
же класс дефекта, что «Сбербанк значился „Медиа"». У других профилей
стекольных заводов в базе («AGC Glass Russia», «Pilkington Glass Russia»)
уже стоит «Строительство» — для завода-цели поставлена та же категория;
для самого холдинга «Адамант» — «Недвижимость», его собственный,
общеизвестный основной бизнес.

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 5 профилям, исправляет
отрасль у 2.

Запуск:
    python3 pipeline/write_company_descriptions_batch19.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch19.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

# id профиля -> описание. Только компании, чей род занятий общеизвестен и
# подтверждён текстом собственной сделки в базе.
DESCRIPTIONS = {
    'g3a8fb04f': 'Уральская горно-металлургическая компания — одна из '
                 'крупнейших промышленных групп России, цветная '
                 'металлургия и добыча.',
    'g6f9c9a9c': 'Крупнейшее российское издательство: художественная и '
                 'нон-фикшн литература.',
    'ge2a1dca0': 'Российская энергетическая компания (бывшая «Энел '
                 'Россия»), генерация электроэнергии; контроль перешёл '
                 'к ЛУКОЙЛу.',
    'gdc8edba1': 'Российский телеком-оператор, интернет и цифровое ТВ '
                 'под брендом «Дом.ru».',
    'g18b68845': 'Петербургский девелопер и оператор торговой '
                 'недвижимости.',
}

# Профили, отрасль которых унаследована от заголовка сделки, а не от
# рода занятий самих сторон (см. докстринг). old — что было, для assert.
INDUSTRY_FIXES = {
    'g18b68845': ('ГМК и добыча', 'Недвижимость'),
    'gaeec2c64': ('ГМК и добыча', 'Строительство'),
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
        print('  %-12s %-34s %s' % (cid, str(c.get('name'))[:34], text[:56]))
        c['desc'] = text
        wrote += 1

    ind_fixed = 0
    for cid, (old_ind, new_ind) in INDUSTRY_FIXES.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert c.get('ind') == old_ind, ('отрасль %s уже другая: %r (ожидали %r)'
                                          % (cid, c.get('ind'), old_ind))
        print('  ОТРАСЛЬ  %-12s %-34s %s -> %s'
              % (cid, str(c.get('name'))[:34], old_ind, new_ind))
        c['ind'] = new_ind
        ind_fixed += 1

    print('\nОписаний записано: %d' % wrote)
    print('Отраслей исправлено: %d' % ind_fixed)
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
