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

ПОЧЕМУ НЕ РАЗБОР РЕГУЛЯРКОЙ. Первая версия читала `index.html` регуляркой и
видела только `DEALS` — а наборов ТРИ: `DEALS` (19), `MINI_DEALS` (21) и
`CHANNEL_DEALS` (14). То есть починка слепоты сама была слепой на 35 сделок
из 54. Теперь источник — `static/data/curated_deals.json`, который снимает с
интерфейса `pipeline/export_curated_from_interface.py` настоящим браузером:
он исполняет файл так же, как посетитель, и своего парсера JS не требует.
Файл обновляется скриптом, а не руками.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
INDEX = os.path.join(ROOT, 'static', 'index.html')

CURATED = os.path.join(ROOT, 'static', 'data', 'curated_deals.json')

# Сколько карточек ожидается: 19 кураторских + 21 мини + 14 из канала. Если
# счёт разъедется, `load()` упадёт — вместо того чтобы тихо отдать половину и
# снова ослепить приток на остальное.
EXPECTED = 54


def load(path=None):
    """[{id, date, title, sum, buyer, target, seller, src}] — вид, который
    понимает `match.index_base`."""
    rows = json.load(open(path or CURATED, encoding='utf-8'))
    assert len(rows) == EXPECTED, (
        'ожидали %d карточек интерфейса, в файле %d — перевыгрузите '
        'pipeline/export_curated_from_interface.py и поправьте EXPECTED' % (EXPECTED, len(rows)))
    out = []
    for row in rows:
        src = row.get('src') or []
        out.append({
            'id': row['id'],
            'date': row.get('date'),
            'title': row.get('title'),
            'sum': row.get('sum'),
            'status': row.get('status'),
            'buyer': row.get('buyer'),
            'target': row.get('target'),
            'seller': row.get('seller'),
            'asset': row.get('asset'),
            'src': [s if isinstance(s, list) else ['', s] for s in src],
            'curated': True,
        })
    return out


def index_all(data, matcher, path=None):
    """Индекс `match.py` по ОБЕИМ частям базы сразу: и промоутнутые карточки,
    и кураторские. Приток обязан пользоваться только этим входом, иначе
    вернётся та же слепота."""
    deals = list(data['deals']) + load(path)
    return matcher.index_base(deals, data.get('companies'), data.get('match_keys'))
