# -*- coding: utf-8 -*-
"""Приток, шаг 3б: новость о сделке, которая УЖЕ ЕСТЬ в базе.

ЗАЧЕМ ОТДЕЛЬНЫЙ ШАГ. `triage.py` делит сырьё на «новая сделка» и
«дополнить карточку N», но потребитель был только у первого: `draft.py` берёт
записи с вердиктом `new` и молча выбрасывает `enrich:<id>`. Между тем это самый
частый случай в жизни: об одной сделке пишут пять изданий за два дня, и вторая
новость обычно приносит то, чего не было в первой, — сумму, продавца,
подтверждение закрытия. Сейчас **923 карточки из 1333 держатся на одном
источнике**, а сумма пуста у 486, продавец — у 694.

ЧТО ДОПИСЫВАЕТСЯ.
  * ССЫЛКА НА ИСТОЧНИК — главный и самый надёжный вклад: её не надо угадывать.
  * ПУСТОЕ поле: сумма, продавец, покупатель. Значение обязано стоять в тексте
    новости — правила те же, что в `draft.py`, ничего не «формулируется».
  * СТАТУС — единственное поле, которое ОБНОВЛЯЕТСЯ, и только вперёд:
    «Обсуждается» → «Закрыта». Замер на 1333 выверенных карточках: правило ни
    разу не назвало закрытой сделку, которая в базе не закрыта (0 раз из 256),
    а все 6 расхождений статуса — в обратную сторону (карточка закрыта, а
    заголовок звучит как намерение). Поэтому вперёд двигать можно, назад — нет.
    «Не состоялась» не трогаем вовсе: сорванная сделка не закрывается новой
    новостью.

ЧЕГО НЕ ДЕЛАЕТСЯ И ПОЧЕМУ.
  * ЗАПОЛНЕННОЕ ПОЛЕ НЕ ПЕРЕПИСЫВАЕТСЯ. Замер на своих же заголовках: 933
    подтверждения против 114 расхождений — то есть каждое девятое выверенное
    значение правило заменило бы догадкой. Расхождение — не повод для правки,
    а повод показать его человеку: «новость называет другую сумму».
  * ПО СЛАБОМУ СОВПАДЕНИЮ НЕ ДОПИСЫВАЕТСЯ НИЧЕГО. У `match.py` четыре сигнала
    разной силы, и они измеримо разные: в корзине «общие слова заголовка» 33 из
    541 совпадений ведут на ЧУЖУЮ карточку (6,1%), а в корзине с названием в
    кавычках — 4 из 568 (0,7%), причём половина из этих четырёх — настоящий
    дубль базы (две карточки про выход Volkswagen), а не ошибка правила.
    Дописать факт не в ту карточку хуже, чем не дописать вовсе, поэтому слабое
    совпадение уходит человеку в `data/inbox/hold/`.
  * ПРЕДМЕТ СДЕЛКИ НЕ ДОПИСЫВАЕТСЯ. Его качество не измерено (в замере
    `draft.py --measure` столбца «предмет» нет), а неизмеренному правилу базу не
    доверяем.

СВЯЗЬ С ТЕЛЕГРАМОМ. Каждое обогащение — это ещё и правка поста: список
изменений считает `publish/format_post.changes`, а решение «будить читателя или
нет» — `should_notify` (уведомляем, только когда факт ДОБАВИЛСЯ). Результат
кладётся в `data/inbox/updates/<дата>.json` — это готовое задание для отправки,
когда появится токен бота (E6).

Запуск:
    python3 pipeline/ingest/enrich.py --measure   # замер правил на своей базе
    python3 pipeline/ingest/enrich.py            # сухой прогон по разбору за сегодня
    python3 pipeline/ingest/enrich.py --write    # дописать в базу
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))

import draft                                        # noqa: E402
import format_post                                  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
SOURCES = os.path.join(HERE, 'sources.json')
TRIAGE = os.path.join(ROOT, 'data', 'inbox', 'triage')
HOLD = os.path.join(ROOT, 'data', 'inbox', 'hold')
UPDATES = os.path.join(ROOT, 'data', 'inbox', 'updates')

# Сильное совпадение — то, в котором название сделки совпало дословно (в
# кавычках) или совпал адрес источника. Слабое — только общие слова заголовка.
STRONG = ('тот же адрес источника', 'название в кавычках')

has = format_post.has


def is_strong(why):
    return any(mark in str(why or '') for mark in STRONG)


def norm(text):
    return re.sub(r'[«»"\'(),.\s]', '', str(text or '')).lower()


def agree(a, b):
    """Одно и то же значение, записанное по-разному, — не расхождение."""
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    return na == nb or na in nb or nb in na


def source_names():
    try:
        reg = json.load(open(SOURCES, encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return {s['id']: s.get('name') or s['id'] for s in reg.get('sources', [])}


def current_value(deal, field, comps):
    """Что в карточке стоит сейчас — с учётом того, что сторона может быть
    записана ссылкой на профиль, а не текстом. Без этого продавец, стоящий
    профилем, выглядел бы пустым полем, и обогащение его бы затёрло."""
    if field == 'seller':
        ref = (comps.get(deal.get('seller_id')) or {}).get('name')
        return ref or (deal.get('seller') if has(deal.get('seller')) else None)
    if field == 'buyer_name':
        ref = (comps.get(deal.get('buyer')) or {}).get('name')
        return ref or (deal.get('buyer_name') if has(deal.get('buyer_name')) else None)
    return deal.get(field) if has(deal.get(field)) else None


def proposals(deal, item, names, comps):
    """Что новость может дать карточке: список (поле, значение, вид, пояснение).

    Вид: «добавить» — поле пусто; «обновить» — статус вперёд; «расхождение» —
    новость называет другое значение заполненного поля (в базу не идёт).
    """
    text = ' '.join(x for x in (item.get('title'), item.get('summary')) if x)
    buyer, _asset, seller = draft.guess_parties(item.get('title'))
    out = []

    url = str(item.get('url') or '')
    known = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
    if url.startswith('http') and url not in known:
        label = names.get(item.get('source_id')) or item.get('source_id') or 'источник'
        out.append(('src', [label, url], 'добавить', 'ещё один источник'))

    for field, guess in (('sum', draft.guess_sum(text)), ('seller', seller),
                         ('buyer_name', buyer)):
        if not guess:
            continue
        current = current_value(deal, field, comps)
        if not current:
            out.append((field, guess, 'добавить', 'в карточке поле пусто'))
        elif not agree(guess, current):
            out.append((field, guess, 'расхождение', 'в карточке «%s»' % str(current)[:60]))

    status = draft.guess_status(text)
    if status == 'Закрыта' and deal.get('status') == 'Обсуждается':
        out.append(('status', 'Закрыта', 'обновить', 'новость сообщает о закрытии'))
    return out


def apply_props(deal, props):
    """Применить к карточке то, что разрешено: «добавить» и «обновить»."""
    for field, value, kind, _why in props:
        if kind == 'расхождение':
            continue
        if field == 'src':
            deal.setdefault('src', []).append(value)
        else:
            deal[field] = value
            if field == 'seller':
                deal['seller_src'] = 'text'
    return deal


# --- замер на своей базе ---------------------------------------------------
def measure():
    """Три числа, ради которых правила и написаны такими осторожными."""
    data = json.load(open(DATA, encoding='utf-8'))
    deals, comps = data['deals'], data['companies']

    fill = {'сумма': 0, 'продавец': 0, 'покупатель': 0}
    same = {'сумма': 0, 'продавец': 0, 'покупатель': 0}
    clash = {'сумма': 0, 'продавец': 0, 'покупатель': 0}
    forward = wrong_forward = 0
    for deal in deals:
        title = str(deal.get('title') or '')
        buyer, _asset, seller = draft.guess_parties(title)
        truth = {
            'сумма': deal.get('sum') if has(deal.get('sum')) else None,
            'продавец': (comps.get(deal.get('seller_id')) or {}).get('name')
                        or (deal.get('seller') if has(deal.get('seller')) else None),
            'покупатель': (comps.get(deal.get('buyer')) or {}).get('name')
                          or (deal.get('buyer_name') if has(deal.get('buyer_name')) else None),
        }
        for key, guess in (('сумма', draft.guess_sum(title)), ('продавец', seller),
                           ('покупатель', buyer)):
            if not guess:
                continue
            if not truth[key]:
                fill[key] += 1
            elif agree(guess, truth[key]):
                same[key] += 1
            else:
                clash[key] += 1
        if deal.get('status') != 'Закрыта':
            forward += 1
            if draft.guess_status(title) == 'Закрыта':
                wrong_forward += 1

    print('Правила обогащения на 1333 выверенных карточках (новость = свой же заголовок):\n')
    print('%-12s %10s %13s %13s' % ('поле', 'дописал', 'подтвердил', 'разошёлся'))
    for key in fill:
        print('%-12s %10d %13d %13d' % (key, fill[key], same[key], clash[key]))
    print('\nРасхождений всего: %d при %d подтверждениях. Именно поэтому заполненное'
          % (sum(clash.values()), sum(same.values())))
    print('поле не переписывается: правило заменило бы догадкой каждое %d-е значение.'
          % round((sum(clash.values()) + sum(same.values())) / max(sum(clash.values()), 1)))
    print('\nСтатус: правило назвало закрытой незакрытую сделку %d раз из %d.'
          % (wrong_forward, forward))
    print('Это и есть цена движения статуса вперёд. Обратное движение запрещено:')
    print('все расхождения статуса в базе — вида «карточка закрыта, заголовок звучит')
    print('как намерение», и, двигая статус назад, мы бы их «чинили» в неверную сторону.')
    print('Сам переход этот замер показать не может: статус карточки выведен из её же')
    print('заголовка, а вперёд его двигает НОВЫЙ заголовок — это видно на фикстуре.')

    single = sum(1 for d in deals
                 if len([s for s in (d.get('src') or []) if len(s) > 1]) <= 1)
    print('\nГлавный вклад — ссылка на источник: у %d карточек из %d он ровно один.'
          % (single, len(deals)))


# --- прогон по разбору за день ---------------------------------------------
def main(argv):
    if '--measure' in argv:
        measure()
        return
    write = '--write' in argv
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    names = source_names()

    day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    path = os.path.join(TRIAGE, day + '.json')
    if not os.path.exists(path):
        print('Нет разбора за %s — сначала fetch.py и triage.py' % day)
        return
    items = [x for x in json.load(open(path, encoding='utf-8'))['items']
             if str(x.get('verdict') or '').startswith('enrich:')]
    if not items:
        print('Новостей о сделках из базы за %s нет.' % day)
        return

    applied, held, nothing, updates = [], [], 0, []
    for item in items:
        deal_id = item['verdict'].split(':', 1)[1]
        deal = by_id.get(deal_id)
        if deal is None:
            held.append((item, None, [('—', '', 'расхождение', 'карточка %s не найдена' % deal_id)]))
            continue
        if not is_strong(item.get('why')):
            held.append((item, deal, [('—', '', 'расхождение',
                                       'слабое совпадение: %s' % item.get('why'))]))
            continue
        props = proposals(deal, item, names, data['companies'])
        clash = [p for p in props if p[2] == 'расхождение']
        good = [p for p in props if p[2] != 'расхождение']
        if clash:
            held.append((item, deal, clash))
        if not good:
            nothing += 1
            continue
        before = json.loads(json.dumps(deal))
        after = apply_props(json.loads(json.dumps(deal)), good)
        change_list = format_post.changes(before, after)
        applied.append((item, deal_id, good, change_list))
        if write:
            apply_props(deal, good)
        updates.append({'deal_id': deal_id, 'news': item.get('url'),
                        'changes': change_list,
                        'notify': format_post.should_notify(change_list),
                        'fields': [p[0] for p in good]})

    print('Новостей о сделках из базы: %d | дописать: %d | на решение: %d | нечего добавить: %d'
          % (len(items), len(applied), len(held), nothing))
    for item, deal_id, good, change_list in applied:
        print('  ДОПИСАТЬ     %s -> %s' % (str(item.get('title'))[:60], deal_id))
        for field, value, _kind, why in good:
            shown = value[0] + ' — ' + value[1] if field == 'src' else str(value)
            print('               %-11s %s (%s)' % (field, str(shown)[:60], why))
        if change_list:
            print('               пост: %s | уведомлять: %s'
                  % (', '.join(change_list), 'да' if format_post.should_notify(change_list) else 'нет'))
    for item, _deal, reasons in held:
        print('  НА РЕШЕНИЕ   %s' % str(item.get('title'))[:60])
        for field, _value, _kind, why in reasons:
            print('               %s: %s' % (field, why))

    if held:
        os.makedirs(HOLD, exist_ok=True)
        out = os.path.join(HOLD, day + '-enrich.json')
        json.dump({'made': day, 'items': [
            {'news': i.get('url'), 'title': i.get('title'), 'verdict': i.get('verdict'),
             'why': i.get('why'), 'reasons': [r[3] for r in reasons]}
            for i, _d, reasons in held]}, open(out, 'w', encoding='utf-8'),
            indent=1, ensure_ascii=False)
        print('  (ожидающие решения: %s)' % os.path.relpath(out, ROOT))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return
    if not applied:
        print('\nЗаписывать нечего.')
        return
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.makedirs(UPDATES, exist_ok=True)
    json.dump({'made': day, 'updates': updates},
              open(os.path.join(UPDATES, day + '.json'), 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)
    print('\nДополнено карточек: %d. Задание на правку постов: data/inbox/updates/%s.json'
          % (len(applied), day))


if __name__ == '__main__':
    main(sys.argv[1:])
