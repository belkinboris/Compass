# -*- coding: utf-8 -*-
"""`ge8f45161` (РЖД планирует продать 49% ФГК за 44 млрд ₽, январь 2026) —
почасовой приток 2 сентября 2026 нашёл первого публично названного
потенциального претендента: гендиректор лизинговой компании «Трансфин-М»
Дмитрий Алафинов заявил РБК, что компания готова рассмотреть покупку, но
только КОНТРОЛЬНОГО пакета — то есть не 49%, как изначально
планировалось, а более 50%. Это меняет уже описанную в карточке картину
(«наиболее вероятными покупателями называют финансовых инвесторов» — из
прежнего анализа Infoline), а не просто добавляет имя к списку.

Полный текст статьи РБК недоступен для автоматического чтения (401 —
известное ограничение для роботов, не признак мёртвой ссылки, см.
CLAUDE.md); используется собственная лид-цитата RBC из RSS-ленты,
дословно совпадающая с кэшем `data/inbox/raw/2026-09-02-articles.jsonl`.

Дополнение к уже занятому полю `eco.context` — не через review.py (цитата
покрывает только новое предложение, а не старое+новое целиком).

Запуск: python3 pipeline/fix_fgk_transfin_m_control_interest.py           # проверка
        python3 pipeline/fix_fgk_transfin_m_control_interest.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ge8f45161'
OLD_CONTEXT = (
    'Аналитики считают продажу неконтрольного пакета малопривлекательной для '
    'операторов-конкурентов ФГК на фоне убыточной конъюнктуры рынка '
    'оперирования вагонами в 2026 году; наиболее вероятными покупателями '
    'называют финансовых инвесторов с горизонтом 3–5 лет, ориентированных на '
    'дивидендную доходность.'
)
ADDITION = (
    'РЖД рассматривают продажу ФГК. «Трансфин-М» готов войти в число '
    'претендентов, но только если на продажу выставят контрольный пакет, '
    'заявил РБК гендиректор лизинговой компании Алафинов (2 сентября 2026).'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card.get('eco', {}).get('context') == OLD_CONTEXT, (
        'eco.context уже другое: %r' % card.get('eco', {}).get('context'))

    print('ДОБАВЛЕНО: %r' % ADDITION)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['eco']['context'] = NEW_CONTEXT
    src = card.setdefault('src', [])
    rbc_url = 'https://www.rbc.ru/business/02/09/2026/6a97b50a5bd2c4a73a49f137'
    if not any(len(s) > 1 and s[1] == rbc_url for s in src):
        src.append(['РБК', rbc_url])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
