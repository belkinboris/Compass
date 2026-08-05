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

ТРИ ИСХОДА, А НЕ ДВА. «Из заголовка не видно, что продают» и «валюта словом» —
разные беды. Первое человек разбирает за полминуты, второе означает, что разбор
соврал. Поэтому:
  * ПУСТИТЬ — прошло все проверки, пишется в базу;
  * НА РЕШЕНИЕ — не хватает того, что человек может проставить: не выделен
    предмет, не названа ни одна сторона, похоже на уже описанную сделку.
    Карточка ждёт в `data/inbox/hold/` ВМЕСТЕ С ПРИЧИНОЙ (`hold_reasons`);
  * ОТКАЗ — нарушен инвариант: дубль уже есть в базе, валюта словом, заглушка
    вместо имени, одна сторона в двух ролях, нет ссылки на источник.
Отказ не значит «потеряли»: запись остаётся в сырье и в разборе.

ЧЕГО ВОРОТА БОЛЬШЕ НЕ ТРЕБУЮТ (правка 5 августа). Требовать покупателя и
отрасль значило требовать от новой карточки большего, чем есть у старых: 431
карточка базы из 1541 (28%) покупателя не называет вовсе, а отрасль «Не
определена» законна и показывается на экране. Прежнее правило пропустило бы
лишь 68% нашей собственной базы, и «отрасль не определилась» была причиной
задержки номер один — 21 черновик из 41. Сделка узнаётся по тому, что назван
ПРЕДМЕТ и хотя бы одна сторона.

ТОРМОЗ E9 СНЯТ 4 АВГУСТА 2026 — и вот на каком основании.

Он был поставлен 28 июля, когда выяснилось, что фильтр «это сделка» измерен на
списке из 18 придуманных тем, а на живом потоке шумит. Это была верная
предосторожность, но за неделю она ни разу не пропустила НИ ОДНОЙ карточки, а
очередь «на решение» падала в контейнер рутины и исчезала вместе с ним.

Что изменилось:
  * фильтр перемерен на реальном потоке (2167 записей за сутки, 113 кандидатов
    размечены чтением, разметка в `live_labels.json`): точность 35% -> 81% без
    потери единой настоящей сделки;
  * отрасль перестала быть замкнутым кругом. Раньше она бралась только у
    профиля компании, а у новой компании профиля нет и не будет, пока карточка
    не попадёт в базу, — из-за этого «пустить» было равно нулю ВСЕГДА, даже со
    снятым тормозом. Теперь отрасль читается и по словам предмета сделки;
    совместное правило измерено на 1538 карточках базы: покрытие 74%,
    точность 84,5%.

Вместо глухого тормоза работает развилка по уверенности (`confidence`).
Замер на потоке 4 августа: из 44 черновиков прошли 10, и все десять —
настоящие сделки; остальные 34 ушли человеку или в отказ с причиной.

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

# Страховка снята: см. «ТОРМОЗ E9 СНЯТ» в docstring выше. Переменная оставлена,
# чтобы её можно было вернуть одной строкой, если поток изменится.
NEW_CARDS_NEED_REVIEW = False

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


def stem_frequency(idx):
    """Сколько заголовков базы содержат каждую основу — чтобы отличать
    различающее слово от общего. «разраб» стоит в 34 заголовках и не значит
    ничего, «персей» — ни в одном и значит всё."""
    df = {}
    for row in idx:
        for stem in row['stems']:
            df[stem] = df.get(stem, 0) + 1
    return df


def near_duplicate(draft, idx, df, rare=5):
    """Свежая карточка про то же самое — повод показать человеку, а не пустить.

    Пороги ниже, чем у `match.py`, и потому годятся только на «показать»:
      * общее название в кавычках при разнице дат до недели. На всей базе один
        общий кавычковый ключ — слабый признак (5 пар за три года, верна одна:
        банк «Траст» совпадает сам с собой). В пределах недели он сильный:
        ««Тантор Лабс» купил права на СУБД «Персей»» и «Создатель российского
        Linux купил полсотни разработчиков суверенной СУБД «Персей»» — это
        одна новость в двух изданиях;
      * два общих слова за месяц, но хотя бы одно из них — РЕДКОЕ. Без этого
        условия «Совладелец „Депо Три Вокзала" продал долю в разработчике» и
        «Владельцы ATI.SU купили разработчика» слипались по словам «владел» и
        «разраб», которые стоят в 25 и 34 заголовках базы и не значат ничего.
    """
    t_stems = matcher.stems(str(draft.get('title') or ''))
    t_quoted = matcher.quoted(str(draft.get('title') or ''))
    for row in idx:
        gap = matcher.days_between(draft.get('date'), row.get('date'))
        if gap <= 7 and matcher.quoted_common(t_quoted, row['quoted']):
            return row['id'], 'общее название в кавычках'
        common = t_stems & row['stems']
        if gap <= 30 and len(common) >= 2 and any(df.get(s, 0) <= rare for s in common):
            return row['id'], 'общие редкие слова: %s' % ', '.join(sorted(common))
    return None


