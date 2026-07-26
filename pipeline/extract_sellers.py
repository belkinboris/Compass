# -*- coding: utf-8 -*-
"""Извлечение продавца (стороны, отчуждающей актив) для карточек сделок.

Зачем: в модели данных есть buyer (покупатель) и target (приобретаемый актив),
но продавца нет вообще — хотя в M&A это равноправная сторона. При этом в тексте
он почти всегда назван: «X купил Y У ПРОДАВЦА», «ПРОДАВЕЦ продал Y компании X»,
а также в подписях консультантов («Юридический консультант продавца (Яндекс)»).

Источники по убыванию надёжности:
  1. law.adv — явная подпись стороны с именем в скобках: «...продавца (Яндекс)»
  2. title  — «... у ПРОДАВЦА» / «ПРОДАВЕЦ продал ...» / «Продажа ПРОДАВЦОМ ...»

Пишем два поля:
  seller      — имя продавца строкой (как в тексте, после чистки)
  seller_id   — id компании из базы, если удалось однозначно сопоставить
Плюс seller_src — откуда взято ('adv' | 'title'), чтобы можно было отличать
уверенные извлечения от эвристики.

Запуск:
    python3 pipeline/extract_sellers.py           # сухой прогон
    python3 pipeline/extract_sellers.py --write   # записать в JSON
"""
import json
import re
import sys
import collections

PATH = 'static/data/deals_promoted.json'
HTML = 'static/index.html'

# Слова, которые не могут быть именем продавца: местоимения, ложные срабатывания
# предлога «у», а также обобщённые обозначения стороны без конкретного имени
# («продавцов (акционеров)») и прилагательные, оторванные от существительного
# («Продажа российского бизнеса Essity» -> «российского»).
STOP = re.compile(
    r'^(?:котор|нег|не[ёе]|них|себя|которой|которого|которых|'
    r'частн|неизвестн|компани[ий]?$|акционер|учредител|участник|владельц|'
    r'собственник|менеджмент|основател|физлиц|физическ|группы\s+инвесторов$|'
    r'росси[йя]ск|американск|британск|немецк|французск|финск|японск|китайск|'
    r'иностранн|международн|отечественн|местн|прежн|бывш|нов|прочи|друг)', re.I)
# Хвосты, которые надо отрезать от захваченного имени
TAIL = re.compile(
    r'\s+(?:для\s+проект\w*|в\s+рамках|в\s+ходе|по\s+цене|после\s+|на\s+фоне|'
    r'с\s+целью|при\s+участии|через\s+|и\s+его\s+|и\s+её\s+)\b.*$', re.I)
# Имя компании-заглушки: обрывок фразы, а не название («контрольный пакет Яндекса»)
JUNK_NAME = re.compile(
    r'^(?:контрольн|российск|блокирующ|мажоритарн|миноритарн|дочерн)|'
    r'\b(?:пакет|доля|долей|доли|структур\w*|бизнес\w*|актив\w*)\b', re.I)


def load_company_names():
    """id -> name из JSON + захардкоженного COMPANIES в index.html."""
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    names = {}
    for cid, c in (data.get('companies') or {}).items():
        n = c.get('name') if isinstance(c, dict) else str(c)
        if n:
            names[cid] = n
    html = open(HTML, encoding='utf-8').read()
    s = html.index('const COMPANIES = {')
    i = html.index('{', s)
    depth = 0
    for j in range(i, len(html)):
        if html[j] == '{':
            depth += 1
        elif html[j] == '}':
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    for cid, n in re.findall(r'(?:^|[{,]\s*)([A-Za-z0-9_]+)\s*:\s*\{name:"([^"]+)"', html[i:end]):
        names.setdefault(cid, n)
    return data, names


def norm(s):
    """Грубая нормализация для сопоставления имён: без кавычек, регистра и
    типовых форм собственности, с отсечением русских падежных окончаний."""
    s = (s or '').lower()
    s = re.sub(r'[«»"\'`]', '', s)
    s = re.sub(r'\b(?:ооо|оао|зао|пао|ао|гк|ук|нк|тоо|ltd|llc|inc|plc|group|групп|холдинг)\b', ' ', s)
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    # «яндекса» -> «яндекс», «системы» -> «систем»
    s = re.sub(r'(?:ом|ами|ах|ов|ей|ями|а|у|ы|е|и|я|ю)$', '', s)
    return s


def clean_name(raw):
    if not raw:
        return None
    n = raw.strip('  ,;:.—-')
    # пояснение после слэша или в скобках — не часть имени
    n = re.split(r'\s*/\s*|\s*\(', n)[0]
    n = TAIL.sub('', n).strip(' ,;:.—-')
    # непарные кавычки в конце
    if n.count('«') > n.count('»'):
        n += '»'
    if len(n) < 3 or len(n) > 70:
        return None
    if STOP.search(n):
        return None
    if not re.search(r'[А-Яа-яA-Za-z]', n):
        return None
    return n


