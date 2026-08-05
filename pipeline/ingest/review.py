# -*- coding: utf-8 -*-
"""Приток, шаг 5: проверка карточки чтением — и перенос найденного в поля.

ЗАЧЕМ ЭТОТ ШАГ ВООБЩЕ ПОЯВИЛСЯ. Правила разбора слепы ровно к тому, чего в них
не написали, и слепы молча. За два дня так нашлись: `рудник`, совпадающий
внутри слова «сотрудники»; `\\bкуп…`, не видящий слова «покупает»; действие,
названное существительным («закрыла сделку по покупке»). Каждый раз замер
выглядел законченным, и каждый раз дефект находился не проверкой кода, а
чтением живых данных. Перечислить такие ошибки заранее нельзя — их можно
только вычитывать.

Поэтому после `promote.py` карточку читает человек (в рутине — модель) и
сверяет КАЖДОЕ поле с текстом источника. Замер первого прогона: из 13 карточек,
которые приток добавил сам, поправить было что у 9. Самое опасное найденное —
не пустые поля, а МОЛЧАЛИВО НЕВЕРНЫЕ: у «Дом.РФ» датой стояло 3 августа, хотя
в источнике «сделка была закрыта 4 мая»; у Visa стоял статус «Закрыта», хотя
в источнике «объявила о приобретении», а сумма — «составит».

ГРАНИЦА, КОТОРАЯ ДЕЛАЕТ ЭТО БЕЗОПАСНЫМ. Читающий не «формулирует» и не
«уточняет» — он ПЕРЕНОСИТ. Каждая правка несёт с собой дословную цитату из
источника, и скрипт механически проверяет, что записываемое значение из этой
цитаты выводимо:
  * имя стороны, предмет, сумма — нормализованная подстрока цитаты;
  * дата — день и месяц названы в цитате прописью, год не меняется (менять год
    значит утверждать новое, а не уточнять известное);
  * отрасль — либо слово нашего же словаря стоит в цитате, либо в цитате стоит
    имя компании, у профиля которой в базе эта отрасль;
  * статус — в цитате есть слово, которым этот статус подтверждается.
Плюс, пока сырьё за день лежит на диске, цитата сверяется с НАСТОЯЩИМ текстом
источника, а не только с таблицей. Соврать в таблице так, чтобы скрипт этого
не заметил, нельзя — можно только не заметить дефект.

ЧЕМ ЭТО ОТЛИЧАЕТСЯ ОТ АВТОМАТИЧЕСКОГО ПРАВИЛА. Тем же, чем «прочитать» от
«угадать». Падежный поиск профиля отрасли (имя с точностью до окончания) как
АВТОМАТИЧЕСКОЕ правило измерен на 1541 карточке и отвергнут: +42 попадания и
+43 ошибки. Здесь он допустим — но только как подтверждение решения, которое
читающий уже принял по тексту, и только на одну карточку, а не на всю базу.

Запуск:
    python3 pipeline/ingest/review.py            # сухой прогон
    python3 pipeline/ingest/review.py --write    # записать
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import draft as drafter                                   # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
INDEX = os.path.join(ROOT, 'static', 'index.html')
RAW = os.path.join(ROOT, 'data', 'inbox', 'raw')
TRIAGE = os.path.join(ROOT, 'data', 'inbox', 'triage')

MONTHS = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
          'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11,
          'декабря': 12}

# Слово, которым подтверждается статус. Список закрытый: статус — единственное
# поле, которое не цитируется дословно, поэтому обоснование должно быть
# перечислимым, а не «на усмотрение».
STATUS_WORDS = {
    'Обсуждается': ('переговор', 'рассматрива', 'обсужда', 'изучает', 'намерен', 'планирует'),
    'Подписана': ('объявил', 'подписал', 'заключил', 'договорил', 'соглашени'),
    'Согласование получено': ('одобрил', 'согласовал', 'разрешил', 'предписани'),
    'Закрыта': ('закрыл', 'заверш', 'купил', 'приобрел', 'приобрёл', 'продал',
                'выкупил', 'привлек', 'привлёк', 'стал владельцем', 'перешл', 'перешёл'),
    'Не состоялась': ('не состоял', 'отказал', 'прекращен', 'отменен', 'отменён'),
}

# ---------------------------------------------------------------------------
# Правки к gd057d2c1 (Visa/BioCatch) и g4a10e7a2 (Smallest.ai) сняты вместе с
# самими карточками: 5 августа владелец решил не держать в базе сделки без
# российской стороны, и обе удалены `pipeline/remove_out_of_scope_deals.py`.
# Правка к карточке, которой нет, — это отказ на каждом прогоне.
#
# ТАБЛИЦА ПРАВОК. Прогон 5 августа 2026: 13 карточек, которые приток добавил
# сам, прочитаны против текста источника. `quote` — дословный кусок источника,
# `why` — что именно правило не увидело и почему.
FIXES = [
    dict(id='gdfce7e3d', field='seller', old=None, new='Business Club',
         quote='Продавцом актива выступала сеть сервисных офисов Business Club.',
         why='продавец назван в аннотации, а разбор читает только заголовок'),
    dict(id='gdfce7e3d', field='date', old='2026-08-03', new='2026-05-04',
         quote='Как следует из выписки Росреестра, сделка была закрыта 4 мая.',
         why='датой стояла дата НОВОСТИ, а сделка закрыта тремя месяцами раньше'),

    dict(id='gfa114edc', field='seller', old=None, new='МТ-Интеграция',
         quote='закрыла сделку по выкупу исключительных прав на отечественную '
               'СУБД «Персей» у компании МТ-Интеграция (ранее Максима)',
         why='продавец назван в аннотации, а разбор читает только заголовок'),

    dict(id='gf70a43e6', field='buyer_name', old=None, new='Dr. Reddy’s',
         quote='Российская «дочка» индийской фармкомпании Dr. Reddy’s получила '
               'от «Вертекса» права на три гинекологических препарата.',
         why='покупатель стоял ВНУТРИ предмета сделки — тот же класс, что '
             '«стороной сделки записан её предмет», только зеркальный'),
    dict(id='gf70a43e6', field='asset', old='Dr. Reddy’s права на три гинекологических препарата',
         new='права на три гинекологических препарата',
         quote='Российская «дочка» индийской фармкомпании Dr. Reddy’s получила '
               'от «Вертекса» права на три гинекологических препарата.',
         why='из предмета убран покупатель'),

    dict(id='gbf6f6432', field='seller', old='Экс-акционер Башкирской содовой компании',
         new='Сергей Черников',
         quote='приобрела производителя пищевой упаковки «Полекс», где долей '
               'владел экс-акционер Башкирской содовой компании Сергей Черников',
         why='в поле стояло описание из заголовка, а имя названо в аннотации'),
    dict(id='gbf6f6432', field='asset', old='производство упаковки', new='«Полекс»',
         quote='приобрела производителя пищевой упаковки «Полекс»',
         why='предмет назывался родовым словом, хотя имя есть в аннотации'),

    dict(id='g97e1f483', field='date', old='2026-08-03', new='2026-07-30',
         quote='В результате сделки, зарегистрированной 30 июля, были приобретены '
               'три юридических лица',
         why='датой стояла дата новости, а сделка зарегистрирована 30 июля'),
    dict(id='g97e1f483', field='ind', old='Не определена', new='Фармацевтика',
         quote='были приобретены три юридических лица, включающих 55 аптек в Воронеже',
         why='отрасль видна по слову «аптек», но оно стоит в аннотации, а не в заголовке'),

    dict(id='g70e51ff1', field='ind', old='Не определена', new='Нефть и газ',
         quote='JPMorgan продал акции «Роснефти»',
         why='отрасль предмета известна из профиля «Роснефть» в нашей же базе'),

    # Прогон 5 августа, вторая партия: «Полекс». Материал упаковки и покупатель
    # названы во ВТОРОМ источнике — «Коммерсантъ» пишет «производителя пищевой
    # упаковки», и по этим словам отрасль читается как «Пищепром», хотя упаковка
    # для еды это не производство еды. mergers.ru называет материал прямо.
    dict(id='gbf6f6432', field='src', old=None,
         new=['mergers.ru', 'https://mergers.ru/news/Investicionnaya-kompaniya-Stroma-'
                            'priobrela-proizvoditelya-upakovki-Poleks-87305'],
         quote='«Полекс Урал» создан в 2002 году, выпускает в Уфе пластиковую упаковку, '
               'в первую очередь для молочной продукции.',
         why='вторая статья о той же сделке называет и покупателя, и материал упаковки'),
    dict(id='gbf6f6432', field='buyer_name', old=None, new='«Строма»',
         quote='Инвестиционная компания «Строма» приобрела производителя упаковки «Полекс»',
         why='покупатель назван в заголовке второго источника'),
    dict(id='gbf6f6432', field='ind', old='Не определена', new='Химия и удобрения',
         quote='«Полекс Урал» создан в 2002 году, выпускает в Уфе пластиковую упаковку',
         why='по пластику в базе два прецедента и оба «Химия и удобрения»: переработка '
             'пластика у «Технониколь» и БОПП-плёнка Manucor'),

    dict(id='g94617d17', field='ind', old='Не определена', new='Недвижимость',
         quote='внесла в прогнозный план приватизации муниципального имущества на '
               '2026 год и плановый период 2027 и 2028 годов шесть помещений и '
               'три земельных участка',
         why='отрасль видна по словам «земельных участка», они стоят в аннотации'),
]


def flat(s):
    return re.sub(r'[^\wа-яё]+', '', str(s or ''), flags=re.I).lower()


def industries():
    html = open(INDEX, encoding='utf-8').read()
    raw = re.search(r'const INDUSTRIES\s*=\s*\[(.*?)\]', html, re.S).group(1)
    return {x.strip().strip('"') for x in raw.split(',') if x.strip()}


def source_texts():
    """Настоящие тексты источников за все дни, что ещё лежат на диске."""
    texts = []
    for folder, load in ((RAW, 'jsonl'), (TRIAGE, 'json')):
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            try:
                if load == 'jsonl' and name.endswith('.jsonl'):
                    for line in open(path, encoding='utf-8'):
                        rec = json.loads(line)
                        texts.append(' '.join(str(rec.get(k) or '') for k in ('title', 'summary')))
                elif load == 'json' and name.endswith('.json'):
                    for rec in json.load(open(path, encoding='utf-8')).get('items', []):
                        texts.append(' '.join(str(rec.get(k) or '') for k in ('title', 'summary')))
            except (ValueError, OSError):
                continue
    return [re.sub(r'\s+', ' ', t) for t in texts if t.strip()]


def quote_is_real(quote, texts):
    """Цитата обязана дословно лежать в тексте источника — пока он есть на диске."""
    needle = flat(quote)
    return any(needle in flat(t) for t in texts)


def date_is_supported(old, new, quote):
    """Дату можно уточнить внутри известного года, но не перенести в другой.

    Менять год — значит утверждать новое; тот же порог, что у
    `fix_placeholder_dates.py`. День и месяц обязаны быть названы в цитате
    прописью («закрыта 4 мая»), иначе это не перенос, а догадка.
    """
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(new or '')):
        return 'новая дата не в формате ГГГГ-ММ-ДД'
    if str(old or '')[:4] != new[:4]:
        return 'год не совпадает: уточнять день можно, переносить год — нет'
    day, month = int(new[8:10]), int(new[5:7])
    for word, num in MONTHS.items():
        if num == month and re.search(r'(?<!\d)%d\s+%s' % (day, word), quote, re.I):
            return None
    return 'в цитате нет «%d %s»' % (day, [w for w, n in MONTHS.items() if n == month][0])


def industry_is_supported(new, quote, companies, inds):
    """Отрасль — либо слово нашего словаря, либо профиль компании из цитаты."""
    if new not in inds:
        return 'отрасли %r нет в списке INDUSTRIES' % new
    if drafter.industry_by_words(quote) == new:
        return None
    # Профиль компании: имя ищется с падежным окончанием. Как АВТОМАТИЧЕСКОЕ
    # правило это измерено и отвергнуто (+42 попадания, +43 ошибки на 1541
    # карточке); здесь оно лишь подтверждает решение, уже принятое по тексту.
    for comp in companies.values():
        core = re.sub(r'^(ООО|АО|ПАО|ЗАО|ГК|МКООО)\s+', '', str(comp.get('name') or '')).strip('«» "')
        if len(core) < 5 or comp.get('ind') != new:
            continue
        stem = core[:-1]
        if re.search(r'(?<![\wа-яё])%s[а-яё]{0,3}(?![\wа-яё])' % re.escape(stem), quote, re.I):
            return None
    return 'ни слово словаря, ни профиль компании из цитаты не дают «%s»' % new


def source_urls():
    """Адреса, которые приток действительно забирал: приложить можно только их."""
    urls = set()
    if os.path.isdir(RAW):
        for name in sorted(os.listdir(RAW)):
            if not name.endswith('.jsonl'):
                continue
            for line in open(os.path.join(RAW, name), encoding='utf-8'):
                try:
                    url = json.loads(line).get('url')
                except ValueError:
                    continue
                if url:
                    urls.add(str(url))
    return urls


def already_applied(fix, card):
    """Правка уже в базе — прогон должен быть идемпотентным, а не падать."""
    if fix['field'] == 'src':
        return any(len(s) > 1 and s[1] == fix['new'][1] for s in card.get('src') or [])
    return card.get(fix['field']) == fix['new']


def check(fix, card, texts, companies, inds, urls=frozenset()):
    """Список причин, по которым правку принимать НЕЛЬЗЯ."""
    bad = []
    field, new, quote = fix['field'], fix['new'], fix['quote']
    if field == 'src':
        # ВТОРОЙ ИСТОЧНИК — НЕ УКРАШЕНИЕ. Об одной сделке пишут несколько
        # изданий, и факт нередко есть только у одного: материал упаковки
        # «Полекса» назван у mergers.ru и не назван у «Коммерсанта». Приложить
        # можно только адрес, который приток РЕАЛЬНО забирал, — иначе ссылка
        # берётся из головы, а это ровно то, чего мы избегаем.
        if not (isinstance(new, list) and len(new) == 2 and str(new[1]).startswith('http')):
            bad.append('источник должен быть парой [имя, http-адрес]')
        elif urls and new[1] not in urls:
            bad.append('такого адреса нет среди забранных источником записей')
        if texts and not quote_is_real(quote, texts):
            bad.append('цитаты нет в тексте источника')
        return bad
    if card.get(field) != fix['old']:
        bad.append('поле уже другое: в базе %r, ожидали %r' % (card.get(field), fix['old']))
    if texts and not quote_is_real(quote, texts):
        bad.append('цитаты нет в тексте источника')
    if field == 'date':
        problem = date_is_supported(fix['old'], new, quote)
        if problem:
            bad.append(problem)
    elif field == 'ind':
        problem = industry_is_supported(new, quote, companies, inds)
        if problem:
            bad.append(problem)
    elif field == 'status':
        if new not in STATUS_WORDS:
            bad.append('неизвестный статус %r' % new)
        elif not any(w in quote.lower() for w in STATUS_WORDS[new]):
            bad.append('в цитате нет слова, подтверждающего статус «%s»' % new)
    elif new is not None:
        # Имя, предмет, сумма — только перенос, дословно.
        if flat(new) not in flat(quote):
            bad.append('значение не лежит в цитате дословно')
    return bad


def _self_check():
    """Правила проверяются на себе — иначе они молча пропустят выдумку."""
    # Дословность: подмена одного слова правило НЕ проходит.
    q = 'Продавцом актива выступала сеть сервисных офисов Business Club.'
    assert flat('Business Club') in flat(q)
    assert flat('Business Centre') not in flat(q)
    # Дата: день и месяц обязаны быть в цитате, год менять нельзя.
    assert date_is_supported('2026-08-03', '2026-05-04', 'сделка была закрыта 4 мая') is None
    assert date_is_supported('2026-08-03', '2026-05-05', 'сделка была закрыта 4 мая')
    assert date_is_supported('2026-08-03', '2025-05-04', 'сделка была закрыта 4 мая')
    # Статус: слово-подтверждение обязательно.
    assert any(w in 'visa объявила о приобретении' for w in STATUS_WORDS['Подписана'])
    assert not any(w in 'visa объявила о приобретении' for w in STATUS_WORDS['Не состоялась'])


def main(write=False):
    _self_check()
    data = json.load(open(DATA, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    inds, texts = industries(), source_texts()
    print('Правок в таблице: %d | текстов источников на диске: %d'
          % (len(FIXES), len(texts)))
    if not texts:
        print('ВНИМАНИЕ: сырья на диске нет — цитаты сверить не с чем, проверяется')
        print('только состояние полей. Это ослабленная проверка, а не полная.')

    urls = source_urls()
    ok, refused, done = [], [], 0
    for fix in FIXES:
        card = cards.get(fix['id'])
        if not card:
            refused.append((fix, ['карточки %s нет в базе' % fix['id']]))
            continue
        if already_applied(fix, card):
            done += 1
            continue
        bad = check(fix, card, texts, data['companies'], inds, urls)
        (refused if bad else ok).append((fix, bad))

    if done:
        print('  уже применено раньше: %d' % done)
    for fix, _ in ok:
        print('  ПРАВИМ   %s %-11s %r -> %r' % (fix['id'], fix['field'],
                                                str(fix['old'])[:34], str(fix['new'])[:40]))
        print('           %s' % fix['why'])
    for fix, bad in refused:
        print('  ОТКАЗ    %s %-11s %s' % (fix['id'], fix['field'], '; '.join(bad)))

    print('\nпринято %d, отклонено %d' % (len(ok), len(refused)))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1 if refused else 0
    if refused:
        print('Есть отклонённые правки — не пишем НИЧЕГО: таблицу надо починить целиком.')
        return 1

    for fix, _ in ok:
        card = cards[fix['id']]
        if fix['field'] == 'src':
            card.setdefault('src', []).append(list(fix['new']))
            continue
        assert card.get(fix['field']) == fix['old'], 'состояние поля изменилось'
        if fix['new'] is None:
            card.pop(fix['field'], None)
        else:
            card[fix['field']] = fix['new']
        # Свидетельство о стороне обязано указывать на то, что теперь в поле,
        # иначе на карточке останется ссылка на снятое значение.
        role = {'buyer_name': 'buyer', 'asset': 'target', 'seller': 'seller'}.get(fix['field'])
        if role and card.get('party_evidence'):
            if fix['new'] is None:
                card['party_evidence'].pop(role, None)
            else:
                url = next((s[1] for s in card.get('src') or []
                            if len(s) > 1 and str(s[1]).startswith('http')), None)
                card['party_evidence'][role] = [{'value': fix['new'], 'field': fix['field'],
                                                 'method': 'human_review', 'url': url}]
            if not card['party_evidence']:
                card.pop('party_evidence')
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: %d правок в %s' % (len(ok), os.path.relpath(DATA, ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
