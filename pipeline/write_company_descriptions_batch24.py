# -*- coding: utf-8 -*-
"""Двадцать четвёртая партия описаний профилей: чем компания занимается.

ЧТО СЛОМАНО. После двадцати трёх партий настоящее описание есть у 609
профилей из 1855 (33%). Кандидатов искали по числу связанных сделок
среди профилей без описания — каждый проверен по тексту его
собственных сделок в базе (урок CLAUDE.md про «Акрон Холдинг»). Два
профиля («Группа АЗТ», «Рязанская чаеразвесочная фабрика») —
выжившие из слияний падежных близнецов в прошлых прогонах, описание
тогда не проставили; закрыто сейчас.

Отдельная находка: у «Готэк (группа)» (`gb5db1ea5`) стояла отрасль
«Пищепром и напитки» — тот же класс дефекта, что у «Каппа РУС» в
прошлом прогоне. Готэк — производитель гофроупаковки, а собственная
сделка профиля (покупка трёх упаковочных заводов Mondi) несёт ind
«Производство тары» ПРАВИЛЬНО — расхождение только у профиля компании,
не у сделки. Исправлено на «Производство тары».

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 7 профилям, исправляет
отрасль у 1.

Запуск:
    python3 pipeline/write_company_descriptions_batch24.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch24.py --write    # записать
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
    'gf480d948': 'Российская сеть автозаправочных станций под брендом '
                 '«ТРАССА», вышла на биржу в 2023 году.',
    'g91a073fb': 'Российский банк, дочерняя структура шведской IKEA; '
                 'в 2022 году 50% долей выкупил Кредит Европа банк.',
    'ga6078435': 'Российская лизинговая компания.',
    'gb5db1ea5': 'Российский производитель гофроупаковки и гибкой '
                 'упаковки.',
    'g489c4c35': 'Группа компаний полного цикла производства '
                 'лекарств (в составе — «АЗТ Химсинтез» и «АЗТ '
                 'Фармресурс»).',
    'g8ee31e1c': 'Российская фабрика по фасовке чая.',
    'g082a5811': 'Морской торговый порт в Таганроге, входил в '
                 'группу НЛМК Владимира Лисина.',
}

# Профиль, отрасль которого не совпадает с родом занятий компании (см.
# докстринг); собственная сделка профиля несёт правильный ind. old — что
# было, для assert.
INDUSTRY_FIXES = {
    'gb5db1ea5': ('Пищепром и напитки', 'Производство тары'),
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
