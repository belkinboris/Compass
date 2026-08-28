# -*- coding: utf-8 -*-
"""Разбор постов @LawFirms: что это за сделка и чем она дополняет базу.

ЗАЧЕМ ИМЕННО ТАК. Сопоставление даже после починки узнаёт половину: на
выверенной вручную десятке — 5 совпадений из 10 (было 2). Значит, решать
«новая или дубль» автоматом нельзя. Но и не нужно: человеку достаточно
увидеть пост рядом с похожими карточками и списком того, чего в них не
хватает, — решение занимает секунды.

ГЛАВНОЕ, ЧТО ЗДЕСЬ ЕСТЬ. «Дубль» — не значит «пропустить». Замечание
владельца: если карточка уже есть, в ней запросто может не быть того, что
знает пост, — суммы, второй стороны, консультанта, даты закрытия. Поэтому
для каждого кандидата считается ЧТО ПОСТ МОЖЕТ ДОБАВИТЬ: поля, которые в
посте есть, а в карточке пусты. Именно так вчера нашлись Nextons и White
Square — карточки были, а половины фактов в них не было.

КАНДИДАТЫ, А НЕ ВЕРДИКТ. Показываются и слабые совпадения тоже, с явной
пометкой силы сигнала. Слабый сигнал нельзя пускать в автозапись (проверено:
объявление BIRCH о золотодобыче связалось с карточкой про девелопмент), но
показать человеку — можно и нужно: он отличит за секунду.

Запуск:
    python3 pipeline/review_lawfirms.py                  # объявления о консультантах
    python3 pipeline/review_lawfirms.py --all            # все посты, похожие на сделки
    python3 pipeline/review_lawfirms.py --limit 15       # размер партии
    python3 pipeline/review_lawfirms.py --year 2024      # только за год
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))

import advisors                # noqa: E402
import classify                # noqa: E402
import draft                   # noqa: E402
import enrich                  # noqa: E402
import match as matcher        # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
ARCHIVE = os.path.join(ROOT, 'data', 'inbox', 'raw', 'lawfirms_archive.jsonl')
SINCE = '2022-01-01'


def has(value):
    """Заполнено ли поле. Заглушка («не раскрыта», «—») — это пустота."""
    text = str(value or '').strip().lower()
    if not text or text in ('—', '-', 'н/д'):
        return False
    return not text.startswith(('не раскры', 'не привлекал', 'публично не', 'не сообщал'))


# Все подписанные поля карточки, кроме заголовка и даты. Список полный
# намеренно: разбор сначала проверял шесть полей, и «дополнять нечем» у
# найденной карточки означало лишь «нечем из этих шести». Замечание владельца
# — «не факт же, что в дубле есть вся информация, которая есть в посте» —
# верно ровно потому, что проверка была уже, чем карточка.
FIELDS = [
    ('sum', 'сумма'),
    ('eco.share', 'предмет / доля'),
    ('eco.val', 'оценка и дисконт'),
    ('eco.target_fin', 'финансы предмета'),
    ('eco.fin', 'финансирование'),
    ('eco.rationale', 'цель сделки'),
    ('eco.context', 'контекст'),
    ('eco.finadv', 'финансовый консультант'),
    ('law.struct', 'структура сделки'),
    ('law.appr', 'согласования'),
    ('law.terms', 'условия'),
    ('extra', 'дополнительная информация'),
]


def field(deal, path):
    node = deal
    for part in path.split('.'):
        node = (node or {}).get(part)
    return node


def gaps(deal, post_text, found_adv):
    """Что пост может дать карточке: поля, которые у неё пусты, а в посте есть.

    Ничего не записывает — только показывает. Решение за человеком: пост
    может называть сумму ДРУГОЙ сделки (известный класс ошибки, см. CLAUDE.md
    про «ВТБ продал Holiday Inn»), и такое ловится только чтением.

    Возвращает две части. Первая — то, что разбор сумел ВЫТАЩИТЬ из поста
    (сумма, стороны, статус, консультант): здесь есть что показать рядом с
    названием поля. Вторая — просто перечень пустых полей карточки: правило
    их не заполняет, но человек, читающий пост, видит, куда смотреть. Вторая
    часть не менее важна первой: правил у нас мало, а глаз есть на каждый
    разбираемый пост.
    """
    out = []
    eco, law = deal.get('eco') or {}, deal.get('law') or {}

    if not has(deal.get('sum')) and not has(eco.get('sum')):
        guess = draft.guess_sum(post_text)
        if guess:
            out.append(('сумма', guess))
    if found_adv:
        known = ' '.join(str(a[1]) for a in (law.get('adv') or []) if len(a) > 1).lower()
        new = [f for f in found_adv[0] if f.lower() not in known]
        if new:
            out.append(('консультант', ', '.join(new)))
    buyer, asset, seller, _ = draft.guess_parties(post_text[:200])
    if seller and not (deal.get('seller') or deal.get('seller_id')):
        out.append(('продавец', seller))
    if buyer and not (deal.get('buyer') or deal.get('buyer_name')):
        out.append(('покупатель', buyer))
    status = draft.guess_status(post_text)
    if status and enrich.STATUS_RANK.get(status, -1) > enrich.STATUS_RANK.get(deal.get('status'), -1):
        out.append(('статус', '%s -> %s' % (deal.get('status'), status)))
    return out


def empty_fields(deal):
    """Пустые поля карточки — куда смотреть в посте глазами."""
    out = []
    for path, label in FIELDS:
        # Сумма живёт в двух местах: заполненного `eco.sum` достаточно.
        if path == 'sum' and has((deal.get('eco') or {}).get('sum')):
            continue
        if not has(field(deal, path)):
            out.append(label)
    adv = (deal.get('law') or {}).get('adv') or []
    # Строка «Не раскрывались» — не консультант, а заглушка: у карточки
    # «Лента»/«РБФ ритейл» она стояла ровно там, где объявление NEXTONS
    # называет фирму по имени.
    if not [a for a in adv if len(a) > 1 and has(a[1])]:
        out.append('консультанты')
    return out


# Пресс-релиз — это ДВА текста, склеенных вместе: сама сделка и реклама
# фирмы, а реклама называет ДРУГИХ клиентов и ДРУГИЕ сделки. У объявления
# White Square про Nordgold в подвале стоят «Восток Инвестиции», «Каллисто»
# и Tasty Coffee — по всему тексту карточка Nordgold не попадала даже в
# пятёрку ближайших, по голове занимала первое место. Замер на 91
# объявлении: голова 300 знаков — 20 значащих слов и 1,3 названия в
# кавычках, весь текст — 79 слов и 2,0 названия, то есть половина сигнала
# приходит из рекламного подвала. Сопоставлять по всему посту — значит
# сопоставлять по списку клиентов фирмы.
HEAD = 300


def nearest(body, idx, top=3):
    """Ближайшие карточки — НЕЗАВИСИМО от порога `match.py`.

    Порог существует, чтобы не писать в базу по слабому признаку, и это
    правильно. Но человеку он мешает: карточка «Совкомбанк купил 100% долей
    ООО «Капитал Медицинское Страхование»» есть в базе, а объявление
    Delcredere о продаже «Капитал МС» её не достаёт — сокращение против
    полного имени. Показать три ближайших дешевле, чем пропустить дубль.
    """
    body = body[:HEAD]
    t_stems, t_quoted = matcher.stems(body), matcher.quoted(body)
    # Редкое слово различает сильнее частого: «nordgo» встречается в базе
    # трижды, «россий» — в сотнях. Без веса карточка Nordgold не попадала в
    # тройку, потому что её обходили сделки с двумя общими общеупотребимыми
    # словами. Вес — обратная частота по базе, считается один раз.
    freq = {}
    for row in idx:
        for st in row['stems']:
            freq[st] = freq.get(st, 0) + 1
    scored = []
    for row in idx:
        common = t_stems & row['stems']
        weight = sum(1.0 + 4.0 / max(freq.get(st, 1), 1) for st in common)
        # Название в кавычках стоит дороже любого слова, и это замер, а не
        # вкус: у `match.py` сигнал «название в кавычках» ведёт на чужую
        # карточку в 0,7% случаев, «общие слова заголовка» — в 6,1%. Вес 8
        # выбран так, чтобы одно общее название перевешивало самое редкое
        # одиночное слово (его потолок — 5,0). Без этого карточка «ООО
        # «Земун» получила 99% «РБФ ритейл»» не попадала в тройку к
        # объявлению NEXTONS о «Ленте» и «РБФ-Ритейл» — при ДВУХ общих
        # названиях её обходили карточки с одним случайным редким словом.
        shared = matcher.quoted_common(t_quoted, row['quoted'])
        score = weight + 8 * len(shared)
        if score:
            scored.append((round(score, 1), len(common), sorted(shared), row))
    scored.sort(key=lambda x: -x[0])
    return scored[:top]


def main(argv):
    only_adv = '--all' not in argv
    limit = int(argv[argv.index('--limit') + 1]) if '--limit' in argv else 15
    year = argv[argv.index('--year') + 1] if '--year' in argv else None

    base = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in base['deals']}
    idx = matcher.index_base(base['deals'], base.get('companies'), base.get('match_keys'))

    rows = [json.loads(l) for l in open(ARCHIVE, encoding='utf-8') if l.strip()]
    rows = [r for r in rows if r.get('text') and (r.get('date') or '') >= SINCE]
    if year:
        rows = [r for r in rows if str(r.get('date') or '').startswith(year)]

    queue = []
    for row in rows:
        text = row['text']
        found = advisors.lead_advisor(text)
        if only_adv and not found:
            continue
        if not classify.looks_like_deal(text[:200], text[:600]):
            continue
        queue.append((row, found))
    queue.sort(key=lambda x: x[0]['date'], reverse=True)

    print('постов к разбору: %d (показываю %d)\n' % (len(queue), min(limit, len(queue))))
    new_cnt = enrich_cnt = 0
    for i, (row, found) in enumerate(queue[:limit], 1):
        body = advisors.deal_text(row['text'])
        deal_id, why = matcher.match(
            {'title': body[:200], 'summary': body[:600], 'url': row['url'], 'date': row['date']}, idx)
        print('=' * 78)
        print('%d. %s  %s' % (i, row['date'], row['url']))
        print('   %s' % row['text'][:190].replace('\n', ' '))
        if found:
            print('   ФИРМА: %s — %s' % (' + '.join(found[0]), found[1]))
        if deal_id:
            enrich_cnt += 1
            deal = by_id[deal_id]
            strength = 'СИЛЬНОЕ' if enrich.is_strong(why) else 'слабое'
            print('   -> ЕСТЬ В БАЗЕ [%s: %s]' % (strength, why))
            print('      %s  (%s)' % ((deal.get('title') or '')[:66], deal_id))
            missing = gaps(deal, row['text'], found)
            if missing:
                print('      ЧЕМ ДОПОЛНИТЬ (вытащено правилом):')
                for name, value in missing:
                    print('        · %-12s %s' % (name, str(value)[:74]))
            blank = empty_fields(deal)
            if blank:
                # Пустые поля печатаются ВСЕГДА, даже когда правило ничего не
                # вытащило: «дополнять нечем» раньше значило «нечем из шести
                # полей», и пост с описанием структуры проходил мимо карточки,
                # у которой это поле пусто.
                print('      ПУСТО В КАРТОЧКЕ — искать в посте глазами:')
                print('        %s' % ', '.join(blank))
            elif not missing:
                print('      дополнять нечем — все поля карточки заполнены')
        else:
            new_cnt += 1
            print('   -> порог сопоставления не сработал. Отрасль: %s | тип: %s | сумма: %s'
                  % (draft.industry_for(row['text'][:200], base['companies']) or '—',
                     draft.guess_type(row['text'][:600]), draft.guess_sum(row['text'][:600]) or '—'))
            close = nearest(body, idx)
            if close:
                print('      БЛИЖАЙШИЕ КАРТОЧКИ — проверьте, нет ли среди них этой сделки:')
                for score, common, shared, cand in close:
                    print('        [%4s] %s  (%s, %s)'
                          % (score, (cand.get('title') or '')[:62], cand['id'], cand.get('date')))
                    if shared:
                        print('             общее название: %s' % ', '.join(shared))
                    missing = gaps(by_id[cand['id']], row['text'], found)
                    if missing:
                        # «Если это она» — не вежливость, а точность: список
                        # пустых полей одинаков у любой карточки без
                        # консультантов, и без условия строка читалась бы как
                        # утверждение, что White Square вела сделку Fort Ross.
                        print('             если это она — дополнить: %s'
                              % ', '.join('%s (%s)' % (f, str(v)[:28]) for f, v in missing[:3]))
            else:
                print('      похожих карточек нет — скорее всего, новая сделка')
    print('=' * 78)
    print('в партии: дополнить существующие — %d, кандидатов в новые — %d' % (enrich_cnt, new_cnt))
    print('\nНичего не записано: это разбор для чтения. Решение — за человеком.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
