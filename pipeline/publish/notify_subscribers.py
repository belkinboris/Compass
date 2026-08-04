#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Приток, шаг 5: личное уведомление подписчику о подходящей ему сделке.

ЧТО БЫЛО СЛОМАНО. Подписка («сообщи о сделках в отрасли X от суммы Y»)
сохранялась (`SavedFilter`), показывалась в кабинете и удалялась — но НИКТО
никогда не сверял её с новыми сделками. Интерфейс при сохранении подборки
пишет «Новые совпадения появятся в уведомлениях», и это обещание не
выполнялось ни разу: во всём коде не было ни одного места, читающего
`saved_filters` иначе, чем ради показа списка самому владельцу. Личные
уведомления доходили только до тех, кто подписан на КОНКРЕТНУЮ сделку
(`DealWatch`, шлёт `enrich.py`), — то есть только про обновление уже
известной карточки, но никогда про появление новой.

СОБЫТИЕ, А НЕ ОБХОД БАЗЫ. Уведомления шлются в тот момент, когда карточка
попадает в базу (`promote.py`), а не сканированием всей базы по расписанию.
Так подписка честно означает «сообщи о будущем»: подписавшийся сегодня не
получает пачку из полутора тысяч исторических сделок, а сканирование
потребовало бы отдельного состояния «о чём уже сообщали» — того самого,
которое у канала лежит в git-файле и на боевом хосте потерялось бы при
деплое (см. CLAUDE.md про `telegram_posts`). Здесь состояние не нужно
вовсе: «уже сообщали» — это существующая строка `Notification` с тем же
`deal_id` у того же пользователя.

ПОРОГ СУММЫ МОЛЧИТ, КОГДА НЕ УВЕРЕН. Сумма в карточке — свободный текст
(«200–550 млн ₽ (по оценке)», «~4,5–5 млрд ₽», «Не раскрыта», «$1,2 млрд»).
Если разобрать её в млн ₽ не удалось, подписка с порогом суммы НЕ
срабатывает: лучше не прислать письмо, чем прислать не по адресу — то же
правило «ошибка дороже молчания», что у разбора новостей. По той же причине
из диапазона берётся НИЖНЯЯ граница: подписка «от 500 млн» не должна
срабатывать на сделке, которая может стоить 200.

ВАЛЮТА НЕ КОНВЕРТИРУЕТСЯ. Курса в базе нет и выдумывать его нельзя, поэтому
«$1,2 млрд» для порога в рублях — неизвестная величина, а не 100 млрд ₽.
Признак рубля — значок `₽` после единицы (соглашение о записи суммы), и
именно он делает разбор однозначным.

ЧЕСТНОСТЬ ДОСТАВКИ. Скрипт печатает, в какую базу он писал. Прогон в
одноразовом контейнере без `DATABASE_URL` работает с локальным файлом
`kompas.db`, которого там нет, — «уведомлений создано: 0» в этом случае
значит не «подписчиков нет», а «мы смотрели не в ту базу», и это прямо
сказано в отчёте. Тихо считать такой прогон успешным нельзя: это ровно тот
случай, когда «готово» подменяет «мы перестали пытаться».

Запуск:
    python3 pipeline/publish/notify_subscribers.py                # состояние и самопроверка
    python3 pipeline/publish/notify_subscribers.py --deal <id>    # кому ушло бы по этой карточке
    python3 pipeline/publish/notify_subscribers.py --deal <id> --write   # отправить
    python3 pipeline/publish/notify_subscribers.py --measure --industry "ИТ и интернет" --min 500
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

KIND = 'subscription_match'

# Заглушки суммы. Анкерим с обеих сторон: «не раскрыта (EV оценена в 21 млрд ₽)»
# — это данные, а не пустота (урок из CLAUDE.md).
PLACEHOLDER = re.compile(
    r'^\s*(?:не\s+раскрыт[а-яё]*|публично\s+не\s+сообщал[а-яё]*|'
    r'не\s+привлекал[а-яё]*|нет\s+данных|[—–-])\s*$', re.I)

UNITS = {'тыс': 0.001, 'млн': 1.0, 'млрд': 1000.0, 'трлн': 1000000.0}

# Пробел внутри числа — разделитель разрядов («41 500 млн ₽»), а запятая —
# десятичная часть («12,5 млрд»). Значок ₽ обязателен: он и есть признак того,
# что число рублёвое, — у долларов и евро значок стоит ПЕРЕД числом и сюда не
# попадёт.
NUM = r'\d[\d\s\u00a0]*(?:[.,]\d+)?'
AMOUNT = re.compile(
    r'(' + NUM + r')\s*\+?'                  # число; «300+ млн» — это тоже нижняя граница
    r'(?:\s*[\u2013\u2014-]\s*' + NUM + r')?'  # верхняя граница диапазона — её не берём
    r'\s*(?:(тыс|млн|млрд|трлн)[а-яё.]*\s*)?'  # единицы может и не быть
    r'\u20bd')                           # и обязательный значок рубля

