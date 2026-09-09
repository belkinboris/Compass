# -*- coding: utf-8 -*-
"""Подпись источника называет издание, на которое ведёт ссылка, — все 89 хвостов.

ЧТО ЧИНИТ. Владелец 9 сентября 2026, открыв карточку «Амбер Талвиса»:
«я нажимаю на источник в этой новости, а перехожу не на телеграм канал,
который там показан @DEALSMA (как так вообще?), а на torgi.gov».

Класс дефекта в CLAUDE.md записан давно («Источник — то, что подтверждает
факт, а не то, как о нём узнали»), и кампания августа переподписала 913
карточек по домену ссылки. Но она чинила ТО, ЧТО НАШЛА ТОГДА, и хвост остался
жить: замер 9 сентября 2026 — 89 карточек, у которых подпись говорит про
Telegram (или начинается с «@»), а ссылка ведёт в обычное издание:
Коммерсантъ (29), Ведомости (10), РБК (9), Forbes (9), АК&М, Интерфакс, ТАСС,
Reuters, Bloomberg, портал правовой информации и — та самая карточка —
torgi.gov.ru. Читатель видит имя телеграм-канала, кликает и попадает в газету;
хуже того, канал-агрегатор выдаётся за первоисточник.

ПОЧЕМУ ЭТО НЕ ЧИНИТСЯ «ЕЩЁ ОДНОЙ ЧИСТКОЙ, КАК В АВГУСТЕ». Разовый скрипт
снимает то, что накопилось, и уходит; через месяц хвост нарастает снова —
это и произошло. Поэтому здесь два конца: этот скрипт снимает накопленное, а
`test_data.py::test_source_label_matches_the_link` не даёт классу вырасти
заново — он падает на ЛЮБОЙ карточке, где подпись обещает Telegram, а ссылка
ведёт в другое место, независимо от того, каким путём такая пара появилась.

КАК ВЫБИРАЕТСЯ НОВАЯ ПОДПИСЬ. Только `source_names.edition_label(url)` — та же
таблица, что у притока и у прошлой кампании; ничего не сочиняется. Если
таблица домена не знает, она возвращает сам домен с заглавной буквы
(«Abireg.ru») — такие случаи скрипт не трогает и печатает отдельным списком,
чтобы имя дописали в таблицу руками, а не подставили красивую догадку.

Запуск:
    python3 pipeline/fix_false_telegram_source_labels.py           # сухой
    python3 pipeline/fix_false_telegram_source_labels.py --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'pipeline'))

from source_names import edition_label, label_promises_telegram, domain_is_known  # noqa: E402

DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'


def links_to_telegram(url):
    host = (urlparse(str(url)).hostname or '').lower()
    return host.endswith('t.me') or host.endswith('telegram.me') or host.endswith('telegram.org')


def main(write=False):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    fixed, unknown = [], []
    for deal in data['deals']:
        for item in (deal.get('src') or []):
            if not (isinstance(item, list) and len(item) >= 2):
                continue
            label, url = str(item[0]), str(item[1])
            if not url.startswith('http'):
                continue
            if not label_promises_telegram(label) or links_to_telegram(url):
                continue
            host = (urlparse(url).hostname or '').lower().replace('www.', '')
            # Таблица домена не знает: имя вывелось бы из самого адреса
            # («Abireg.ru»). Подставлять его — менять одну неверную подпись на
            # некрасивую; такие идут человеку в список, а не в правку.
            if not domain_is_known(url):
                unknown.append((deal['id'], label, host))
                continue
            name = edition_label(url)
            fixed.append((deal['id'], label, name, url))
            if write:
                item[0] = name

    print('Ложных подписей «Telegram» на ссылке в издание: %d' % (len(fixed) + len(unknown)))
    print('  переподписано по таблице изданий: %d' % len(fixed))
    for did, old, new, _ in fixed[:12]:
        print('    %s  %r -> %r' % (did, old, new))
    if len(fixed) > 12:
        print('    … и ещё %d' % (len(fixed) - 12))
    if unknown:
        print('  домен не в таблице `source_names.DOMAIN_NAMES`, оставлено человеку: %d' % len(unknown))
        for did, old, host in unknown:
            print('    %s  %r  <- %s' % (did, old, host))
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    print('\nЗаписано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
