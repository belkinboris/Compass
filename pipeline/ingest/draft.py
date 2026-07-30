# -*- coding: utf-8 -*-
"""Приток, шаг 3: собрать из новости ЧЕРНОВИК карточки.

ЗАЧЕМ. Между «это сделка» и «в базе появилась карточка» лежит разбор: сумма,
стороны, тип, статус. Если разбирать вручную, приток не масштабируется; если
разбирать доверчиво, база наполнится быстро и неверно — ровно то, что двадцать
прогонов исправляли. Поэтому черновик собирается правилами, а всё, что правило
не смогло подтвердить, остаётся ПУСТЫМ: пустое поле честнее правдоподобного.

ГЛАВНЫЙ ИНВАРИАНТ. Любое имя стороны обязано дословно лежать в тексте новости
(с точностью до окончаний — та же проверка падежа, что в прогонах 34–45).
Скрипт не «формулирует» и не «уточняет»: он переносит.

КАК ИЗМЕРЕНО. `--measure` собирает черновик из ЗАГОЛОВКА каждой карточки базы и
сравнивает с тем, что в этой карточке уже выверено людьми. Это честный замер
качества разбора: мы знаем правильный ответ по 1333 сделкам. Для каждого поля
считаются три числа: сколько раз правило промолчало, сколько раз попало и
сколько раз ошиблось. Ошибка дороже молчания, поэтому пороги правил выбраны в
сторону молчания.

ЧЕГО ЗДЕСЬ НЕТ. Записи в базу: черновик кладётся в `data/inbox/drafts/`, а
переносит его в базу отдельный шаг с проверками (`promote.py`, следующий шаг
работы).

Запуск:
    python3 pipeline/ingest/draft.py --measure       # замер на своей базе
    python3 pipeline/ingest/draft.py                 # собрать черновики из разбора
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
TRIAGE = os.path.join(ROOT, 'data', 'inbox', 'triage')
DRAFTS = os.path.join(ROOT, 'data', 'inbox', 'drafts')

WORD = re.compile(r"[\w%.,-]+", re.U)

# --- сумма -----------------------------------------------------------------
# Формат один на всю базу (CLAUDE.md): значок валюты, а не слово.
CUR = [(r'руб(?:л(?:ей|я|ь))?\.?|₽|rub', '₽'), (r'долл(?:ар(?:ов|а))?\.?|\$|usd', '$'),
       (r'евро|€|eur', '€')]
SUM_RE = re.compile(
    r'(?<![\w])(\d[\d\s]*(?:[.,]\d+)?)\s*(млрд|млн|тыс)\.?\s*'
    r'(руб(?:л(?:ей|я|ь))?\.?|₽|долл(?:ар(?:ов|а))?\.?|\$|евро|€)', re.I)
SUM_RE_PRE = re.compile(
    r'([$€])\s?(\d[\d\s]*(?:[.,]\d+)?)\s*(млрд|млн|тыс)', re.I)


def guess_sum(text):
    """«12 млрд рублей» -> «12 млрд ₽»; «$230 млн» -> «$230 млн». Иначе None."""
    text = str(text or '')
    m = SUM_RE.search(text)
    if m:
        num, scale, cur = m.group(1).strip(), m.group(2).lower(), m.group(3).lower()
        sign = next((s for pat, s in CUR if re.fullmatch(pat, cur, re.I)), None)
        if not sign:
            return None
        num = re.sub(r'\s+', ' ', num)
        return ('%s %s %s' % (num, scale, sign)) if sign == '₽' else ('%s%s %s' % (sign, num, scale))
    m = SUM_RE_PRE.search(text)
    if m:
        return '%s%s %s' % (m.group(1), re.sub(r'\s+', ' ', m.group(2).strip()), m.group(3).lower())
    return None


# --- тип сделки ------------------------------------------------------------
TYPE_RULES = [
    ('IPO', r'\bipo\b|\bspo\b|размещ\w+\s+акци|выход\w*\s+на\s+бирж'),
    ('Продажа с торгов', r'\bторг(?:ах|и|ов)\b|аукцион|конкурсн\w+\s+производств|банкротн'),
    ('Финансирование · структурная сделка',
     r'структурн\w+\s+\w*\s*сделк|под\s+залог|предоплатн\w+\s+финансир|синдицированн|кредитн\w+\s+лини'),
    ('Инвестиция',
     r'раунд|series\s+[abcd]\b|\bseed\b|pre-?ipo|венчурн|инвестиц\w+\s+в\b|инвестировал'),
    ('M&A', r'.'),                       # по умолчанию — покупка/продажа
]


def guess_type(text):
    text = str(text or '')
    for name, pattern in TYPE_RULES:
        if re.search(pattern, text, re.I):
            return name
    return 'M&A'


# --- статус ----------------------------------------------------------------
FUTURE = r'план\w+|намерен|ведёт\s+переговоры|ведет\s+переговоры|может\s+(?:купить|продать|приобрести)' \
         r'|рассматрива\w+|обсужда\w+|договорил\w+|намерева'
SIGNED = r'подписал\w*\s+(?:соглашени|договор)|заключил\w*\s+(?:соглашени|договор)'
APPROVED = r'(?:получил|получила|получило|получили)\s+(?:согласие|одобрение|разрешение)' \
           r'|(?:фас|регулятор|правкомисси\w*|правительственн\w+\s+комисси\w*)\s+(?:одобрил|одобрила|согласовал|разрешил)'
DONE = r'закрыл\w*\s+сделку|сделка\s+закрыта|завершил\w*|купил|приобр(?:е|ё)л|продал|выкупил'
CANCELLED = r'сделка\s+не\s+состоял|отказал\w*\s+от\s+сделк|переговоры\s+прекращен|сделк\w*\s+отмен'


def guess_status(text):
    text = str(text or '')
    if re.search(CANCELLED, text, re.I):
        return 'Не состоялась'
    if re.search(DONE, text, re.I):
        return 'Закрыта'
    if re.search(APPROVED, text, re.I):
        return 'Согласование получено'
    if re.search(SIGNED, text, re.I):
        return 'Подписана'
    if re.search(FUTURE, text, re.I):
        return 'Обсуждается'
    return None


def guess_event(item):
    """Один подтверждённый этап из одной новости, без пересказа от модели.

    Заголовок этапа определяется закрытыми правилами, дата и ссылка берутся из
    самой записи. Если новость не содержит маркера этапа, возвращаем None —
    лишний этап хуже пропущенного.
    """
    text = ' '.join(x for x in (item.get('title'), item.get('summary')) if x)
    status = guess_status(text)
    if not status:
        return None
    kind = {
        'Обсуждается': 'negotiations',
        'Подписана': 'signed',
        'Согласование получено': 'approval',
        'Закрыта': 'closed',
        'Не состоялась': 'cancelled',
    }[status]
    title = {
        'negotiations': 'Переговоры',
        'signed': 'Документы подписаны',
        'approval': 'Согласование получено',
        'closed': 'Сделка завершена',
        'cancelled': 'Сделка не состоялась',
    }[kind]
    summary = re.sub(r'\s+', ' ', str(item.get('summary') or '')).strip()
    return {
        'kind': kind,
        'date': item.get('date') or 'unknown',
        'title': title,
        'note': summary[:260].rstrip(' ,;:-—') if summary else '',
        'source': [item.get('source_name') or item.get('source_id') or 'источник',
                   item.get('url')] if item.get('url') else None,
    }


# --- стороны ---------------------------------------------------------------
BUY_VERB = re.compile(
    r'\b(?:куп(?:ил[аио]?|ит|ят|ует)|приобр(?:е|ё)(?:л[аио]?|тает|тёт|тет)|выкуп(?:ил[аио]?|ает|ит)'
    r'|консолидировал[аи]?|получил[аио]?)\b', re.I)
SELL_VERB = re.compile(r'\b(?:прода(?:л[аио]?|ёт|ет|ст)|реализовал[аи]?)\b', re.I)
FROM_WHOM = re.compile(r'\bу\s+((?:[а-яё]+\s+){0,3}[«"А-ЯЁA-Z][^.;,]{2,60})')
SALE_BUYER_MARKER = re.compile(
    r'\b(?:компании|группе|банку|фонду|структуре|холдингу|инвестору|'
    r'консорциуму|менеджменту|сотрудникам|покупателю|ритейлеру|девелоперу|'
    r'оператору|предпринимателю|владельцу)\s+', re.I)
GENERIC_ASSET_END = re.compile(
    r'(?:^|\s)(?:дол[яиюей]|акци[яиюй]|пакет|бизнес|активы?|контроль|общество|'
    r'предприятие|компания|100%)\s*(?:в)?$', re.I)


def clean_name(text):
    text = re.sub(r'\s+', ' ', str(text or '')).strip(' ,;:-—')
    text = re.sub(r'^(?:компании|компания|группы|группа|банка|банк|фонда|фонд|холдинга|холдинг|'
                  r'структур[ыа]?|девелопера|аэропорта|альянса)\s+', '', text, flags=re.I)
    text = re.sub(r'\s+за\s+[\d$€].*$', '', text)
    return text.strip()


def _split_sale_tail(tail):
    """Разделить «актив компании/банку покупателю» без догадки по падежу.

    Берём только явный служебный маркер покупателя. Конструкция «доля в
    компании X» намеренно не разбирается: в ней X обычно является предметом,
    а не покупателем.
    """
    matches = list(SALE_BUYER_MARKER.finditer(tail))
    if len(matches) > 1:
        # Заголовок может описывать две параллельные продажи. Такой текст
        # нельзя сводить к одному покупателю автоматически.
        return clean_name(tail), None
    for marker in reversed(matches):
        prefix = tail[:marker.start()].strip(' ,;:-—')
        suffix = tail[marker.end():].strip(' ,;:-—')
        before = tail[max(0, marker.start()-3):marker.start()].lower().strip()
        if not prefix or not suffix or before == 'в':
            continue
        marker_word = marker.group(0).strip().lower()
        if marker_word == 'компании' and not re.search(r'[«"А-ЯЁA-Z0-9]', prefix):
            # «Продала дочерние компании (X и Y)» — здесь слово «компании»
            # описывает предмет, а не вводит покупателя.
            continue
        if GENERIC_ASSET_END.search(prefix):
            continue
        if len(suffix) > 100 or not re.search(r'[«"А-ЯЁA-Z0-9]', suffix):
            continue
        return clean_name(prefix), clean_name(suffix)
    return clean_name(tail), None


def guess_parties(title):
    """(покупатель, предмет, продавец) — только явно названные стороны.

    Подлежащее до глагола покупки — покупатель; сторона после «у» — продавец.
    Для заголовков о продаже покупатель извлекается только после явного
    маркера («компании», «банку», «фонду», «структуре» и т. п.).
    """
    title = re.sub(r'\s+', ' ', str(title or '')).strip()
    buyer = asset = seller = None
    m = BUY_VERB.search(title)
    if m:
        head = title[:m.start()].strip()
        if head and len(head) < 70:
            buyer = clean_name(head)
        tail = title[m.end():]
        u = FROM_WHOM.search(tail)
        if u:
            seller = clean_name(u.group(1))
            tail = tail[:u.start()]
        asset = clean_name(re.sub(r'^\s*(?:\d+[,.]?\d*%|\d+%|долю|доли|пакет|акции|контроль)\s*(?:в|акций)?\s*',
                                  '', tail.strip()))
    else:
        m = SELL_VERB.search(title)
        if m:
            head = title[:m.start()].strip()
            if head and len(head) < 70:
                seller = clean_name(head)
            asset, buyer = _split_sale_tail(title[m.end():].strip())
    cut = lambda s: (s[:100].rstrip(' ,;:-—') if s else None)
    return cut(buyer), cut(asset), cut(seller)


# --- отрасль ---------------------------------------------------------------
def guess_industry(text, companies):
    """Отрасль берётся у профиля компании, найденного в тексте, а не угадывается
    по словам: угаданная отрасль — это выдумка, а профиль — факт базы."""
    low = ' ' + re.sub(r'\s+', ' ', str(text or '')).lower() + ' '
    best = None
    for comp in companies.values():
        name = str(comp.get('name') or '')
        core = re.sub(r'^(ООО|АО|ПАО|ЗАО|ГК|МКООО)\s+', '', name).strip('«» "')
        if len(core) < 4:
            continue
        if ' ' + core.lower() + ' ' in low or '«%s»' % core.lower() in low:
            if comp.get('ind') and (best is None or len(core) > best[1]):
                best = (comp['ind'], len(core))
    return best[0] if best else None


def industry_for(title, companies):
    """Отрасль берётся по ПРЕДМЕТУ сделки, а не по всему заголовку.

    Иначе «Альфа-банк приобрел платформу Flocktory» получает отрасль банка, а
    сделка — про e-commerce: замер прогона 47 показал 180 таких ошибок из 1066.
    Предмет — то, что стоит после глагола покупки; если его выделить не вышло,
    отступаем к заголовку целиком.
    """
    _, asset, _ = guess_parties(title)
    return guess_industry(asset, companies) if asset else guess_industry(title, companies)


def build(item, companies):
    """Черновик карточки из записи разбора."""
    text = ' '.join(x for x in (item.get('title'), item.get('summary')) if x)
    buyer, asset, seller = guess_parties(item.get('title'))
    event = guess_event(item)
    return {
        'draft_id': 'd' + str(abs(hash(item.get('url'))))[:8],
        'title': item.get('title'),
        'date': item.get('date'),
        'src': [[item.get('source_name') or item.get('source_id'), item.get('url')]],
        'sum': guess_sum(text),
        'type': guess_type(text),
        'status': guess_status(text),
        'events': [event] if event else [],
        'buyer_name': buyer,
        'asset': asset,
        'seller': seller,
        'parsed_parties': {'buyer': buyer, 'asset': asset, 'seller': seller},
        'ind': industry_for(item.get('title') or text, companies),
        'needs_review': True,
    }


# --- замер на своей базе ---------------------------------------------------
def norm(s):
    return re.sub(r'[«»"\'(),.\s]', '', str(s or '')).lower()


def measure():
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    stats = {k: {'молчит': 0, 'попал': 0, 'ошибся': 0, 'нечем проверить': 0}
             for k in ('сумма', 'тип', 'статус', 'покупатель', 'продавец', 'отрасль')}

    def core(s):
        """Первое значимое слово имени: «ООО «Нео-Фарм»» и «Неофарм» — одно и
        то же имя, записанное по-разному, и считать это ошибкой разбора нельзя."""
        words = [w for w in re.findall(r'[\w-]{4,}', str(s or ''), re.U)
                 if w.lower() not in ('оооо', '公司')]
        skip = {'ооо', 'пао', 'зао', 'акционерное', 'общество', 'группа', 'холдинг',
                'компания', 'медиахолдинг', 'строительная'}
        words = [w for w in words if w.lower() not in skip]
        return re.sub(r'[^\wа-яё]', '', words[0].lower())[:5] if words else ''

    def score(key, guess, truth):
        if not truth:
            stats[key]['нечем проверить'] += 1
        elif not guess:
            stats[key]['молчит'] += 1
        elif (norm(guess) == norm(truth) or norm(guess) in norm(truth)
              or norm(truth) in norm(guess) or (core(guess) and core(guess) == core(truth))):
            stats[key]['попал'] += 1
        else:
            stats[key]['ошибся'] += 1

    for deal in data['deals']:
        title = str(deal.get('title') or '')
        buyer, asset, seller = guess_parties(title)
        true_buyer = (comps.get(deal.get('buyer')) or {}).get('name') or deal.get('buyer_name')
        true_seller = (comps.get(deal.get('seller_id')) or {}).get('name') or deal.get('seller')
        score('сумма', guess_sum(title), deal.get('sum') if deal.get('sum') not in ('—', None) else None)
        score('тип', guess_type(title), deal.get('type'))
        score('статус', guess_status(title), deal.get('status'))
        score('покупатель', buyer, true_buyer)
        score('продавец', seller, true_seller)
        score('отрасль', industry_for(title, comps), deal.get('ind'))

    print('Разбор заголовка против выверенной карточки, %d сделок:\n' % len(data['deals']))
    print('%-12s %8s %8s %8s %8s' % ('поле', 'попал', 'ошибся', 'молчит', 'нет эталона'))
    for key, row in stats.items():
        print('%-12s %8d %8d %8d %8d'
              % (key, row['попал'], row['ошибся'], row['молчит'], row['нечем проверить']))
    print('\nОшибка дороже молчания: карточка с неверным покупателем хуже карточки,')
    print('где покупатель пуст. Поэтому правила намеренно молчаливы.')


def main(argv):
    if '--measure' in argv:
        measure()
        return
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    path = os.path.join(TRIAGE, day + '.json')
    if not os.path.exists(path):
        print('Нет разбора за %s — сначала fetch.py и triage.py' % day)
        return
    items = json.load(open(path, encoding='utf-8'))['items']
    drafts = [build(x, comps) for x in items if x.get('verdict') == 'new']
    os.makedirs(DRAFTS, exist_ok=True)
    out = os.path.join(DRAFTS, day + '.json')
    json.dump({'made': day, 'drafts': drafts}, open(out, 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)
    print('Черновиков: %d -> %s' % (len(drafts), os.path.relpath(out, ROOT)))
    for d in drafts:
        filled = [k for k in ('sum', 'buyer_name', 'seller', 'asset', 'ind') if d.get(k)]
        print('  %s | заполнено: %s' % (d['title'][:70], ', '.join(filled) or '—'))


if __name__ == '__main__':
    main(sys.argv[1:])