def check(draft, base, idx, inds, df=None):
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
    # НЕИЗВЕСТНАЯ ОТРАСЛЬ — НЕ ПОВОД НЕ ПУСКАТЬ. Неделю это была причина
    # задержки номер один (21 черновик из 41), и держалась она на ложной
    # посылке: будто карточка без отрасли базе не годится. В `INDUSTRIES` есть
    # значение «Не определена», интерфейс его показывает — просто до сих пор им
    # не была помечена ни одна карточка из 1541. Отрасль дописывается позже
    # (профилем компании, обогащением, человеком), а сделка, которой на сайте
    # нет вовсе, не дописывается ничем. Выдумывать отрасль по аннотации мы при
    # этом не стали: замер на живом потоке дал 6 верных из 8 — ниже порога, за
    # которым ошибка дешевле молчания.
    if draft.get('ind') and draft['ind'] not in inds:
        bad.append('отрасль не из списка INDUSTRIES (%r)' % draft.get('ind'))
    if draft.get('sum') and WORD_CURRENCY.search(str(draft['sum'])):
        bad.append('валюта словом, а не значком')
    if draft.get('seller') and PLACEHOLDER.match(str(draft['seller']).strip()):
        bad.append('в продавце заглушка, а не имя')
    if draft.get('status') == 'Закрыта' and PRESENT_CLOSED.search(str(draft.get('title') or '')):
        hold.append('закрытая сделка названа настоящим временем — заголовок нужно привести к завершённому действию')
    # ТРЕБОВАТЬ ПОКУПАТЕЛЯ — ЗНАЧИТ ТРЕБОВАТЬ ОТ НОВОЙ КАРТОЧКИ БОЛЬШЕГО, ЧЕМ
    # ЕСТЬ У СТАРЫХ. В базе 431 карточка из 1541 (28%) не называет покупателя
    # вовсе — «UniCredit продаст часть российских активов банка инвестору из
    # ОАЭ», «Продажа аптечной сети „Апрель"», — и это нормальные карточки:
    # покупателя не назвал источник. Прежнее правило пропустило бы лишь 68%
    # нашей собственной базы. Сделка узнаётся по тому, что назван ПРЕДМЕТ и
    # хотя бы одна сторона; кто именно из сторон — вопрос того, что раскрыли,
    # а не нашей уверенности.
    #
    # ПРОВЕРКА РАСПРОСТРАНЕНА НА ВСЕ ТИПЫ, а не только на M&A. Раньше её
    # обходило всё, что разбор счёл размещением или инвестицией: «Shein
    # выплатит инвесторам не менее $1,1 млрд перед IPO» — это не сделка, но
    # слово IPO уводило запись мимо единственной проверки на содержание.
    named_side = (draft.get('buyer') or draft.get('buyer_name')
                  or draft.get('seller') or draft.get('seller_id'))
    if not (draft.get('target') or draft.get('asset_id') or draft.get('asset')):
        hold.append('не установлен предмет сделки — из заголовка не видно, что продают')
    elif not named_side:
        hold.append('не названа ни одна сторона — ни покупатель, ни продавец')
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
    else:
        # ПОЧТИ-ДУБЛЬ ОТДАЁМ ЧЕЛОВЕКУ, А НЕ ПУСКАЕМ. `match.py` объявляет дубль
        # по трём общим словам заголовка — порог выбран замером (два слова
        # уводили на чужую карточку в 6,1% случаев) и снижать его в самом
        # `match.py` нельзя. Но «отказать» и «показать человеку» — разные цены:
        # «Создатель российского Linux купил полсотни разработчиков суверенной
        # СУБД «Персей»» и вчерашняя ««Тантор Лабс» купил права на СУБД
        # «Персей»» — одна сделка в двух изданиях, и двух слов тут хватает,
        # если новость свежая. Ошибка стоит одного взгляда, а не карточки-дубля.
        near = near_duplicate(draft, idx, df or {})
        if near:
            hold.append('похоже на уже описанную сделку %s (%s) — проверьте, не дубль ли'
                        % near)
    if not bad and NEW_CARDS_NEED_REVIEW:
        hold.append('фильтр «это сделка» не проверен на живом потоке — ждёт подтверждения человека (см. E9)')
    return bad, hold


