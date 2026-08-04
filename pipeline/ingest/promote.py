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

NEW_CARDS_NEED_REVIEW (E9, поставлено 28 июля 2026, при первом реальном
прогоне на живой сети). Фильтр «это сделка» (`classify.py`) был измерен на
95,3% полноты и 0% ложных срабатываний — но на списке из 18 РУЧНЫХ соседних
тем. На первом же реальном потоке (1992 записи, 166 признаны сделками) из 11
карточек, прошедших бы в базу автоматически («ПУСТИТЬ»), настоящей сделкой
была ОДНА: «Внуково станет совладельцем Домодедово». Остальные десять — рост
акций Ozon, решение суда о масках с лицом Джигурды, футбольный «раунд плей-офф»
(совпал с «раунд» инвестиций), уход эстрады из квартиры и т.п. Замер на 18
темах не увидел этого класса ошибок вовсе — ровно тот случай CLAUDE.md
«замер сравнивает то, что сравнимо»: маленький ручной список не был живым
потоком.
Пока это не переизмерено и не починено на реальном шуме, ПУСТИТЬ временно
не пишет в базу молча: каждая такая карточка получает причину «на решение» и
ждёт человека — так же, как карточки без отрасли. Это обратимо одной строкой
(`NEW_CARDS_NEED_REVIEW = False`) после того, как `classify.py` перемерен на
реальном потоке, а не на ручном списке.

Запуск:
    python3 pipeline/ingest/promote.py            # сухой прогон: кого пустим, кому откажем
    python3 pipeline/ingest/promote.py --write    # записать прошедших в базу
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import match as matcher                                  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
INDEX = os.path.join(ROOT, 'static', 'index.html')
DRAFTS = os.path.join(ROOT, 'data', 'inbox', 'drafts')

# Смотри NEW_CARDS_NEED_REVIEW в docstring выше — временная страховка после
# находки прогона 28.07.2026: фильтр «это сделка» не проверен на живом потоке.
NEW_CARDS_NEED_REVIEW = True

WORD_CURRENCY = re.compile(r'\b(?:руб(?:лей|ля|\.)?|долл(?:аров|\.)?|евро|USD|EUR|RUB)\b', re.I)
PLACEHOLDER = re.compile(r'^(?:[—-]|н/д|не\s+раскры[а-яё]*|публично\s+не\s+[а-яё]+)[.\s]*$', re.I)
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
PRESENT_CLOSED = re.compile(r'\b(?:покупает|приобретает|прода[её]т|созда[её]т|получает|входит|проводит|привлекает|выкупает)\b', re.I)
HOME_PATHS = {'', '/', '/ru', '/ru/', '/index.html'}


