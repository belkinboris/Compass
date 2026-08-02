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
import re
import sys
from urllib.parse import urlparse

PATH = 'static/data/deals_promoted.json'
LABEL_RE = re.compile(r'dealsma|telegram', re.I)

EXPECTED_TOUCHED = 836

DOMAIN_NAMES = {
    'kommersant.ru': 'Коммерсантъ',
    'vedomosti.ru': 'Ведомости',
    'vdmsti.ru': 'Ведомости',
    'rbc.ru': 'РБК',
    'amp.rbc.ru': 'РБК',
    'pro.rbc.ru': 'РБК Pro',
    'quote.rbc.ru': 'РБК Quote',
    'quote.ru': 'РБК Quote',
    'reader.rbc.ru': 'РБК',
    'tv.rbc.ru': 'РБК ТВ',
    'ekb.rbc.ru': 'РБК Екатеринбург',
    'kuban.rbc.ru': 'РБК Кубань',
    'nsk.rbc.ru': 'РБК Новосибирск',
    'rostov.rbc.ru': 'РБК Ростов',
    'ufa.rbc.ru': 'РБК Уфа',
    'interfax.ru': 'Интерфакс',
    'interfax-russia.ru': 'Интерфакс',
    'realty.interfax.ru': 'Интерфакс Недвижимость',
    'web.scan-interfax.ru': 'СКАН-Интерфакс',
    'news.myseldon.com': 'СКАН-Интерфакс',
    'forbes.ru': 'Forbes',
    'forbes-ru.turbopages.org': 'Forbes',
    'forbes.kz': 'Forbes Kazakhstan',
    'tass.ru': 'ТАСС',
    'iz.ru': 'Известия',
    'rb.ru': 'RB.ru',
    'akm.ru': 'АК&М',
    'cnews.ru': 'CNews',
    'comnews.ru': 'ComNews',
    'vc.ru': 'VC.ru',
    'vademec.ru': 'Vademecum',
    'dp.ru': 'Деловой Петербург',
    'abireg.ru': 'Абирег',
    'abn.agency': 'АБН',
    'fontanka.ru': 'Фонтанка.ру',
    'frankmedia.ru': 'Frank Media',
    'frankrg.com': 'Frank RG',
    'tadviser.ru': 'TAdviser',
    'shoppers.media': 'Shoppers',
    'gorodn.ru': 'Про Город',
    'sostav.ru': 'Sostav.ru',
    'bloomberg.com': 'Bloomberg',
    'reuters.com': 'Reuters',
    'washingtonpost.com': 'The Washington Post',
    'timesofisrael.com': 'The Times of Israel',
    'derstandard.at': 'Der Standard',
    'mscwtimes.global.ssl.fastly.net': 'The Moscow Times',
    'ru.wikipedia.org': 'Википедия',
    'realty.ria.ru': 'РИА Недвижимость',
    'static.kremlin.ru': 'Kremlin.ru',
    'publication.pravo.gov.ru': 'Официальный интернет-портал правовой информации',
    '1prime.ru': 'ПРАЙМ',
    '47news.ru': '47News',
    '74.ru': '74.RU',
    'agroinvestor.ru': 'Агроинвестор',
    'bfm.ru': 'BFM.ru',
    'business-magazine.online': 'Бизнес-журнал',
    'c-o-k.ru': 'С.О.К.',
    'chelny-biz.ru': 'Челны-биз',
    'dk.ru': 'Деловой квартал',
    'nn.dk.ru': 'Деловой квартал Нижний Новгород',
    'finam.ru': 'Финам',
    'inkazan.ru': 'InKazan',
    'kam24.ru': 'Kam24',
    'ko.ru': 'Компания',
    'konkurent.ru': 'Конкурент',
    'medvestnik.ru': 'Медицинский вестник',
    'neftegaz.ru': 'Нефтегаз.ру',
    'new-retail.ru': 'New Retail',
    'ngs55.ru': 'НГС55',
    'nur.kz': 'NUR.KZ',
    'pharmvestnik.ru': 'Фармацевтический вестник',
    'plastinfo.ru': 'Plastinfo',
    'portnews.ru': 'PortNews',
    'retail.ru': 'Retail.ru',
    'ruscable.ru': 'РусКабель',
    'tomsk.aif.ru': 'АиФ Томск',
    'vgudok.com': 'Вгудок',
    'adindex.ru': 'AdIndex',
}


def display_name(domain):
    if domain in DOMAIN_NAMES:
        return DOMAIN_NAMES[domain]
    # Хвост без карточки в таблице — не изданию имя не выдумываем, подписываем
    # доменом как есть (капитализация первой буквы — минимальный тюнинг, не
    # переименование).
    return domain[:1].upper() + domain[1:] if domain else domain


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