# Сумма без единицы — это рубли («450 090 ₽», «1 ₽» у символических сделок).
UNIT_NONE = 1e-6


def amount_mln_rub(text):
    """Сумма карточки в млн ₽ или None, если разобрать нельзя."""
    if not text or PLACEHOLDER.match(text):
        return None
    found = AMOUNT.search(text)
    if not found:
        return None
    raw = re.sub(r'[\s\u00a0]', '', found.group(1)).replace(',', '.')
    try:
        value = float(raw)
    except ValueError:
        return None
    return value * (UNITS[found.group(2)] if found.group(2) else UNIT_NONE)


def _self_check():
    """Правило проверяется на себе, а не на глаз (соглашение репозитория)."""
    assert amount_mln_rub('12,5 млрд ₽') == 12500.0
    assert amount_mln_rub('41 500 млн ₽') == 41500.0
    # Из диапазона — нижняя граница, тильда и «(по оценке)» не мешают.
    assert amount_mln_rub('200–550 млн ₽ (по оценке)') == 200.0
    assert amount_mln_rub('~4,5–5 млрд ₽ (по оценке)') == 4500.0
    # Валюта не конвертируется, заглушка — не число.
    assert amount_mln_rub('$1,2 млрд') is None
    assert amount_mln_rub('€800 млн') is None
    assert amount_mln_rub('Не раскрыта') is None
    assert amount_mln_rub('не раскрыта') is None
    # А вот это не заглушка: сумма названа в скобках и должна читаться.
    assert amount_mln_rub('Не раскрыта (EV оценена в 21 млрд ₽)') == 21000.0
    # Рублёвая часть берётся, даже когда рядом стоит пересчёт в валюте.
    assert amount_mln_rub('17,7 млрд ₽ (191,5 млн $)') == 17700.0
    # Без единицы значок ₽ значит рубли, а не миллионы: «1 ₽» — символическая
    # цена, и подписка «от 500 млн» на неё сработать не должна.
    assert amount_mln_rub('450 090 ₽') == 0.45009
    assert amount_mln_rub('2 800 000 000 ₽') == 2800.0
    assert amount_mln_rub('1 ₽') == 1e-6
    # «300+ млн» — тоже нижняя граница, а не незнакомая запись.
    assert amount_mln_rub('300+ млн ₽') == 300.0
    assert amount_mln_rub('1+ млрд ₽') == 1000.0
    # А вот тут числа нет вовсе — молчим, а не угадываем «несколько».
    assert amount_mln_rub('несколько сотен млн ₽ (по оценке)') is None
    assert amount_mln_rub('несколько млрд ₽ (точно не указана)') is None


def company_names(deal, companies):
    """Имена профилей, на которые ссылается карточка."""
    names = []
    for field in ('buyer', 'target', 'seller_id', 'asset_id'):
        profile = companies.get(deal.get(field) or '')
        if profile and profile.get('name'):
            names.append(profile['name'])
    return names


def haystack(deal, companies):
    """Текст, по которому ищется ключевое слово подписки.

    Только НАЗВАНИЯ и заголовок — не всё содержимое карточки: подписка на
    «Сбер» не должна срабатывать оттого, что банк упомянут в пояснении как
    кредитор чужой сделки.
    """
    parts = [deal.get('title') or '', deal.get('seller') or '',
             deal.get('buyer_name') or '', deal.get('asset') or '']
    parts.extend(company_names(deal, companies))
    return ' | '.join(parts).lower()


def match_reason(flt, deal, companies):
    """Почему эта сделка подходит подписке. None — не подходит.

    Условия складываются по И: подписка «отрасль X + от Y» — это про сделки в
    X дороже Y, а не про объединение двух лент.
    """
    reasons = []
    industry = (getattr(flt, 'industry', None) or '').strip()
    keyword = (getattr(flt, 'keyword', None) or '').strip()
    floor = getattr(flt, 'min_amount_mln_rub', None)

    if not industry and not keyword and floor is None:
        return None  # подписки «на всё» не бывает, её не даёт создать и API

    if industry:
        if (deal.get('ind') or '') != industry:
            return None
        reasons.append('отрасль «%s»' % industry)
    if keyword:
        if keyword.lower() not in haystack(deal, companies):
            return None
        reasons.append('упоминание «%s»' % keyword)
    if floor is not None:
        value = amount_mln_rub(deal.get('sum'))
        if value is None or value < float(floor):
            return None
        reasons.append('сумма от %s млн ₽' % _num(float(floor)))
    return ', '.join(reasons)


def _num(value):
    return ('%.0f' % value) if abs(value - round(value)) < 1e-9 else ('%.1f' % value)


def database_is_local_file():
    """Пишем в одноразовый файл рядом с кодом, а не в базу сайта."""
    return not (os.environ.get('DATABASE_URL') or '').strip()