# --- источник 1: подпись стороны у консультанта ---
ADV_SELLER = re.compile(r'продавц\w*[^()]*\(([^)]{2,60})\)', re.I)

# --- источник 2: заголовок ---
T_U = re.compile(r'\bу\s+([А-ЯA-Z][^,;:]{2,65}?)(?=$|[,;.]|\s+за\s|\s+в\s+\d|\s+—|\s+-\s|\s+для\s|\s+в\s+рамках)')
T_SOLD = re.compile(r'^([А-ЯA-Z][^,;:]{2,58}?)\s+(?:продал[аои]?|реализовал[аи]?)\b', re.I)
# «Продажа <ПРОДАВЕЦ> 50% доли ...» — имя идёт сразу после «Продажа».
# Конструкции вида «Продажа российского бизнеса Essity» этим паттерном не берём:
# там после «Продажа» стоит прилагательное, а имя продавца — дальше, поэтому
# требуем, чтобы захват начинался с заглавной и не был прилагательным (см. STOP).
T_PRODAZHA = re.compile(r'^Продажа\s+([А-ЯA-Z][\w\s«»"\'\-\.&]{2,52}?)\s+(?:\d|доли|долей|акци|100%)', re.I)
# «Продажа российского бизнеса Essity (бренды ...) компании X» -> Essity
T_PRODAZHA_BIZ = re.compile(r'^Продажа\s+(?:\w+\s+)?(?:бизнеса|активов|подразделения)\s+([А-ЯA-Z][\w\s«»"\'\-\.&]{2,40}?)(?=$|[,(]|\s+компани|\s+групп|\s+—)', re.I)


def extract(d):
    """-> (имя, источник) либо (None, None)"""
    for row in (d.get('law') or {}).get('adv') or []:
        if not row:
            continue
        m = ADV_SELLER.search(str(row[0] or ''))
        if m:
            n = clean_name(m.group(1))
            if n:
                return n, 'adv'
    t = d.get('title') or ''
    for rx in (T_SOLD, T_PRODAZHA_BIZ, T_PRODAZHA, T_U):
        m = rx.search(t)
        if m:
            n = clean_name(m.group(1))
            if n:
                return n, 'title'
    return None, None


def main(write=False):
    data, names = load_company_names()
    # Несколько профилей могут нормализоваться в один ключ («Яндекс» и мусорный
    # обрывок «Яндексе»). Берём лучшего кандидата: сначала не-заглушку, затем
    # с более коротким (то есть более «чистым») названием.
    buckets = {}
    for cid, n in names.items():
        buckets.setdefault(norm(n), []).append(cid)
    by_norm = {}
    for key, ids in buckets.items():
        ids.sort(key=lambda c: (bool(JUNK_NAME.search(names.get(c, ''))), len(names.get(c, ''))))
        by_norm[key] = ids[0]

    stats = collections.Counter()
    samples = []
    for d in data['deals']:
        name, src = extract(d)
        if not name:
            d.pop('seller', None)
            d.pop('seller_id', None)
            d.pop('seller_src', None)
            continue
        cid = by_norm.get(norm(name))
        # профиль-обрывок («Яндексе», «контрольный пакет Яндекса») — не ссылаемся
        if cid and JUNK_NAME.search(names.get(cid, '')):
            cid = None
        # Частый дефект данных: в target лежит не приобретаемый актив, а ПРОДАВЕЦ
        # («Т-Технологии купила Авто.ру у Яндекса», target=Яндекс). Если извлечённый
        # из текста продавец совпал с компанией в target — значит target подписан
        # неверно: переносим его в продавца и очищаем. Делаем это только когда есть
        # покупатель, иначе у карточки не осталось бы ни одной стороны.
        if cid and cid == d.get('target') and d.get('buyer') and cid != d.get('buyer'):
            d['target'] = None
            d['target_was_seller'] = True
            stats['fixed_target_was_seller'] += 1
        elif cid and cid in (d.get('buyer'), d.get('target')):
            cid = None
        if cid == d.get('buyer'):
            stats['skip_is_buyer'] += 1
            continue
        d['seller'] = name
        d['seller_src'] = src
        if cid:
            d['seller_id'] = cid
            stats['matched_company'] += 1
        else:
            d.pop('seller_id', None)
        stats[src] += 1
        stats['total'] += 1
        if len(samples) < 14:
            samples.append((d['id'], (d.get('title') or '')[:60], name, cid, src))

    print('извлечено продавцов:', stats['total'])
    print('  из подписи консультанта (adv):', stats['adv'])
    print('  из заголовка (title):', stats['title'])
    print('  сопоставлено с компанией базы:', stats['matched_company'])
    print('  исправлено target, где на деле был продавец:', stats['fixed_target_was_seller'])
    print('\nпримеры:')
    for i, t, n, cid, src in samples:
        print(f'  [{src}] {n!r:38} {"→ "+cid if cid else "(без ссылки)":22} | {t}')
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
