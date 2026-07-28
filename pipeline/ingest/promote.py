# -*- coding: utf-8 -*-
"""Приток, шаг 4 (последний): перенести черновик в базу — или отказать.

ЗАЧЕМ ЭТО ОТДЕЛЬНЫЙ ШАГ. Черновик собран правилами и может быть неполным или
неверным. База — то, что видит юрист. Между ними должна стоять дверь с
замком, а не воронка: этот скрипт пропускает карточку, только если она проходит
ВСЕ инварианты базы, и отказывает с причиной, если нет. Отказ — нормальный
исход: непопавшая карточка стоит дешевле неверной.

ЧТО ПРОВЕРЯЕТСЯ (то же, что тесты `test_data.py` требуют от всей базы):
  * заголовок, дата в формате ГГГГ-ММ-ДД и хотя бы одна ссылка на источник;
  * отрасль — из списка `INDUSTRIES` в интерфейсе, а не любая строка;
  * сумма — одним способом: значок валюты, а не слово;
  * продавец — не заглушка («не раскрыт» это пустота, а не имя);
  * одна компания не занимает в сделке двух ролей, предмет не равен стороне;
  * такой сделки ещё нет в базе (`match.py`), иначе это обогащение, а не новая
    карточка;
  * id уникален.

ТРИ ИСХОДА, А НЕ ДВА. «Не хватает отрасли» и «валюта словом» — разные беды.
Первое человек проставляет за пять секунд, второе означает, что разбор соврал.
Поэтому:
  * ПУСТИТЬ — прошло все проверки, пишется в базу;
  * НА РЕШЕНИЕ — не хватает того, что человек может проставить (сегодня это
    только отрасль: она берётся у профиля компании, а для новой компании
    профиля ещё нет). Карточка ждёт в `data/inbox/hold/`;
  * ОТКАЗ — нарушен инвариант: дубль уже есть в базе, валюта словом, заглушка
    вместо имени, одна сторона в двух ролях, нет ссылки на источник.
Отказ не значит «потеряли»: запись остаётся в сырье и в разборе.

Запуск:
    python3 pipeline/ingest/promote.py            # сухой прогон: кого пустим, кому откажем
    python3 pipeline/ingest/promote.py --write    # записать прошедших в базу
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import match as matcher                                  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
INDEX = os.path.join(ROOT, 'static', 'index.html')
DRAFTS = os.path.join(ROOT, 'data', 'inbox', 'drafts')

WORD_CURRENCY = re.compile(r'\b(?:руб(?:лей|ля|\.)?|долл(?:аров|\.)?|евро|USD|EUR|RUB)\b', re.I)
PLACEHOLDER = re.compile(r'^(?:[—-]|н/д|не\s+раскры[а-яё]*|публично\s+не\s+[а-яё]+)[.\s]*$', re.I)
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def industries():
    html = open(INDEX, encoding='utf-8').read()
    raw = re.search(r'const INDUSTRIES\s*=\s*\[(.*?)\]', html, re.S).group(1)
    return {x.strip().strip('"') for x in raw.split(',') if x.strip()}


def flat(s):
    return re.sub(r'[«»"\'(),.\s]', '', str(s or '')).lower()


def check(draft, base, idx, inds):
    """(причины отказа, причины «на решение»). Обе пусты — карточку пишем."""
    bad, hold = [], []
    if not str(draft.get('title') or '').strip():
        bad.append('нет заголовка')
    if not DATE.match(str(draft.get('date') or '')):
        bad.append('дата не в формате ГГГГ-ММ-ДД')
    src = [s for s in (draft.get('src') or []) if len(s) > 1 and str(s[1]).startswith('http')]
    if not src:
        bad.append('нет ссылки на источник')
    if not draft.get('ind'):
        hold.append('отрасль не определилась — у предмета сделки нет профиля в базе')
    elif draft.get('ind') not in inds:
        bad.append('отрасль не из списка INDUSTRIES (%r)' % draft.get('ind'))
    if draft.get('sum') and WORD_CURRENCY.search(str(draft['sum'])):
        bad.append('валюта словом, а не значком')
    if draft.get('seller') and PLACEHOLDER.match(str(draft['seller']).strip()):
        bad.append('в продавце заглушка, а не имя')
    parties = [flat(draft.get(f)) for f in ('buyer_name', 'seller', 'asset') if draft.get(f)]
    if len(parties) != len(set(parties)):
        bad.append('одна и та же сторона стоит в двух ролях')
    found, why = matcher.match(
        {'title': draft.get('title'), 'date': draft.get('date'),
         'url': src[0][1] if src else None}, idx)
    if found:
        bad.append('такая сделка уже есть в базе: %s (%s)' % (found, why))
    return bad, hold


def new_id(existing):
    """id того же вида, что у остальных карточек: буква g и 8 знаков."""
    n = 0
    while True:
        candidate = 'g%08x' % ((abs(hash(str(datetime.now(timezone.utc)) + str(n)))) % (16 ** 8))
        if candidate not in existing:
            return candidate
        n += 1


def to_card(draft, deal_id):
    """Черновик -> карточка базы. Пустые поля не выдумываются."""
    card = {
        'id': deal_id,
        'date': draft['date'],
        'title': draft['title'],
        'ind': draft['ind'],
        'type': draft.get('type') or 'M&A',
        'status': draft.get('status') or 'Обсуждается',
        'src': draft['src'],
        'from_ingest': True,
    }
    for field in ('sum', 'seller', 'buyer_name', 'asset'):
        if draft.get(field):
            card[field] = draft[field]
    if draft.get('seller'):
        card['seller_src'] = 'text'
    return card


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    idx = matcher.index_base(data['deals'])
    inds = industries()
    existing = {d['id'] for d in data['deals']}

    files = sorted(os.listdir(DRAFTS)) if os.path.isdir(DRAFTS) else []
    drafts = []
    for name in files:
        if name.endswith('.json'):
            drafts += json.load(open(os.path.join(DRAFTS, name), encoding='utf-8'))['drafts']
    if not drafts:
        print('Черновиков нет — сначала fetch.py, triage.py и draft.py.')
        return

    passed, refused, held = [], [], []
    for draft in drafts:
        bad, hold = check(draft, data, idx, inds)
        if bad:
            refused.append((draft, bad))
        elif hold:
            held.append((draft, hold))
        else:
            passed.append((draft, []))

    print('Черновиков: %d | пустить: %d | на решение: %d | отказ: %d'
          % (len(drafts), len(passed), len(held), len(refused)))
    for draft, _ in passed:
        print('  ПУСТИТЬ      %s' % str(draft.get('title'))[:84])
    for draft, reasons in held:
        print('  НА РЕШЕНИЕ   %s\n               %s'
              % (str(draft.get('title'))[:76], '; '.join(reasons)))
    for draft, reasons in refused:
        print('  ОТКАЗ        %s\n               причина: %s'
              % (str(draft.get('title'))[:76], '; '.join(reasons)))
    if held:
        hold_dir = os.path.join(ROOT, 'data', 'inbox', 'hold')
        os.makedirs(hold_dir, exist_ok=True)
        day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        json.dump({'made': day, 'drafts': [d for d, _ in held]},
                  open(os.path.join(hold_dir, day + '.json'), 'w', encoding='utf-8'),
                  indent=1, ensure_ascii=False)
        print('  (ожидающие решения сложены в data/inbox/hold/%s.json)' % day)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return
    if not passed:
        print('\nЗаписывать нечего.')
        return
    for draft, _ in passed:
        deal_id = new_id(existing)
        existing.add(deal_id)
        data['deals'].append(to_card(draft, deal_id))
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано карточек: %d. Всего в базе: %d.' % (len(passed), len(data['deals'])))


if __name__ == '__main__':
    main('--write' in sys.argv)