def confidence(draft):
    """Насколько мы уверены, что это сделка и что карточка полна.

    Заменяет глухой тормоз E9 осмысленной развилкой. Уверенность — не
    вероятность, а перечень того, что удалось установить: названа сторона,
    назван предмет, названа сумма, известна отрасль. Карточка, у которой всё
    это есть, спорной не бывает — «Ригла приобрела аптечную сеть „Здоровый
    город"» не требует человека. Карточка без сторон («Кто и почему продаёт
    ПВЗ Wildberries») требует всегда.
    """
    have = []
    if draft.get('buyer') or draft.get('buyer_name'):
        have.append('покупатель')
    if draft.get('seller') or draft.get('seller_id'):
        have.append('продавец')
    if draft.get('target') or draft.get('asset_id') or draft.get('asset'):
        have.append('предмет')
    if draft.get('ind'):
        have.append('отрасль')
    if draft.get('sum'):
        have.append('сумма')
    return have


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
        # «Не определена» — законное значение списка INDUSTRIES и честная
        # подпись на экране: лучше показать сделку без отрасли, чем приписать
        # ей чужую (см. развёрнутый разбор в `check`).
        'ind': draft.get('ind') or 'Не определена',
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

    # ДУБЛИ ИЩУТСЯ И ВНУТРИ ОДНОЙ ПАРТИИ, а не только против базы. Об одной
    # сделке за сутки пишут несколько изданий: 4 августа про покупку СУБД
    # «Персей» пришли три заголовка («Тантор Лабс купил права…», «Создатель
    # российского Linux купил полсотни разработчиков…», «Группа Астра купила
    # права…»), и все три прошли ворота — потому что ни одного из них ещё не
    # было в базе, а друг с другом их никто не сверял. Пустив их, мы завели бы
    # три карточки на одну сделку в первый же рабочий день. Поэтому прошедшая
    # карточка сразу попадает в индекс, и следующая сверяется уже с ней.
    passed, refused, held = [], [], []
    admitted, batch_names = [], []
    for draft in drafts:
        bad, hold = check(draft, data, idx, inds, stem_frequency(idx))
        if bad:
            refused.append((draft, bad))
        elif hold:
            held.append((draft, hold))
        else:
            # Внутри одной партии общего названия в кавычках ДОСТАТОЧНО, чтобы
            # заподозрить одну сделку. `match.py` этого не признаёт и правильно
            # делает: на трёхлетней базе «Лента» встречается у десятков карточек,
            # и одного общего имени мало. Но в пределах одних суток два
            # заголовка про «Персей» — это одна новость в двух изданиях, а не
            # две сделки. Первый проходит, остальные ждут человека: выбрать
            # формулировку — его дело, а не наше.
            same = [t for t, names in batch_names
                    if matcher.quoted_common(matcher.quoted(draft.get('title')), names)]
            if same:
                held.append((draft, ['в этой же партии уже есть карточка про то же название: «%s» — '
                                     'скорее всего, одна сделка в двух изданиях' % str(same[0])[:60]]))
                continue
            passed.append((draft, []))
            batch_names.append((draft.get('title'), matcher.quoted(draft.get('title'))))
            admitted.append(dict(draft, id='pending-%d' % len(passed)))
            idx = matcher.index_base(data['deals'] + admitted,
                                     data.get('companies'), data.get('match_keys'))

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
        # ПРИЧИНА ЛОЖИТСЯ В ФАЙЛ ВМЕСТЕ С ЧЕРНОВИКОМ. Раньше в очередь падал
        # только черновик, а причина оставалась в выводе прогона — а прогон
        # идёт в одноразовом контейнере, и вывод человек не увидит никогда.
        # Открыв очередь, он видел карточки без единого слова о том, чего им
        # не хватает, и должен был выводить это заново сам.
        json.dump({'made': day,
                   'drafts': [dict(d, hold_reasons=reasons) for d, reasons in held]},
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
