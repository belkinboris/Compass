# -*- coding: utf-8 -*-
"""Публикация в Telegram: один пост на сделку, обновление — правкой поста.

ЗАЧЕМ. Об одной сделке пишут пять изданий за два дня. Пять постов об одном и
том же — это спам, поэтому правило простое: одна сделка — один пост. Появился
новый факт (сумма, сторона, консультант) — тот же пост редактируется, а внизу
появляется строка «⟳ Обновлено: …». Уведомление о правке приходит НЕ всегда:
только когда изменилось то, ради чего пост читают.

ЧТО СЧИТАЕТСЯ ЗНАЧИМЫМ (`SIGNIFICANT`). Сумма, покупатель, продавец, предмет,
статус сделки и консультанты. Появление такого факта — повод для короткого
уведомления ответом на пост. Всё остальное (уточнение формулировки, ещё один
источник, отрасль) правит пост молча. Отдельно оговорено закрытие сделки:
переход статуса в «Закрыта» — событие, а не переформулировка, и о нём
уведомляем.

ПОЧЕМУ НЕ НОВЫЙ ПОСТ НА КАЖДОЕ ОБНОВЛЕНИЕ. Лента должна оставаться списком
сделок, а не списком новостей: юрист ищет «что было со сделкой X», а не «что
писали в среду». Пост со сделкой — это её карточка в телеграме, и она живёт
столько же, сколько карточка на сайте.

ЧТО ЭТОТ МОДУЛЬ НЕ ДЕЛАЕТ. Он ничего не отправляет: отправка — отдельный шаг,
которому нужен токен бота и который живёт там, где есть сеть. Здесь только
текст, разбор изменений и решение «уведомлять или нет» — всё это чистые
функции, и потому проверяются тестами без сети.

Запуск (пример поста по случайной карточке базы):
    python3 pipeline/publish/format_post.py --sample
"""
import json
import os
import re
import sys
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
# Адрес витрины, который уходит в ссылки телеграм-поста. Домен был вписан
# в код числом — и не тот: сайт живёт на projectcompass.ru, а посты вели бы
# читателя на kompas.deals. Берём из переменной окружения `APP_BASE_URL` (той
# же, что уже используется для ссылок из писем), а вписанное значение — лишь
# запасное на случай, если переменная не задана.
SITE = (os.environ.get('APP_BASE_URL') or 'https://projectcompass.ru').rstrip('/')

SIGNIFICANT = ('sum', 'buyer', 'buyer_name', 'seller', 'target', 'asset', 'status', 'advisers', 'events')

PLACEHOLDER = re.compile(
    r'^\s*(?:[—-]|н/д|нет\s+данных|не\s+раскры[а-яё]*|не\s+привлекал[а-яё]*'
    r'|(?:публично|официально)\s+не\s+[а-яё]+)\s*\.?\s*$', re.I)


def has(value):
    v = re.sub(r'\s+', ' ', str(value or '')).strip()
    return bool(v) and not PLACEHOLDER.match(v)


