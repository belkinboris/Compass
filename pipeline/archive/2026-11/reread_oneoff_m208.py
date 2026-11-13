# -*- coding: utf-8 -*-
"""Разовые правки вычитки, партия m208 (марафон 12 ноября 2026): то, что не ложится в FIXES.

Что и почему — в комментарии у каждой правки. Дата по реестру review.py не принимает
(в цитате нет дня прописью), элемент списка events[] он не адресует.

    python3 pipeline/archive/2026-11/reread_oneoff_m208.py [--write]

Повторный запуск ничего не ломает: правка, у которой поле уже равно новому значению,
пропускается («уже применено»); иначе — assert на старое значение.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m208', '2026-11-12'
FACT = {'date', 'title', 'status', 'sum', 'eco.sum', 'seller', 'buyer', 'buyer_name', 'target',
        'asset', 'asset_id', 'seller_id', 'stake_acquired', 'eco.share', 'law.adv', 'eco.finadv'}

# (id, путь, старое, новое, цитата, адрес)
EDITS = [
    # «Полипластик»: в реестре ООО «Диалог Инвестиции» (управляющая ЗПИФ) вошло в участники
    # 24.07.2026 с 14,08%; в карточке стояло 27 июля — день заметки mergers.ru.
    ('gmru-prime-pervy-poliplastik', 'date', '2026-07-27', '2026-07-24',
     'ЕГРЮЛ, ООО «Группа «Полипластик» (ИНН 5021013384): 2026-07-24 joined: ООО "ДИАЛОГ ИНВЕСТИЦИИ" (None -> 14.08). '
     'МОСКВА, 24 июл - ПРАЙМ. Закрытый паевой инвестиционный фонд "Прайм Первый" под управлением ООО "Диалог Инвестиции" приобрел 14,08% в капитале группы "Полипластик"',
     'https://1prime.ru/20260724/fond-871747341.html'),
    ('gmru-prime-pervy-poliplastik', 'events.0.date', '2026-07-27', '2026-07-24', None, None),

    # «Пеко»: в реестре ООО «Хлебинвест» стало единственным участником 23.07.2026 (карточка — 27 июля,
    # день заметки mergers.ru). Сумма: 800–900 млн ₽ — оценка консультанта Ивана Пешкова всей
    # компании с долгом, а не цена (docs/card_money.md, «Что идет в сумму», 13 ноября 2026) —
    # сумма «Не раскрыта», оценка остается в eco.val.
    ('gmru-kolomenskoe-peko', 'date', '2026-07-27', '2026-07-23',
     '2026-07-23: Фрольцова Галина Викторовна вышел из участников (доля до 25.0%, после None%). '
     '2026-07-23: ООО "ХЛЕБИНВЕСТ" вошел в участники (доля до None%, после 100.0%).',
     'https://projectcompass.ru/api/companies/gbd6de100/fns'),
    ('gmru-kolomenskoe-peko', 'events.1.date', '2026-07-27', '2026-07-23', None, None),
    ('gmru-kolomenskoe-peko', 'sum', '800–900 млн ₽ (по оценке)', 'Не раскрыта',
     'Сумма сделки не раскрывается. Консультант по M&A Иван Пешков оценивает стоимость ХБК «Пеко» в 800–900 млн руб. с учетом долга.',
     'https://new-retail.ru/novosti/retail/kolomenskiy_vykupil_khlebokombinat_peko/'),
    ('gmru-kolomenskoe-peko', 'eco.sum', '800–900 млн ₽ (по оценке)', 'Не раскрыта',
     'Сумма сделки не раскрывается. Консультант по M&A Иван Пешков оценивает стоимость ХБК «Пеко» в 800–900 млн руб. с учетом долга.',
     'https://new-retail.ru/novosti/retail/kolomenskiy_vykupil_khlebokombinat_peko/'),
    ('gmru-kolomenskoe-peko', '+retracted.sum', None, '800–900 млн ₽ (по оценке)', None, None),
    ('gmru-kolomenskoe-peko', '+retracted.seller', None, 'Исак Гилядов, Галина Фрольцова и Марина Цебоева', None, None),
    # «Форма расчетов» рассказывала о покупателе (доля рынка) — факт перенесен в eco.context.
    ('gmru-kolomenskoe-peko', 'eco.fin',
     'ГК «Коломенское» — крупнейший в России производитель хлеба по выручке. Ее доля в 2025 году — около 15% рынка хлебобулочных изделий России в деньгах, по собственной оценке компании.',
     '—', None, None),
    # Профиль «Пеко» приписывал комбинату долю рынка «Коломенского» (15%, «крупнейший по выручке»).
    ('@gbd6de100', 'desc',
     'ООО ХБК «Пеко» выпускает хлебобулочные и кондитерские изделия под брендами «Медведковский», «Пеко» и Alpin Brot; крупнейший по выручке производитель хлеба в России (около 15% рынка в денежном выражении в 2025 году). Комбинат на Полярной улице в Москве основан в 1973 году, выручка в 2025 году — 3,5 млрд ₽.',
     'ООО ХБК «Пеко» выпускает хлебобулочные и кондитерские изделия под брендами «Медведковский», «Пеко» и Alpin Brot. Комбинат на Полярной улице в Москве основан в 1973 году, выручка в 2025 году — 3,5 млрд ₽.',
     None, None),
    # Профиль покупателя называл холдинг «хлебокомбинатом».
    ('@gce291e54', 'desc',
     'Хлебокомбинат: хлеб, кондитерские изделия и замороженная выпечка.',
     'Булочно-кондитерский холдинг: хлеб, кондитерские изделия и замороженная выпечка; владелец — Алексей Тулупов.',
     None, None),
    # БЗТО: заметка этапа почти дословно повторяла «Коммерсантъ» (near_copy); мнение Суворова — в eco.rationale.
    ('gmru-mariholodmash-borsky', 'events.0.note',
     'По неофициальным данным, сумма сделки превысила 10 млрд ₽, а дополнительных вложений в бизнес БЗТО пока не требуется. Руководитель проектов практики «Потребительский сектор и АПК» Strategy Partners Артем Суворов считает, что покупка БЗТО поможет «Марихолодмашу» выстроить вертикальную интеграцию.',
     '«Марихолодмаш» стал владельцем завода; по неофициальным данным, он заплатил больше 10 млрд ₽.',
     None, None),
    # «Арктик СПГ 2»: продавец по распоряжению и по ЕГРЮЛ (участник «ТоталЭнерджиз Разведка Разработка
    # Салманов», АО упрощенного типа) — TotalEnergies EP Salmanov, а не концерн: схема называет
    # сторону договора (docs/card_parties.md, 11 ноября 2026). Профиль концерна снимается со слота продавца.
    ('gmru-nordline-totalenergies-arctic', 'seller', 'TotalEnergies', 'TotalEnergies EP Salmanov',
     'В соответствии с документом, ООО «НордЛайн» («дочка» НОВАТЭКа) может приобрести 10% ООО «Арктик СПГ 2», принадлежащих TotalEnergies EP Salmanov.',
     'https://www.akm.ru/news/nordlayn_mozhet_priobresti_10_arktik_spg_2/'),
    ('gmru-nordline-totalenergies-arctic', 'seller_id', 'g30486604', None,
     'TotalEnergies EP Salmanov — «дочка» французской энергетической компании TotalEnergies в России.',
     'https://www.akm.ru/news/nordlayn_mozhet_priobresti_10_arktik_spg_2/'),
]


def _get(card, path):
    cur = card
    for p in path.split('.'):
        if cur is None:
            return None
        cur = cur[int(p)] if isinstance(cur, list) else cur.get(p)
    return cur


def _set(card, path, value):
    parts = path.split('.')
    cur = card
    for p in parts[:-1]:
        cur = cur[int(p)] if isinstance(cur, list) else cur.setdefault(p, {})
    last = parts[-1]
    if isinstance(cur, list):
        cur[int(last)] = value
    else:
        cur[last] = value


def apply(data, verbose=False):
    sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
    import review
    by = {d['id']: d for d in data['deals']}
    done = 0
    for cid, path, old, new, quote, url in EDITS:
        c = data['companies'][cid[1:]] if cid.startswith('@') else by[cid]
        if path.startswith('+'):
            # дописать в список (retracted.<поле>): снятое значение не вернется обогащением
            box = c.setdefault('retracted', {}).setdefault(path.split('.', 1)[1], [])
            if new not in box:
                box.append(new)
                done += 1
            continue
        cur = _get(c, path)
        if cur == new:
            if verbose:
                print('  уже применено  %s %s' % (cid, path))
            continue
        assert cur == old, (cid, path, cur)
        _set(c, path, new)
        if path.startswith(('eco.', 'law.', 'extra')) and path not in FACT and isinstance(old, str):
            # поле прозы правили записи FIXES: отпечаток прежнего текста — в proofread_absorbed
            fp = review.fix_fingerprint(old)
            box = c.setdefault('proofread_absorbed', {}).setdefault(path, [])
            if fp not in box:
                box.append(fp)
        if quote and path in FACT:
            fact_edit_guard.log(c, path, new, quote, url or '', BY, DAY)
        done += 1
        if verbose:
            print('  ПРАВИМ  %s %s: %r -> %r' % (cid, path, str(old)[:50], str(new)[:60]))
    return done


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data, verbose=True)
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    if not n:
        print('Все правки уже применены.')
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
