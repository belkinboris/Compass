# -*- coding: utf-8 -*-
"""Кураторские карточки из `static/index.html` — чтобы приток о них знал.

ЧТО БЫЛО СЛОМАНО. 19 карточек живут не в `deals_promoted.json`, а прямо в
`static/index.html` (захардкоженный массив `DEALS`): citibank, «Балтика»,
Hugo Boss/«Стокманн», Яндекс/«Заряд!», «Мерседес», TechnoRed и другие. При
этом `match.py` строит индекс ТОЛЬКО по `deals_promoted.json` — то есть весь
приток был структурно слеп к этим 19 сделкам: любая новость о них считалась
новой, и мы завели бы дубль уже существующей карточки.

Нашлось это не проверкой кода, а вопросом владельца: он вбил две сделки,
которые точно помнит (Яндекс/«Заряд!» и «Стокманн»/Hugo Boss), и обе нашлись
на сайте — хотя мой разбор архива объявил их отсутствующими. Урок в CLAUDE.md:
у базы ТРИ источника данных, и проверка на дубль обязана смотреть во все.

ЧТО ОТДАЁТСЯ. Только поля, нужные `match.py` для сопоставления: id, дата,
заголовок, сумма, стороны и ссылки. Полные карточки (eco/law) остаются в
интерфейсе — приток их не читает и не правит.

ПОЧЕМУ РАЗБОР РЕГУЛЯРКОЙ, А НЕ JSON. Массив лежит внутри JavaScript и не
является валидным JSON (ключи без кавычек). Полноценный разбор JS здесь не
нужен: у карточек регулярная шапка `{id:"…",date:"…",title:"…"…}`, и берутся
только поля из неё. Если формат изменится, `assert` в `load()` упадёт, а не
молча вернёт пустой список — это важнее гибкости.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
INDEX = os.path.join(ROOT, 'static', 'index.html')

HEAD = re.compile(r'\{id:"([a-zA-Z0-9_-]+)",date:"([0-9-]+)",title:"((?:[^"\\]|\\.)*)"')
FIELD = re.compile(r'\b%s:"((?:[^"\\]|\\.)*)"')
SRC_BLOCK = re.compile(r'src:\s*\[(.*?)\]\s*\}', re.S)
SRC_URL = re.compile(r'"(https?://[^"]+)"')

# Сколько карточек ожидается. Если формат разъедется, счёт не сойдётся и
# скрипт упадёт — вместо того чтобы тихо отдать половину и снова ослепить
# приток. Число меняется вместе с массивом в index.html, осознанно.
EXPECTED = 19


def _field(chunk, name):
    m = re.search(r'\b%s:"((?:[^"\\]|\\.)*)"' % name, chunk)
    return m.group(1) if m else None


def load(path=None):
    """[{id, date, title, sum, buyer, target, seller, src}] — вид, который
    понимает `match.index_base`."""
    text = open(path or INDEX, encoding='utf-8').read()
    starts = [m.start() for m in HEAD.finditer(text)]
    assert starts, 'кураторские карточки не найдены в %s — изменился формат?' % (path or INDEX)

    out = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else min(start + 12000, len(text))
        chunk = text[start:end]
        head = HEAD.match(text, start)
        urls = []
        block = SRC_BLOCK.search(chunk)
        if block:
            urls = SRC_URL.findall(block.group(1))
        out.append({
            'id': head.group(1),
            'date': head.group(2),
            'title': head.group(3),
            'sum': _field(chunk, 'sum'),
            'status': _field(chunk, 'status'),
            'buyer': _field(chunk, 'buyer'),
            'target': _field(chunk, 'target'),
            'seller': _field(chunk, 'seller'),
            'src': [['', u] for u in urls],
            'curated': True,
        })
    assert len(out) == EXPECTED, (
        'ожидали %d кураторских карточек, разобрали %d — формат массива в '
        'index.html изменился, поправьте EXPECTED осознанно' % (EXPECTED, len(out)))
    return out


def index_all(data, matcher, path=None):
    """Индекс `match.py` по ОБЕИМ частям базы сразу: и промоутнутые карточки,
    и кураторские. Приток обязан пользоваться только этим входом, иначе
    вернётся та же слепота."""
    deals = list(data['deals']) + load(path)
    return matcher.index_base(deals, data.get('companies'), data.get('match_keys'))
