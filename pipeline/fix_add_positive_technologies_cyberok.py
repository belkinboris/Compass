# -*- coding: utf-8 -*-
"""Приток 11 сентября 2026 (08:43 МСК) — реальная сделка, которую ворота
ошибочно спрятали как «нет связи с российским рынком»: обе стороны
(Positive Technologies и CyberOK) — российские компании, но их названия
записаны латиницей, а `russian_evidence()` в promote.py требует либо
кириллического имени стороны, либо явного русского маркера (₽, ООО/АО,
«росс…») — ни того, ни другого в исходном тексте РБК не было, хотя вся
остальная проза дословно русская. Раздел «сырьё» send_drafts.py прячет
такие черновики целиком, не показывая консоли, — родня уже записанного
класса «поиск компании упирается в порог по длине слова», только здесь
порог по НАЛИЧИЮ кириллицы в самом имени, а не по длине.

Найдено при разборе очереди `raw_screen.py` (пункт «не видно связи с
российским рынком») личным чтением исходного сообщения РБК и
независимым подтверждением через WebSearch (Habr — официальный блог
Positive Technologies, CISOClub, Smart-lab, Anti-Malware). Habr —
дословный пресс-релиз самой Positive Technologies (аккаунт `ptsecurity`),
включая прямую цитату управляющего директора Алексея Новикова.

Карточка собрана тем же путём, что и обычный `promote.py` (та же форма
`card`, тот же `new_id()`), а факты внесены `review.py` с дословными
цитатами — расхождений с обычным конвейером нет, кроме самого способа
завести id (вручную, а не через ворота, которые эту сделку отвергли).

Продавец не назван ни в одном источнике 2026 года: кому именно
принадлежала продаваемая доля CyberOK на момент сделки, не раскрыто (устав
компании на момент основания в 2022 году, по данным Anti-Malware, был у
«Большой истории» Маргариты Кондратюк — но это состояние четырёхлетней
давности, переносить его на 2026 год без подтверждения нельзя). Сумма
сделки нигде не раскрыта.

Запуск: python3 pipeline/fix_add_positive_technologies_cyberok.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

SRC_URL = 'https://www.rbc.ru/rbcfreenews/6aa3982a048df5576e86aee5'
DRAFT_ID = 'd33645420'


def main(write=False):
    import promote

    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)

    existing_ids = {c['id'] for c in pending['cards']}
    assert not any('CyberOK' in (c.get('title') or '') for c in pending['cards']), \
        'карточка про CyberOK уже есть в pending.json'

    new_id = promote.new_id(existing_ids)
    card = {
        'id': new_id,
        'date': '2026-09-11',
        'title': 'Positive Technologies приобрела долю в CyberOK',
        'ind': 'ИТ и интернет',
        'type': 'M&A',
        'status': 'Закрыта',
        'src': [['РБК', SRC_URL]],
        'from_ingest': True,
        'eco': {'sum': '—', 'share': '—', 'val': '—', 'target_fin': '—',
                'fin': '—', 'rationale': '—', 'context': '—', 'finadv': '—'},
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        'buyer_name': 'Positive Technologies',
        'asset': 'CyberOK',
        'events': [{
            'kind': 'closed',
            'date': '2026-09-11',
            'title': 'Сделка завершена',
            'note': 'Positive Technologies приобрела долю в компании CyberOK, '
                    'которая разрабатывает решения в области кибербезопасности, '
                    'сообщила РБК пресс-служба компании.',
            'source': ['РБК', SRC_URL],
        }],
    }

    pending['cards'].append(card)
    # Черновик сырья, из которого собрана карточка, отмечаем решённым —
    # иначе send_drafts.py продолжит носить его в консоль отдельным пунктом
    # «сырьё», хотя он уже стал полноценной карточкой.
    state.setdefault('decided_raw', {})[DRAFT_ID] = 'take'

    print('Добавлена карточка %s: Positive Technologies/CyberOK.' % new_id)

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано. Дальше: pipeline/ingest/review.py [--write] с '
              'дословными цитатами, затем --mark-deep и --write.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
