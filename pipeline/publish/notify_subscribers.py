#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Приток, шаг 5: личное уведомление подписчику о подходящей ему сделке.

ГДЕ ЖИВЁТ САМО ПРАВИЛО. В `subscription_feed.py` рядом с приложением: сверку
подписок делает САЙТ на старте после деплоя, потому что база пользователей
стоит во внутренней сети хостинга и из контейнера притока недостижима. Этот
файл — командная строка к тем же правилам: посмотреть, кому что ушло бы,
и замерить правило на своей базе, не поднимая сайт.

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
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import subscription_feed  # noqa: E402

KIND = subscription_feed.KIND
PLACEHOLDER = subscription_feed.PLACEHOLDER
amount_mln_rub = subscription_feed.amount_mln_rub
haystack = subscription_feed.haystack
match_reason = subscription_feed.match_reason
notify_new_deals = subscription_feed.notify_new_deals
_self_check = subscription_feed.self_check


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
