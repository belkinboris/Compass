# -*- coding: utf-8 -*-
"""Разовые правки вычитки, партия m109b (13 ноября 2026): оценка эксперта в сумме сделки.

Находка приемки `sum_is_expert_estimate`: в sum и eco.sum стояло «N (по оценке)», а цифру в
источнике называет эксперт, аналитик или консультант, а не стороны и не источник о самой
сделке. Решение 13 ноября 2026 (docs/card_money.md, раздел «Что идет в сумму»): в sum — только
цена этой сделки; оценка эксперта — «Не раскрыта», цифра с автором остается в eco.val
(во всех карточках ниже она там уже есть), прежнее значение — в retracted.sum. Цитата у каждой
правки — слова источника, по которым видно, что цифру назвал эксперт.

Исключение — ge3a1be68 («Магнит» — 33% «Самбери»): кроме пересчета аналитиков («INFOLine» оценивала всю
сеть в 20–25 млрд ₽, «треть может стоить 6,6–8,3») EastRussia со ссылкой на сервер раскрытия
информации называет цену самой доли — 9,2 млрд ₽ с отложенным возмещением. Это цена этой сделки
по данным издания: sum = «9,2 млрд ₽», sum_basis «reported» (сайт подпишет «по данным источников»),
пересчет аналитиков — в eco.val, где он и был.

review.py «Не раскрыта» не принимает — поэтому разовый скрипт.

    python3 pipeline/archive/2026-11/reread_oneoff_m109b.py [--write]

Повторный запуск ничего не ломает: уже снятая сумма пропускается; иначе — assert на старое значение.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, "static", "data", "deals_promoted.json")
BY, DAY = "reread_oneoff_m109b", "2026-11-13"
N = "Не раскрыта"

# (id, старая сумма, новая, sum_basis или None, цитата, адрес)
EDITS = [
    ('g45ba6605', '1,8–2 млрд ₽ (по оценке)', N, None,
     'Инвестиционный банкир Илья Шумов оценивает актив примерно в 1,8 млрд руб.',
     'https://www.rbc.ru/business/23/05/2025/6830077f9a7947402cdbda13'),
    ('g0924279f', '150–300 млн ₽ (по оценке)', N, None,
     '50% в ООО «Полипап» эксперт по розничному бизнесу и потребительским рынкам Инна Гольфанд оценивает в 150–300 млн руб.',
     'https://www.kommersant.ru/doc/8516012'),
    ('g23ff3a09', '300–350 млн ₽ (по оценке)', N, None,
     'Гендиректор «Infoline-аналитики» Михаил Бурмистров оценил сумму сделки в диапазоне 300–350 млн руб.',
     'https://www.vedomosti.ru/business/articles/2024/12/25/1083550-motorika-kupila-dolei-v-zavode-proizvoditele-invalidnih-kolyasok'),
    ('ge3bc7c98', '4–4,5 млрд ₽ (по оценке)', N, None,
     'Гендиректор агентства «Infoline-Аналитика» Михаил Бурмистров оценил стоимость бизнеса «Эй Кей Раша» в 4–4,5 млрд рублей.',
     'https://vc.ru/food/1706797-rostics-kfc'),
    ('gca6c1eff', '600 млн ₽ (по оценке)', N, None,
     'Гендиректор «Infoline-Аналитики» Михаил Бурмистров предполагает, что стоимость сделки составила около 600 млн руб.',
     'https://www.kommersant.ru/doc/7181682'),
    ('ge3a1be68', '6,6–8,3 млрд ₽ (по оценке)', '9,2 млрд ₽', 'reported',
     'Сегодня доля 33% в компании «ДВ Невада» принадлежит акционерному обществу «Тандер» (учредитель «Магнит)». Ретейлер приобрел ее за 9,2 млрд рублей на условиях «отложенного возмещения» с правом выкупа оставшихся долей',
     'https://www.eastrussia.ru/material/propusk-na-vostok-kak-lenta-izmenit-konkurentsiyu-v-dalnevostochnom-riteyle/'),
    ('ge292671d', '150–200 млн ₽ (по оценке)', N, None,
     'Гендиректор «Infoline-Аналитики» Михаил Бурмистров предполагает, что стоимость «Тетры» — 150–200 млн руб.',
     'https://www.kommersant.ru/doc/7214484'),
    ('gfe151394', '100–130 млн ₽ (по оценке)', N, None,
     '«С учетом финансовых показателей за последние три года и объема предыдущих инвестиций в компанию, сумму сделки по продаже 100% Checkme можно оценить в 130 млн рублей», — сообщил аналитик ФГ «Финам» Леонид Делицын',
     'https://rb.ru/news/chekme-exit/'),
    ('g1ce3ddfc', '60–65 млн ₽ (по оценке)', N, None,
     'Независимый эксперт Алена Кондратьева поясняет, что «Карачинская звезда» выпускает воду «Чистозерье». … Стоимость сделки могла составить 60–65 млн руб., считает эксперт.',
     'https://www.kommersant.ru/doc/6822105'),
    ('g64141daa', '300–675 млн ₽ (по оценке)', N, None,
     'Точная сумма сделки не разглашается, но эксперты оценивают ее в диапазоне от 300 до 675 млн рублей.',
     'https://habr.com/ru/companies/onlinepatent/news/908538'),
]


def _get(card, path):
    cur = card
    for p in path.split('.'):
        if cur is None:
            return None
        cur = cur.get(p)
    return cur


def _set(card, path, value):
    parts = path.split('.')
    cur = card
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


def apply(data, verbose=False):
    sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
    import review
    by = {d['id']: d for d in data['deals']}
    done = 0
    for cid, old, new, basis, quote, url in EDITS:
        c = by[cid]
        if c.get('sum') == new and _get(c, 'eco.sum') == new:
            if verbose:
                print('  уже применено  %s' % cid)
            continue
        assert c.get('sum') == old, (cid, 'sum', c.get('sum'))
        assert _get(c, 'eco.sum') == old, (cid, 'eco.sum', _get(c, 'eco.sum'))
        for path in ('sum', 'eco.sum'):
            _set(c, path, new)
            # прежние записи таблицы правок на это поле погашены отпечатком прежнего значения
            box = c.setdefault('proofread_absorbed', {}).setdefault(path, [])
            fp = review.fix_fingerprint(old)
            if fp not in box:
                box.append(fp)
            fact_edit_guard.log(c, path, new, quote, url, BY, DAY)
        if basis and c.get('sum_basis') != basis:
            c['sum_basis'] = basis
            fact_edit_guard.log(c, 'sum_basis', basis, quote, url, BY, DAY)
        box = c.setdefault('retracted', {}).setdefault('sum', [])
        if old not in box:
            box.append(old)
        done += 1
        if verbose:
            print('  ПРАВИМ  %s sum: %r -> %r' % (cid, old, new))
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
