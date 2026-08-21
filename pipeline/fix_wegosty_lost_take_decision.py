# -*- coding: utf-8 -*-
"""17 августа владелец нажал «✅ Признана сделкой — уйдёт в работу» по сырью
`d44072805` (Wegosty/rusven) — approve.py должен был превратить черновик в
карточку предпросмотра и сразу разослать её в консоль (📣+🗂). Она не
появилась НИГДЕ: ни в `pending.json`, ни в `deals_promoted.json` ни разу с
17 августа, а `data/inbox/moderation_state.json` ни разу не нёс `decided_raw`
со значением `take` для этого draft_id (хотя 10 ДРУГИХ решений «в работу» за
тот же период применились нормально — механизм в целом рабочий).

ПОЧЕМУ ТАК ВЫШЛО (реконструкция по коду, без прямого доступа к БД сайта).
`approve.py --write` в один проход: (1) читает решение с сайта, (2) строит
карточку и пишет её В ЛОКАЛЬНЫЙ `pending.json`, (3) тут же вызывает
`/api/moderation/decisions/consume` — сайт помечает решение применённым
НАВСЕГДА. Коммит и push в git — ПОСЛЕДНИЙ шаг рутины «публикация», уже ВНЕ
approve.py, через несколько шагов (send_telegram, полный pytest). Если
контейнер рутины умер МЕЖДУ шагом (3) и git push — а именно так уже терялась
запись «отправлено» у поста про Ленобласть 19 августа, тот же класс сбоя —
локальная карточка и обновлённое состояние исчезают вместе с контейнером, а
решение на сайте уже необратимо помечено применённым: следующий прогон его
больше не увидит и не попробует снова. Раз в git это не попало НИ РАЗУМ за
четыре дня и ~40+ прогонов рутины «публикация» (а другие 10 решений «в
работу» за тот же период применились штатно) — решение потеряно молча, не
дублировано.

ВТОРАЯ, НЕЗАВИСИМАЯ НАХОДКА ПО ДОРОГЕ: пока карточка собиралась заново,
`to_card()` в `promote.py` резолвил подпись источника по домену ссылки
ТОЛЬКО для `web:`-префикса ленты — сырьё «на решение» (кнопка «это сделка»)
приходит с префиксом `tg:`, и то же условие его пропускало: карточка понесла
бы «tg:rusven» вместо «Телеграм-канал: Русский Венчур» на экране. Починено
в `promote.py` отдельно (условие теперь по самой ссылке, не по тегу ленты),
тестом `test_to_card_resolves_telegram_source_label_not_the_feed_id`.

ЧТО В ЭТОМ СКРИПТЕ. Черновик `d44072805` по-прежнему цел в
`data/inbox/hold/*.json` (файлы притока не трогает ничто, кроме самого
притока) — восстанавливаем ровно то решение, которое владелец уже принял:
строим карточку предпросмотра из ТОГО ЖЕ черновика и кладём её в
`pending.json`, как это сделал бы `approve.py`. Разница с механическим
`to_card()` в двух местах — оба сделаны ВРУЧНУЮ, начитано по первоисточнику
(https://t.me/rusven/7666, сырой HTML прочитан напрямую, не пересказ
инструмента-суммаризатора):
  1. заголовок и `asset` — не сырой заголовок ленты (он целым предложением с
     атрибуцией), а короткое имя по правилу «мягких» заголовков новых
     карточек (см. CLAUDE.md, «Модерация притока»);
  2. `eco.*` заполнены дословными кусками текста поста — состав раунда,
     продукт, структура собственности, выручка 2025 — а не оставлены
     заглушками, как их оставил бы голый `to_card()`: раз уж карточка
     собирается заново, собираем её сразу по стандарту качества, который
     владелец просил применять к КАЖДОЙ новой карточке (не «переобогащать»
     потом отдельной кампанией).
`reviewed` ставится честно — источник прочитан целиком, сумма и стороны
дословно лежат в тексте поста.

Второй черновик, `d59961733` (tadviser.ru, «Российская платформа для отелей
и ресторанов Wegosty привлекла 23 млн рублей инвестиций» — та же сумма, та
же компания, другая формулировка), сегодня снова спросил «это сделка?» в
консоли: сработал НЕ баг дедупликации по заголовку (эта точная формулировка
показывалась впервые, `promote.raw_key()` корректно различил её от трёх уже
виденных вариантов), а то, что заголовок был про ТОТ ЖЕ раунд, который уже
получил решение «да» — просто другими словами. tadviser.ru отдаёт 503/404
этой сессии (DDoS-guard), прочитать его дословно не удалось — используется
только как ВТОРАЯ ссылка на ту же новость (сумма и компания совпадают
дословно с уже прочитанным постом, это не домысел), без утверждений из его
текста, которых я не проверил. Оба черновика помечаются решёнными в
`moderation_state.json`, чтобы ни один не спросил снова.

Запуск: python3 pipeline/fix_wegosty_lost_take_decision.py           # проверка
        python3 pipeline/fix_wegosty_lost_take_decision.py --write   # запись
"""
import glob
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))

