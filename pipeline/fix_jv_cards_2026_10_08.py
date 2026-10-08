"""Карточка СП «Яндекс»/VK (g5850b57f) после замечаний владельца 8 октября
2026 («две точки», «форма расчётов не про форму расчётов») и мелкая чистка
по той же проверке базы.

g5850b57f (всё — дословно по CNews и Хабру, источники карточки):
- law.struct: «2027 г.. то есть» — опечатка CNews, двойная точка снята;
- eco.rationale: обрывок «такой симбиоз…» заменён предложением целиком;
- law.appr: вместо «кто сообщил» — что Минцифры контролирует объединение (Хабр);
- eco.fin («Форма расчётов») нёс описание VK Tech: выручка — в eco.target_fin
  («Показатели СП»), чем занимается и продукты — в eco.context, поле — «—».
g179841a1: «15 млрд руб.. Завод», g12a761e4: «112–118 ₽)..» — та же опечатка.
Скрипт можно запускать повторно: уже исправленное пропускается.
Четыре СП с типом «M&A» и три с типом «СП» — тип «Создание СП» (правило
docs/card_status_dates.md; kind остаётся jv).

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static/data/deals_promoted.json')

STRUCT_OLD = 'в I квартале 2027 г.. то есть в период'
STRUCT_NEW = 'в I квартале 2027 г., то есть в период'
RATIONALE_OLD = 'такой симбиоз в итоге приведет к появлению лидера российского рынка облачных и корпоративных ИТ-решений с долей около 30%.'
RATIONALE_PRESS = 'Как сообщал CNews, такой симбиоз в итоге приведет к появлению лидера российского рынка облачных и корпоративных ИТ-решений с долей около 30%.'
RATIONALE_NEW = 'Такой симбиоз в итоге приведет к появлению лидера российского рынка облачных и корпоративных ИТ-решений с долей около 30%.'
APPR_NEW = ('Заместитель министра цифрового развития Евгений Филатов подтвердил объединение '
            'на форуме «Цифровые решения». Представитель Минцифры пояснил, что ведомство '
            'контролирует процесс объединения компаний и влияет на него.')
FIN_HEAD = 'Yandex B2B Tech и VK Tech – это прямые конкуренты'
VK_FIN = 'В первой половине 2026 г. выручка VK Tech составила 9 млрд руб. За год она выросла на 35,3%.'
VK_DESC = ('VK Tech занимается разработкой корпоративного ПО и веб-сервисов. Основные наработки – это '
           'в первую очередь облачный сервис VK Cloud (аналог Yandex Cloud), коммуникационная платформа '
           'VK WorkSpace (аналог «Яндекс 360»), а также продукты для работы с данными Tarantool и VK Data Platform.')
JV_TO_RETYPE = ['g0b47dfbb', 'gcfa06fd8', 'gf424fa11', 'gece30945',
                'gmru-geotek-bashneftegeofizika', 'gmru-rostech-avia-holding', 'ca71a7545']


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    c = deals['g5850b57f']
    if STRUCT_OLD in c['law']['struct']:
        c['law']['struct'] = c['law']['struct'].replace(STRUCT_OLD, STRUCT_NEW)
        assert c['eco']['rationale'] == RATIONALE_OLD
        c['eco']['rationale'] = RATIONALE_NEW
        assert c['law']['appr'].startswith('Как пишет портал'), c['law']['appr']
        c['law']['appr'] = APPR_NEW
        assert c['eco']['fin'].startswith(FIN_HEAD) and VK_FIN in c['eco']['fin'], c['eco']['fin'][:80]
        c['eco']['fin'] = '—'
        assert VK_FIN not in c['eco']['target_fin']
        c['eco']['target_fin'] = c['eco']['target_fin'].rstrip() + ' ' + VK_FIN
        assert 'VK Tech занимается' not in c['eco']['context']
        c['eco']['context'] = c['eco']['context'].rstrip() + ' ' + VK_DESC
        print('g5850b57f: struct, rationale, appr, fin → target_fin/context')
    else:
        assert STRUCT_NEW in c['law']['struct'] and c['eco']['fin'] == '—'
    if c['eco']['rationale'] == RATIONALE_PRESS:
        # Первый вариант с «Как сообщал CNews» приёмка отвела как пресс-язык:
        # фраза целиком, с заглавной, источник — в src.
        c['eco']['rationale'] = RATIONALE_NEW
        print('g5850b57f: rationale без пресс-атрибуции')

    # Шесть полей карточки поставлены записями таблицы FIXES
    # (pipeline/ingest/fixes/fix_yandex_vk_b2b_tech_jv.py); правка мимо таблицы
    # обязана сохранить их отпечатки в `proofread_absorbed` (docs/card_editing.md,
    # «Правка поля мимо таблицы…»), иначе `already_applied()` считает записи
    # неприменёнными и `review.py --write` отказывает целиком.
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ingest'))
    import importlib
    import review
    batch = importlib.import_module('fixes.fix_yandex_vk_b2b_tech_jv')
    absorbed = c.setdefault('proofread_absorbed', {})
    for fix in batch.FIXES:
        if fix['id'] != 'g5850b57f' or review.already_applied(fix, c, data.get('companies')):
            continue
        fp = review.fix_fingerprint(fix['new'])
        if fp not in absorbed.setdefault(fix['field'], []):
            absorbed[fix['field']].append(fp)
            print('g5850b57f: отпечаток записи %s сохранён' % fix['field'])

    for did, field, old, new in (('g179841a1', 'extra', '15 млрд руб.. Завод', '15 млрд руб. Завод'),
                                 ('g12a761e4', 'law.struct', '112–118 ₽)..', '112–118 ₽).')):
        d = deals[did]
        a, _, b = field.partition('.')
        v = d[a][b] if b else d[a]
        if old in v:
            v = v.replace(old, new)
            if b:
                d[a][b] = v
            else:
                d[a] = v
            print('%s: двойная точка в %s' % (did, field))
        else:
            assert new in v, (did, field)

    for did in JV_TO_RETYPE:
        d = deals[did]
        assert d.get('type') in ('M&A', 'СП', 'Создание СП'), (did, d.get('type'))
        if d['type'] != 'Создание СП':
            d['type'] = 'Создание СП'
            print('%s: тип %s' % (did, d['type']))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh = json.load(open(DATA, encoding='utf-8'))          # перечитать перед записью
    by_id = {d['id']: d for d in fresh['deals']}
    for did in ['g5850b57f', 'g179841a1', 'g12a761e4'] + JV_TO_RETYPE:
        by_id[did].update({k: v for k, v in deals[did].items()
                           if k in ('type', 'eco', 'law', 'extra', 'proofread_absorbed')})
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(fresh, f, ensure_ascii=False, indent=1)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
