# -*- coding: utf-8 -*-
"""Источник подписан «@dealsma (Telegram)», хотя ссылка ведёт на СМИ.

ЧТО СЛОМАНО. У 913 карточек из 1350 (68%) первый источник подписан
«@dealsma (Telegram)» — имя Telegram-канала, через который сделка попала в
базу. Но у подавляющего большинства ссылка при этом ведёт НЕ на t.me, а
прямо на статью в Коммерсанте, Ведомостях, РБК и т. д.: подпись называет,
откуда мы узнали о сделке, а не то, что подтверждает факт, — и вводит в
заблуждение читателя, который кликает «источник», ожидая точно то же самое,
что видит рядом с подписью «Коммерсантъ».

ЗАМЕР (после починки 10 битых ссылок в fix_broken_source_links.py):
  * 78 источников с подписью dealsma/Telegram РЕАЛЬНО ведут на t.me —
    подпись «Telegram» для них верна, не трогаем.
  * 49 источников — «домен» без пути (`http://X.ru/`), похожий на
    название компании из текста карточки, а не на ссылку на статью; из них
    10 уже почищены отдельным скриптом (2 WhatsApp-ссылки, 8 живым поиском),
    ОСТАЛЬНЫЕ 41 не тронуты (см. PRODUCT_ROADMAP.md) — их не переименовать
    честно, они не ведут ни на что.
  * 836 источников — обычная ссылка на конкретную статью. Ниже правится
    только эта группа: подпись меняется на имя издания, определённое по
    домену ссылки. Правка решением владельца (2 августа 2026): «источник —
    это то, что подтверждает факт», а не то, как редакция о нём узнала.

КАК ОПРЕДЕЛЯЕТСЯ ИМЯ. Таблица `DOMAIN_NAMES` — для узнаваемых изданий
(Коммерсантъ, Ведомости, РБК и её региональные/тематические поддомены,
Интерфакс, Forbes и т. д.). Для доменов вне таблицы (длинный хвост из
единичных упоминаний — нишевые отраслевые издания, собственные сайты
компаний-сторон сделки) имя не выдумывается: подписью становится сам домен
с заглавной буквы («Eqiva.ru» вместо «eqiva.ru») — это не имя издания «на
глаз», а честная запись того, что реально стоит в ссылке.

ЧЕГО НЕ ДЕЛАЕМ. Не трогаем настоящие t.me-ссылки (там подпись верна) и не
трогаем «домены без пути» — правка URL для них ещё не сделана, подписывать
несуществующую статью именем издания значило бы утверждать больше, чем
показывает ссылка.

Запуск:
    python3 pipeline/relabel_dealsma_sources.py            # сухой прогон
    python3 pipeline/relabel_dealsma_sources.py --write    # записать
"""
import json
import os
import re
import sys
from urllib.parse import urlparse

PATH = 'static/data/deals_promoted.json'
LABEL_RE = re.compile(r'dealsma|telegram', re.I)

EXPECTED_TOUCHED = 836

# Таблица «домен -> имя издания» вынесена в pipeline/source_names.py:
# она понадобилась второму скрипту (fix_web_prefixed_source_labels.py), а
# два экземпляра одной таблицы — готовый баг.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from source_names import DOMAIN_NAMES, display_name  # noqa: E402,F401


def is_bare(url):
    p = urlparse(url)
    return not p.path.rstrip('/') and not p.query


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    changes = []
    for d in data['deals']:
        src = d.get('src') or []
        for i, s in enumerate(src):
            if len(s) < 2:
                continue
            label, url = s[0], s[1]
            if not LABEL_RE.search(str(label)):
                continue
            domain = urlparse(url).netloc.replace('www.', '')
            if domain == 't.me' or is_bare(url) or 'wa.me' in domain:
                continue
            new_label = display_name(domain)
            if new_label == label:
                continue
            changes.append((d['id'], i, label, new_label, url))
            if write:
                src[i] = [new_label, url]

    assert len(changes) == EXPECTED_TOUCHED, (
        f'ожидали {EXPECTED_TOUCHED} правок, нашли {len(changes)} — '
        'состав базы изменился с момента замера, перепроверьте перед записью')

    print(f'правок: {len(changes)}')
    from collections import Counter
    by_new_label = Counter(c[3] for c in changes)
    for label, cnt in by_new_label.most_common(30):
        print(f'  {cnt:4d}  -> {label}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