def notify_new_deals(db, deals, companies, base_url=None):
    """Разослать уведомления по подпискам о ТОЛЬКО ЧТО добавленных карточках.

    Возвращает счётчики; ничего не печатает — за отчёт отвечает вызывающий.
    """
    from sqlalchemy import select

    import notification_service
    from db.models import Notification, SavedFilter, User

    base = (base_url or os.environ.get('APP_BASE_URL') or 'https://projectcompass.ru').rstrip('/')
    filters = list(db.scalars(select(SavedFilter).where(SavedFilter.active.is_(True))).all())
    stats = {'filters': len(filters), 'subscribers': len({f.user_id for f in filters}),
             'deals': len(deals), 'created': 0, 'repeat': 0}

    for deal in deals:
        # Одному человеку — одно уведомление о сделке, даже если совпали две
        # его подписки: читателю важна сделка, а не то, сколько его фильтров
        # на неё среагировало.
        hits = {}
        for flt in filters:
            reason = match_reason(flt, deal, companies)
            if reason:
                hits.setdefault(flt.user_id, []).append(reason)
        for user_id, reasons in hits.items():
            seen = db.scalar(select(Notification).where(
                Notification.user_id == user_id,
                Notification.deal_id == deal['id'],
                Notification.kind == KIND))
            if seen:
                stats['repeat'] += 1
                continue
            user = db.get(User, user_id)
            if not user:
                continue
            notification_service.create_notification(
                db, user,
                title='Новая сделка по вашей подписке: %s' % (deal.get('title') or deal['id']),
                body='Совпало: %s.' % '; '.join(sorted(set(reasons))),
                link='%s/#/deal/%s' % (base, deal['id']),
                deal_id=deal['id'], kind=KIND)
            stats['created'] += 1
    return stats


def report(stats):
    """Отчёт, который нельзя прочитать как успех, когда база не та."""
    lines = ['Подписок активных: %d (людей: %d), новых карточек: %d'
             % (stats['filters'], stats['subscribers'], stats['deals']),
             'Уведомлений создано: %d, повторов пропущено: %d'
             % (stats['created'], stats['repeat'])]
    if database_is_local_file() and not stats['filters']:
        lines.append('ВНИМАНИЕ: DATABASE_URL не задан — читали локальный файл '
                     'kompas.db, а не базу сайта. «Подписок 0» здесь значит '
                     '«смотрели не туда», а не «подписчиков нет». Для прогона в '
                     'одноразовом контейнере это ожидаемо — чинить здесь нечего.')
    return '\n'.join(lines)


def main(argv):
    _self_check()
    data = json.load(open(DATA, encoding='utf-8'))
    deals, companies = data['deals'], data['companies']

    if '--measure' in argv:
        flt = type('Spec', (), {
            'industry': _opt(argv, '--industry'),
            'keyword': _opt(argv, '--keyword'),
            'min_amount_mln_rub': float(_opt(argv, '--min')) if _opt(argv, '--min') else None,
        })()
        hit = [d for d in deals if match_reason(flt, d, companies)]
        print('Подходит карточек: %d из %d' % (len(hit), len(deals)))
        for deal in hit[:10]:
            print('  %s — %s' % (str(deal.get('title'))[:70], deal.get('sum')))
        unparsed = sum(1 for d in deals if d.get('sum') and amount_mln_rub(d['sum']) is None)
        print('Сумма не разобрана у %d карточек из %d с непустой суммой — по порогу '
              'суммы они молчат.' % (unparsed, sum(1 for d in deals if d.get('sum'))))
        return 0

    wanted = _opt(argv, '--deal')
    picked = [d for d in deals if d['id'] == wanted] if wanted else []
    if wanted and not picked:
        print('Карточки %s в базе нет.' % wanted)
        return 1

    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    try:
        from db.session import SessionLocal
    except Exception as exc:
        print('База недоступна: %s' % exc)
        return 1

    with SessionLocal() as db:
        if '--write' in argv and picked:
            stats = notify_new_deals(db, picked, companies)
        else:
            # Сухой прогон: считаем совпадения, ничего не создавая.
            from sqlalchemy import select

            from db.models import SavedFilter
            filters = list(db.scalars(select(SavedFilter).where(SavedFilter.active.is_(True))).all())
            stats = {'filters': len(filters), 'subscribers': len({f.user_id for f in filters}),
                     'deals': len(picked), 'created': 0, 'repeat': 0}
            for deal in picked:
                for flt in filters:
                    reason = match_reason(flt, deal, companies)
                    if reason:
                        print('  ушло бы пользователю %d: %s' % (flt.user_id, reason))
            if picked and not filters:
                print('  подходящих подписок нет')
        print(report(stats))
        if not picked:
            print('Карточка не указана — это только сводка. Разбор суммы проверен '
                  'самопроверкой, она прошла.')
        elif '--write' not in argv:
            print('Сухой прогон. Отправка — с ключом --write.')
    return 0


def _opt(argv, name):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else None


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