import promote  # noqa: E402
import source_names  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')
HOLD_DIR = os.path.join(ROOT, 'data', 'inbox', 'hold')

TAKEN_ID = 'd44072805'
COMPANION_ID = 'd59961733'
RUSVEN_URL = 'https://t.me/rusven/7666'
TADVISER_URL = 'https://www.tadviser.ru/a/961816'


def find_draft(draft_id):
    for name in sorted(glob.glob(os.path.join(HOLD_DIR, '*.json'))):
        doc = json.load(open(name, encoding='utf-8'))
        for d in doc.get('drafts', []):
            if str(d.get('draft_id')) == draft_id:
                return d
    return None


def main(write=False):
    draft = find_draft(TAKEN_ID)
    assert draft is not None, '%r не найден в data/inbox/hold — восстанавливать нечего' % TAKEN_ID
    companion = find_draft(COMPANION_ID)
    assert companion is not None, '%r не найден в data/inbox/hold' % COMPANION_ID

    pending = promote.load_pending()
    assert not any('wegosty' in str(c.get('title', '')).lower() for c in pending['cards']), \
        'карточка Wegosty уже в pending.json — скрипт уже применён?'
    data = json.load(open(DATA, encoding='utf-8'))
    assert not any('wegosty' in str(d.get('title', '')).lower() for d in data['deals']), \
        'карточка Wegosty уже в deals_promoted.json — скрипт уже применён?'

    state = promote.load_state()
    assert state.get('decided_raw', {}).get(TAKEN_ID) != 'take', \
        '%r уже отмечен как take в moderation_state.json' % TAKEN_ID

    existing_ids = {c['id'] for c in pending['cards']} | {d['id'] for d in data['deals']}
    deal_id = promote.new_id(existing_ids)

    rusven_label = source_names.edition_label(RUSVEN_URL)
    tadviser_label = source_names.edition_label(TADVISER_URL)

    card = {
        'id': deal_id,
        'date': '2026-08-13',
        'title': 'ИИ-платформа Wegosty привлекла 23 млн ₽ от бизнес-ангелов',
        'ind': 'Искусственный интеллект',
        'type': 'Инвестиция',
        'status': 'Закрыта',
        'src': [[rusven_label, RUSVEN_URL], [tadviser_label, TADVISER_URL]],
        'from_ingest': True,
        'sum': '23 млн ₽',
        'buyer_name': 'Константин Степаненко, Алексей Гончаров, Евгений Степанов, Леонид Мармер',
        'asset': 'Wegosty',
        'eco': {
            'sum': '—',
            'share': '20,57% компании — доля, полученная инвесторами в этом раунде.',
            'val': '—',
            'target_fin': 'WEGOSTY в 2025 году создал Роман Тян. Согласно данным Rusprofile, '
                           'ООО «Гости Путеводители» (юрлицо WEGOSTY) образовано в январе 2025 '
                           'года в Элисте. Роман Тян владеет 85,04% долей, ещё 14,96% '
                           'принадлежит Евгению Степанову. Выручка за 2025 год составила '
                           '1,35 млн рублей.',
            'fin': '—',
            'rationale': 'Стартап разработал ИИ-платформу для ресторанов, отелей и '
                         'туристической отрасли. Решение автоматизирует весь путь гостя: от '
                         'первого обращения до бронирования и оплаты. Платформа объединяет '
                         'ИИ-ресепшн, систему онлайн-бронирования и оплаты, инструменты '
                         'привлечения гостей через партнёрские каналы и мобильный '
                         'гастронавигатор. Продукт интегрируется с ключевыми отраслевыми '
                         'системами, включая iiko и Bnovo. Задача компании — помочь объектам '
                         'HoReCa получать больше бронирований при меньших операционных '
                         'затратах и создать единую независимую ИИ-инфраструктуру для '
                         'российского рынка.',
            'context': 'В раунде участвовали: сооснователь сервиса доставки «Самокат», '
                       'гендиректор гостиничной IT-платформы Bnovo Константин Степаненко, '
                       'основатель проектов MIL Team и CompressaAI Алексей Гончаров, частный '
                       'инвестор Евгений Степанов и экс-глава «Интуриста» и Amadeus Россия '
                       'Леонид Мармер.',
            'finadv': '—',
        },
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        'reviewed': '2026-08-21',
    }

    print('ВОССТАНАВЛИВАЕМ решение владельца от 17 августа: %s -> предпросмотр %s'
          % (TAKEN_ID, deal_id))
    print('  %s' % card['title'])
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    now = datetime.now(timezone.utc)
    card['pending_since'] = now.isoformat(timespec='seconds')
    pending['cards'].append(card)
    promote.save_pending(pending)

    state.setdefault('decided_raw', {})[TAKEN_ID] = 'take'
    state.setdefault('raw_titles', {})[promote.raw_key(draft.get('title'))] = 'take'
    state.setdefault('decided_raw', {})[COMPANION_ID] = 'take'
    state.setdefault('raw_titles', {})[promote.raw_key(companion.get('title'))] = 'take'
    promote.save_state(state)
    print('Записано: pending.json + moderation_state.json.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
