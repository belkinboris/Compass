# -*- coding: utf-8 -*-
"""Одна таблица «домен -> имя издания» на все скрипты.

Родилась в `relabel_dealsma_sources.py` (переподпись 836 ссылок с
«@dealsma (Telegram)» на имя издания по домену) и была нужна снова, когда
приток начал подписывать источники служебным id ленты («web:kommersant.ru»)
прямо на экран. Правка владельца 6 августа: подпись источника — имя
издания, а не внутренний идентификатор. Держать таблицу в двух скриптах —
готовый баг (см. урок про пять мест хранения одних данных), поэтому она
вынесена сюда, а оба потребителя импортируют.

Для домена вне таблицы имя не выдумывается: подписью становится сам домен
с заглавной буквы («Eqiva.ru») — честная запись того, что стоит в ссылке.
"""
from urllib.parse import urlparse

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
    'thebell.io': 'The Bell',
    'iz.ru': 'Известия',
    'rb.ru': 'RB.ru',
    'akm.ru': 'АК&М',
    'cnews.ru': 'CNews',
    'comnews.ru': 'ComNews',
    'rambler.ru': 'Рамблер',
    'finance.rambler.ru': 'Рамблер',
    'news.rambler.ru': 'Рамблер',
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
    'ria.ru': 'РИА Новости',
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
    # Издания, пришедшие с притоком (лент у них раньше не было).
    'mergers.ru': 'Mergers.ru',
    'ura.news': 'URA.RU',
    'incrussia.ru': 'Inc. Russia',
}


def display_name(domain):
    if domain in DOMAIN_NAMES:
        return DOMAIN_NAMES[domain]
    return domain[:1].upper() + domain[1:] if domain else domain


# Телеграм-каналы — тот же дефект, что уже чинили для «web:kommersant.ru»
# (докстрока выше), повторился 18 августа для «tg:»: домен t.me не несёт
# имени канала (в адресе только @username), поэтому карточка ПСБ/«Атом»
# несла подписью «tg:rusven» — внутренний id ленты (build_sources.py), а
# не имя. Известные каналы подписаны по имени, неизвестные — честно как
# «Телеграм-канал @username», не выдумывая название.
TELEGRAM_CHANNEL_NAMES = {
    'rusven': 'Русский Венчур',
    # Имя уже стояло верно в верхнеуровневом `src` тех же карточек
    # («Сделки M&A (@dealsma)») — здесь просто та же информация, без
    # повторного «(@dealsma)»: его добавляет сам telegram_channel_label().
    'dealsma': 'Сделки M&A',
}


def telegram_channel_label(username):
    name = TELEGRAM_CHANNEL_NAMES.get(str(username or '').lower())
    return 'Телеграм-канал: %s' % name if name else 'Телеграм-канал @%s' % username


def edition_label(url):
    """Имя издания по адресу статьи; www. отрезается до поиска в таблице."""
    parsed = urlparse(str(url))
    host = (parsed.hostname or '').lower()
    if host.startswith('www.'):
        host = host[4:]
    if host == 't.me':
        username = parsed.path.strip('/').split('/')[0]
        if username:
            return telegram_channel_label(username)
    return display_name(host)
