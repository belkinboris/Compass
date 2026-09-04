# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень) нашла дубль при
дочитывании `g82c59e72` («Игорь Шилов купил российский бизнес Essity
за $117 млн», 2023-07-17): в базе уже есть `g5bb3e777` («Продажа
российского бизнеса Essity (бренды Zewa, Libresse, Libero) компании
«Новые технологии» Игоря Шилова», та же дата 2023-07-17) — тот же
продавец (`seller_id='ga48b2459'`, Essity), тот же покупатель (Игорь
Шилов через ООО «Новые технологии»), та же сумма (~10 млрд ₽/$117
млн), те же три завода (Советск, Венёв, Светогорск), те же бренды
(Zewa, Libresse, Libero/Tena/Tork).

`g5bb3e777` — заметно более полная карточка: 7 источников (включая
собственные пресс-релизы Essity и PR Newswire) против одного
(Коммерсантъ) у `g82c59e72`, заполнены law.appr/struct/terms,
eco.rationale/context/target_fin/share, тема «Уход иностранного
владельца». `g82c59e72` — заметно беднее, но несёт то, чего у
`g5bb3e777` нет: правильно связанный `target` (`g2cceb6b7`, «ЭвоКом»
— тот же профиль, под которым предмет сделки фигурирует в более
позднем, отдельном и уже существующем в базе `g4ba9150f`, продаже
«ЭвоКом» Светогорскому ЦБК в 2025 году). У `g5bb3e777` `target` был
`None` при `target_was_seller=True` — та же комбинация, что уже
чинилась `merge_tochka_rumor_card.py` для другой пары карточек: флаг
означает «у предмета сделки нет профиля», но профиль есть.

ЧТО ДЕЛАЕМ.
1. У `g5bb3e777` чиним самостоятельный дефект: `target` = `g2cceb6b7`,
   `target_was_seller` снимается.
2. Источник `g82c59e72` (kommersant.ru/doc/6110116) переносится в
   `src` `g5bb3e777` — он отсутствует среди уже семи источников,
   отдельная (пусть и не первая) статья того же издания о той же
   сделке.
3. `g82c59e72` сливается в `g5bb3e777`: `merged[g82c59e72] = g5bb3e777`,
   карточка убирается из `deals`, адрес `#/deal/g82c59e72` продолжит
   открывать браузер и приведёт на верную карточку.

Запись `FIXES` для `g82c59e72` (4 записи в двух файлах —
`pipeline/ingest/fixes/batch_agents059_r9.py` и
`pipeline/ingest/fixes/batch_c_2023.py`) удалены ЭТИМ ЖЕ прогоном
ДО слияния — обязательный шаг по уроку CLAUDE.md, иначе
`test_review_table_is_applied_and_not_pending` упадёт на записи,
ссылающейся на несуществующую карточку.

Профиль покупателя `g688b99cb` («Игорь Шилов») после слияния
становится осиротевшим (ни одна сделка на него больше не ссылается)
— не удаляется: `g5bb3e777` уже верно ссылается на профиль
юридического покупателя (`g58575e9c`, «Новые технологии»), а
осиротевший профиль физлица не хуже других 127 уже существующих в
базе орфанов и не искажает данные.

Запуск: python3 pipeline/merge_essity_shilov_dup.py
        python3 pipeline/merge_essity_shilov_dup.py --write
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'

KEEP, DROP = 'g5bb3e777', 'g82c59e72'

TARGET_CO = 'g2cceb6b7'  # «ЭвоКом»
EXTRA_SRC = ['Коммерсантъ', 'https://www.kommersant.ru/doc/6110116']


def norm(s):
    return ' '.join(str(s or '').split())


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    deals = data['deals']
    by_id = {d['id']: d for d in deals}

    keep, drop = by_id.get(KEEP), by_id.get(DROP)
    assert keep and drop, 'карточек пары нет в базе — состояние изменилось, скрипт остановлен'

    assert keep.get('target') is None and keep.get('target_was_seller') is True, \
        f'{KEEP}.target уже не в ожидаемом состоянии: target={keep.get("target")!r}, target_was_seller={keep.get("target_was_seller")!r}'
    assert drop.get('target') == TARGET_CO, f'{DROP}.target изменился: {drop.get("target")!r}'

    keep_urls = {norm(s[1]) for s in (keep.get('src') or []) if len(s) > 1}
    assert norm(EXTRA_SRC[1]) not in keep_urls, 'источник уже перенесён'
    drop_urls = {norm(s[1]) for s in (drop.get('src') or []) if len(s) > 1}
    assert norm(EXTRA_SRC[1]) in drop_urls, 'источник не лежит в карточке-дубле'

    assert keep.get('seller_id') == drop.get('seller_id') == 'ga48b2459', \
        'продавец у пары разошёлся — это не та пара дублей'

    print('ЧИНИМ САМОСТОЯТЕЛЬНЫЙ ДЕФЕКТ У', KEEP)
    print(f'  target: None -> {TARGET_CO} ({data["companies"][TARGET_CO]["name"]!r})')
    print('  target_was_seller: True -> убран')
    print(f'  src: + {EXTRA_SRC}')

    print('\nСЛИЯНИЕ ДУБЛЕЙ')
    print('  оставляем %s  %s' % (KEEP, str(keep['title'])[:80]))
    print('  удаляем   %s  %s' % (DROP, str(drop['title'])[:80]))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    keep['target'] = TARGET_CO
    del keep['target_was_seller']
    keep.setdefault('src', []).append(EXTRA_SRC)

    was = len(deals)
    data['deals'] = [d for d in deals if d['id'] != DROP]
    assert len(data['deals']) == was - 1, 'удалилась не одна карточка'
    data.setdefault('merged', {})[DROP] = KEEP

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано. Карточек в базе: %d (было %d).' % (len(data['deals']), was))


if __name__ == '__main__':
    main('--write' in sys.argv)
