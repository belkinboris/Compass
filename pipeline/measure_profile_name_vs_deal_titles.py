# -*- coding: utf-8 -*-
"""Замер (не пишет в базу): профили компаний с 2+ сделками, чьё имя не
встречается ни в одном заголовке связанной сделки — сигнал того, что
профиль на деле обслуживает больше одной сущности (см. журнал прогона
G2-30: «стоит подумать, не завести ли одноразовый скрипт-замер»).

КАК СЧИТАЕТ. Слово имени профиля и слово заголовка сделки совпадают,
если совпадают их 5-значные префиксы после транслитерации в латиницу
(снимает падеж: «Еаптека»/«Еаптеке») и смягчения c/k, ph/f, y/i, ё/e,
удвоенных букв (тот же приём, что `test_no_company_twins`). Профиль, ни
одна сделка которого не даёт совпадения, — сильнейший сигнал; профиль с
частичным совпадением — слабее (может быть законной ролью без
дословного имени в заголовке, например «Сбер» в заголовке при имени
профиля «Сбербанк»).

ЧТО ЭТО НЕ ЛОВИТ. Ложных срабатываний много: заголовок называет РОЛЬ
стороны («структуры Харитонина»), а не имя профиля дословно — это не
дефект. Каждый кандидат ТРЕБУЕТ чтения текста сделки, а не автоматической
правки (родня урока CLAUDE.md «признак дефекта — повод прочитать, а не
основание стереть»).

ЗАМЕР 11 августа (прогон G2-31): 36 кандидатов из 1709 профилей с 2+
сделками; из 5 профилей с ПОЛНЫМ отсутствием совпадения (сильнейший
сигнал) — 4 ложных (уже проверены и описаны: «Лента», Augment
Investments, «Стинн», «АЛД Автомотив»), 1 настоящий близнец
(TicketsCloud/«ТИКЕТСКЛАУД», слит скриптом
`merge_ticketscloud_twin_and_describe_batch31.py`). Оставшиеся 31
кандидат послабее сигналом — не прочитаны, ждут следующего прогона.

Запуск: python3 pipeline/measure_profile_name_vs_deal_titles.py
"""
import json
import re
from collections import defaultdict

DATA = 'static/data/deals_promoted.json'

CYR = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
       "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
       "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
       "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "i", "ь": "", "э": "e",
       "ю": "iu", "я": "ia"}
ORG_FORMS = re.compile(r'\b(ооо|зао|оао|пао|ао|нко|мкоо|нао|гк|пкф|тд|group|holding|corp'
                        r'|corporation|inc|ltd|llc|плс|plc)\b', re.I)
QUOTES = re.compile(r'[«»"\'`]')
PREFIX_LEN = 5


def translit_word(w):
    w = "".join(CYR.get(ch, ch) for ch in w)
    for a, b in (("ph", "f"), ("sch", "sh"), ("ck", "k"), ("ts", "s"), ("x", "ks"),
                 ("w", "v"), ("q", "k"), ("y", "i"), ("j", "i")):
        w = w.replace(a, b)
    w = w.replace("ch", "\x00").replace("c", "k").replace("\x00", "ch")
    return re.sub(r"(.)\1+", r"\1", w)


def prefixes(s):
    s = QUOTES.sub('', s or '')
    s = ORG_FORMS.sub(' ', s)
    s = re.sub(r'[^\w\s]', ' ', s, flags=re.U)
    words = re.sub(r'\s+', ' ', s).strip().lower().split()
    return [translit_word(w)[:PREFIX_LEN] for w in words if len(translit_word(w)) >= 4]


def main():
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    deals = data['deals']

    by_company = defaultdict(list)
    for d in deals:
        for role in ('buyer', 'target', 'seller_id'):
            v = d.get(role)
            if isinstance(v, str) and v in comps:
                by_company[v].append((role, d))

    candidates = []
    for cid, entries in by_company.items():
        if len(entries) < 2:
            continue
        name_pfx = set(prefixes(comps[cid].get('name', '')))
        if not name_pfx:
            continue
        missing = [(d['id'], d.get('title')) for role, d in entries
                   if not (name_pfx & set(prefixes(d.get('title', ''))))]
        if missing:
            candidates.append((cid, comps[cid].get('name'), len(entries), missing))

    candidates.sort(key=lambda x: (-(len(x[3]) == x[2]), -len(x[3])))
    print(f'Кандидатов: {len(candidates)} из {len(by_company)} профилей с 2+ сделками')
    print()
    for cid, name, total, missing in candidates:
        all_missing = ' ВСЕ' if len(missing) == total else ''
        print(f'{cid} {name!r} ({total} сделок, {len(missing)} без имени{all_missing})')
        for did, title in missing:
            print(f'    {did}: {title!r}')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