def esc(text):
    return (str(text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def party_names(deal, companies):
    """Стороны так, как их видит читатель: имя из профиля либо имя текстом."""
    def name(ref, text):
        if ref and companies.get(ref):
            return companies[ref]['name']
        return text if has(text) else None
    seller = name(deal.get('seller_id'), deal.get('seller'))
    buyer = name(deal.get('buyer'), deal.get('buyer_name'))
    asset = name(deal.get('target'), deal.get('asset'))
    if not asset and deal.get('asset_id') and companies.get(deal['asset_id']):
        asset = companies[deal['asset_id']]['name']
    return seller, asset, buyer


def advisers(deal):
    out = []
    for row in ((deal.get('law') or {}).get('adv') or []):
        if isinstance(row, (list, tuple)) and len(row) > 1 and has(row[1]):
            out.append(str(row[1]).strip())
    fin = (deal.get('eco') or {}).get('finadv')
    if has(fin):
        out += [x.strip().split('—')[0].strip() for x in str(fin).split(';') if x.strip()]
    seen, uniq = set(), []
    for a in out:
        if a.lower() not in seen:
            seen.add(a.lower())
            uniq.append(a)
    return uniq


MONTHS_OF = ('январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
             'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь')


def fmt_day(raw):
    """«2026-08-06» -> «6 августа 2026». Пусто — если даты нет или она неполная."""
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', str(raw or ''))
    if not m:
        return ''
    of = ('января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
          'августа', 'сентября', 'октября', 'ноября', 'декабря')
    month = int(m.group(2))
    if not 1 <= month <= 12:
        return ''
    return '%d %s %s' % (int(m.group(3)), of[month - 1], m.group(1))


def fmt_month(raw):
    """«2026-06-26» -> «июнь 2026», «2024» -> «2024 год». Пусто — если неясно."""
    raw = str(raw or '')
    if re.fullmatch(r'\d{4}', raw):
        return '%s год' % raw
    m = re.fullmatch(r'(\d{4})-(\d{2})-\d{2}', raw)
    if not m:
        return ''
    month = int(m.group(2))
    return '%s %s' % (MONTHS_OF[month - 1], m.group(1)) if 1 <= month <= 12 else m.group(1)


# Сколько дней сделка считается свежей новостью. Дальше пост читается не как
# объявление о сделке, а как сообщение о новых сведениях по известной сделке.
FRESH_DAYS = 30


def deal_age_days(deal, today=None):
    """Сколько дней сделке. None — если дату разобрать нельзя (год без дня)."""
    raw = str(deal.get('date') or '')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', raw):
        return None
    try:
        made = datetime.strptime(raw, '%Y-%m-%d').date()
    except ValueError:
        return None
    return ((today or date.today()) - made).days


def is_fresh(deal, today=None):
    """Свежая сделка — обычный пост. Старая — «новое о сделке».

    ЗАЧЕМ. Правило публикации смотрело, видел ли карточку КАНАЛ, а не что
    нового узнали МЫ. Из-за этого 4 августа в канал ушли посты о сделках 26
    июня, 15 июня и 1 марта 2025 года — каждый читался как объявление о свежей
    сделке, хотя поводом было дописанное обогащением поле. Читателю канала
    нужны новости, а не выдача архива за новость.

    Дата, у которой известен только год, свежей не считается: если мы не знаем
    даже месяца, объявлять сделку сегодняшней нельзя.
    """
    age = deal_age_days(deal, today)
    return age is not None and age <= FRESH_DAYS


def render(deal, companies, updates=(), today=None):
    """Текст поста (HTML для Telegram). Пустых строк-заглушек в посте нет."""
    seller, asset, buyer = party_names(deal, companies)
    lines = []
    if not is_fresh(deal, today):
        # Старая сделка: сначала честно говорим, что это не свежая новость, и
        # называем ЕЁ дату — иначе читатель примет архив за сегодняшний рынок.
        #
        # ЗАГОЛОВОК ЗАВИСИТ ОТ ТОГО, ЕСТЬ ЛИ ЧТО СКАЗАТЬ. 7 августа в канал ушёл
        # пост «Новое о сделке · май 2026» про «Обсидиан», в котором ничего
        # нового не сообщалось, — владелец справедливо спросил, что же в ней
        # новое. Ответ: ничего, просто карточка впервые дошла до канала.
        # Обещать новизну там, где её нет, нельзя; но и молчать о том, почему
        # сделка мая всплыла в августе, тоже — поэтому называем дату появления
        # карточки в базе, это проверяемый факт (поле `added`).
        when = fmt_month(deal.get('date'))
        if updates:
            lines.append('🗂 <b>Новое о сделке</b>%s' % (' · %s' % esc(when) if when else ''))
            lines.append('Что стало известно: %s' % esc(', '.join(updates)))
        else:
            lines.append('🗂 <b>Сделка из базы</b>%s' % (' · %s' % esc(when) if when else ''))
            added = fmt_day(deal.get('added'))
            lines.append('Публикуем впервые%s.'
                         % (' — карточка появилась в «Компасе» %s' % esc(added) if added else ''))
        lines.append('')
    lines.append('<b>%s</b>' % esc(deal.get('title')))

    parties = []
    if seller:
        parties.append('Продавец: %s' % esc(seller))
    if asset:
        parties.append('Предмет: %s' % esc(asset))
    if buyer:
        parties.append('Покупатель: %s' % esc(buyer))
    if parties:
        lines.append('')
        lines += parties

    facts = []
    if has(deal.get('sum')):
        facts.append('Сумма: %s' % esc(deal['sum']))
    if has(deal.get('status')):
        facts.append('Статус: %s' % esc(deal['status']))
    if has(deal.get('ind')):
        facts.append('Отрасль: %s' % esc(deal['ind']))
    if facts:
        lines.append('')
        lines += facts

    adv = advisers(deal)
    if adv:
        lines.append('')
        lines.append('Консультанты: %s' % esc(', '.join(adv[:6])))

    src = [s for s in (deal.get('src') or []) if len(s) > 1 and str(s[1]).startswith('http')]
    lines.append('')
    lines.append('<a href="%s/#/deal/%s">Карточка сделки</a>' % (SITE, deal['id']))
    # Прямые ссылки на линзу — только когда там правда что-то есть: иначе
    # читатель кликает «Юрист» и попадает на приглушённую пустую вкладку.
    eco, law = (deal.get('eco') or {}), (deal.get('law') or {})
    if facts or has(eco.get('share')) or has(eco.get('rationale')):
        lines.append('<a href="%s/#/deal/%s?lens=eco">→ Экономист</a>' % (SITE, deal['id']))
    if adv or has(law.get('struct')) or has(law.get('appr')) or has(law.get('terms')):
        lines.append('<a href="%s/#/deal/%s?lens=law">→ Юрист</a>' % (SITE, deal['id']))
    if src:
        lines.append('Источник: <a href="%s">%s</a>' % (esc(src[0][1]), esc(src[0][0])))
        if len(src) > 1:
            lines.append('Ещё источников: %d' % (len(src) - 1))

    # «⟳ Обновлено» — для ПРАВКИ уже опубликованного поста. У старой сделки то
    # же самое уже сказано шапкой «Новое о сделке», и повторять незачем.
    if updates and is_fresh(deal, today):
        lines.append('')
        lines.append('⟳ Обновлено: %s' % esc(', '.join(updates)))

    # Хештег — из названия отрасли и типа как есть: регистр не трогаем, иначе
    # «#ИТиинтернет» превращается в нечитаемое «#итиинтернет».
    tag = lambda s: '#' + re.sub(r'[^\wА-Яа-яЁё]+', '', str(s or ''))
    tags = [tag(deal.get('ind'))]
    if has(deal.get('type')):
        tags.append(tag(str(deal['type']).split('·')[0]))
    lines.append('')
    lines.append(' '.join(t for t in tags if len(t) > 1))
    return '\n'.join(lines)


def render_milestone(deal, event):
    """Текст ОТДЕЛЬНОГО поста-вехи (раздел A, 22 августа) — не правка живого
    поста, а новое сообщение об одном подтверждённом этапе сделки
    (`review.POSTWORTHY_MILESTONE_KINDS`: согласование, закрытие, срыв).

    ЧЕСТНОСТЬ МОМЕНТА. Поля берутся из СНИМКА события (`event['snapshot']`,
    записан `review.build_snapshot()` в момент `--milestone`), а не из
    текущих полей сделки: к моменту публикации карточка могла обогатиться
    более поздними фактами (например, уточнённой ценой закрытия), а веха
    обязана честно показывать то, что было известно НА МОМЕНТ ЭТОГО ЭТАПА,
    а не задним числом — тот же принцип, что и у панели «Карточка на
    момент этого этапа» на странице этапа.
    """
    snap = event.get('snapshot') or {}
    lines = ['📌 <b>%s</b>' % esc(event.get('headline') or '')]
    lines.append('')
    lines.append('Сделка: %s' % esc(snap.get('title') or deal.get('title')))

    parties = []
    if has(snap.get('seller')):
        parties.append('Продавец: %s' % esc(snap['seller']))
    if has(snap.get('asset')):
        parties.append('Предмет: %s' % esc(snap['asset']))
    if has(snap.get('buyer')):
        parties.append('Покупатель: %s' % esc(snap['buyer']))
    if parties:
        lines.append('')
        lines += parties

    facts = []
    if has(snap.get('sum')):
        facts.append('Сумма: %s' % esc(snap['sum']))
    if has(snap.get('status')):
        facts.append('Статус: %s' % esc(snap['status']))
    if facts:
        lines.append('')
        lines += facts

    lines.append('')
    lines.append('<a href="%s/#/deal/%s">Карточка сделки</a>' % (SITE, deal['id']))
    return '\n'.join(lines)


def changes(old, new):
    """Что изменилось между версиями карточки — человеческими словами."""
    label = {'sum': 'сумма', 'buyer': 'покупатель', 'buyer_name': 'покупатель',
             'seller': 'продавец', 'target': 'предмет сделки', 'asset': 'предмет сделки',
             'status': 'статус', 'advisers': 'консультанты', 'events': 'этап сделки'}
    out = []
    for field in SIGNIFICANT:
        was = old.get(field) if field != 'advisers' else advisers(old)
        now = new.get(field) if field != 'advisers' else advisers(new)
        if field not in ('advisers', 'events'):
            was, now = (was if has(was) else None), (now if has(now) else None)
        if field == 'events':
            # Сравниваем только виды этапов: повторная публикация о том же
            # закрытии добавит источник, но не должна считаться новым этапом.
            kinds = lambda rows: tuple(e.get('kind') for e in (rows or []) if isinstance(e, dict))
            was, now = kinds(was), kinds(now)
        if was == now:
            continue
        # Закрытие сделки — не переформулировка, а событие: сделка, о которой
        # писали «обсуждается», состоялась. По общему правилу это считалось
        # «уточнением статуса» и проходило молча — то есть самое важное
        # обновление было единственным, о котором читатель не узнавал.
        if field == 'status' and str(now) == 'Закрыта':
            out.append('сделка закрыта')
            continue
        if field == 'events' and len(now) > len(was):
            out.append('добавлен этап сделки')
            continue
        text = label[field]
        out.append(('добавлен(а) ' + text) if not was else ('уточнён(а) ' + text))
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def should_notify(change_list):
    """Уведомлять ответом на пост — только когда факт ДОБАВИЛСЯ, а не уточнился.

    Иначе каждая правка формулировки будила бы читателя. Уточнение видно в
    самом посте строкой «⟳ Обновлено», и этого достаточно.

    Исключение одно и оно по смыслу такое же: «сделка закрыта» — это появление
    факта, а не другая формулировка прежнего.
    """
    return any(c.startswith('добавлен') or c == 'сделка закрыта' for c in change_list)


def sample():
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    rich = [d for d in data['deals']
            if has(d.get('sum')) and (d.get('seller') or d.get('seller_id'))
            and ((d.get('law') or {}).get('adv'))]
    deal = rich[0]
    print(render(deal, comps))
    print('\n' + '-' * 60)
    older = json.loads(json.dumps(deal))
    older['sum'] = '—'
    older['law']['adv'] = []
    ch = changes(older, deal)
    print('изменения:', ch, '| уведомлять:', should_notify(ch))
    print('-' * 60)
    print(render(deal, comps, updates=ch))


if __name__ == '__main__':
    if '--sample' in sys.argv:
        sample()
    else:
        print(__doc__)