def source_is_homepage(url):
    try:
        parsed = urlparse(str(url or ''))
    except Exception:
        return True
    path = parsed.path or '/'
    return (parsed.scheme not in {'http', 'https'} or not parsed.netloc
            or path.lower() in HOME_PATHS
            )


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
    elif all(source_is_homepage(x[1]) for x in src):
        bad.append('источник ведёт только на главную страницу')
    if not draft.get('ind'):
        hold.append('отрасль не определилась — у предмета сделки нет профиля в базе')
    elif draft.get('ind') not in inds:
        bad.append('отрасль не из списка INDUSTRIES (%r)' % draft.get('ind'))
    if draft.get('sum') and WORD_CURRENCY.search(str(draft['sum'])):
        bad.append('валюта словом, а не значком')
    if draft.get('seller') and PLACEHOLDER.match(str(draft['seller']).strip()):
        bad.append('в продавце заглушка, а не имя')
    if draft.get('status') == 'Закрыта' and PRESENT_CLOSED.search(str(draft.get('title') or '')):
        hold.append('закрытая сделка названа настоящим временем — заголовок нужно привести к завершённому действию')
    if draft.get('type') in ('M&A', 'Продажа недвижимости', 'Выкуп доли'):
        if not (draft.get('buyer') or draft.get('buyer_name')):
            hold.append('для M&A не установлен покупатель')
        if not (draft.get('target') or draft.get('asset_id') or draft.get('asset')):
            hold.append('для M&A не установлен предмет сделки')
        parsed = draft.get('parsed_parties') or {}
        if parsed.get('seller') and not (draft.get('seller') or draft.get('seller_id')):
            hold.append('в источнике назван продавец, но он не перенесён в карточку')
    parties = [flat(draft.get(f)) for f in ('buyer_name', 'seller', 'asset') if draft.get(f)]
    if len(parties) != len(set(parties)):
        bad.append('одна и та же сторона стоит в двух ролях')
    found, why = matcher.match(
        {'title': draft.get('title'), 'date': draft.get('date'),
         'url': src[0][1] if src else None, 'buyer': draft.get('buyer_name'),
         'asset': draft.get('asset'), 'seller': draft.get('seller'),
         'status': draft.get('status')}, idx)
    if found:
        bad.append('такая сделка уже есть в базе: %s (%s)' % (found, why))
    if not bad and NEW_CARDS_NEED_REVIEW:
        hold.append('фильтр «это сделка» не проверен на живом потоке — ждёт подтверждения человека (см. E9)')
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
    """Черновик -> карточка базы. Пустые поля не выдумываются.

    `eco`/`law` заполняются заглушками («—», как у всей базы), а не
    опускаются: интерфейс много где читает `d.law.adv`/`d.eco.rationale`
    без проверки на существование объекта — до первой настоящей записи
    (E9 держал промоут на паузе год) это не давало о себе знать, но карточка
    без `eco`/`law` вообще рушит и «Консультантов», и «Аналитику»."""
    card = {
        'id': deal_id,
        'date': draft['date'],
        'title': draft['title'],
        'ind': draft['ind'],
        'type': draft.get('type') or 'M&A',
        'status': draft.get('status') or 'Обсуждается',
        'src': draft['src'],
        'from_ingest': True,
        'eco': {'sum': '—', 'share': '—', 'val': '—', 'target_fin': '—',
                'fin': '—', 'rationale': '—', 'context': '—', 'finadv': '—'},
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
    }
    for field in ('sum', 'seller', 'buyer_name', 'asset'):
        if draft.get(field):
            card[field] = draft[field]
    if draft.get('events'):
        card['events'] = draft['events']
    if draft.get('seller'):
        card['seller_src'] = 'text'
    source_url = next((s[1] for s in card.get('src', []) if len(s) > 1 and str(s[1]).startswith('http')), None)
    if source_url:
        evidence = {}
        for role, field in (('buyer', 'buyer_name'), ('target', 'asset'), ('seller', 'seller')):
            if card.get(field):
                evidence[role] = [{'value': card[field], 'field': field,
                                   'method': 'explicit_news_title', 'url': source_url}]
        if evidence:
            card['party_evidence'] = evidence
    return card


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    idx = matcher.index_base(data['deals'], data.get('companies'), data.get('match_keys'))
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
    fresh = []
    for draft, _ in passed:
        deal_id = new_id(existing)
        existing.add(deal_id)
        card = to_card(draft, deal_id)
        data['deals'].append(card)
        fresh.append(card)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано карточек: %d. Всего в базе: %d.' % (len(passed), len(data['deals'])))
    notify(fresh, data['companies'])


def notify(fresh, companies):
    """Разослать личные уведомления по подпискам о только что записанных карточках.

    ЗАПАСНОЙ ПУТЬ, А НЕ ОСНОВНОЙ. Обычно приток крутится в одноразовом
    контейнере в другом облаке, а база пользователей стоит во внутренней сети
    хостинга (`192.168.x.x`) и оттуда недостижима — маршрута нет физически.
    Поэтому подписки сверяет сам сайт на старте после деплоя
    (`subscription_feed.scan_on_startup`), а этот вызов работает только там,
    где приток запущен рядом с базой. Двойной отправки он не создаёт:
    повтор отсекается существующей строкой `Notification`.

    Сбой доставки не откатывает базу: карточка записана и без письма остаётся
    записанной — так же устроено уведомление наблюдателей в `enrich.py`.
    """
    try:
        if ROOT not in sys.path:
            sys.path.insert(0, ROOT)
        sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))
        import notify_subscribers

        from db.session import SessionLocal
        with SessionLocal() as db:
            print(notify_subscribers.report(
                notify_subscribers.notify_new_deals(db, fresh, companies)))
    except Exception as exc:
        print('Предупреждение: уведомления по подпискам не отправлены: %s' % exc)


if __name__ == '__main__':
    main('--write' in sys.argv)
