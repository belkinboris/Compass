# -*- coding: utf-8 -*-
"""Приток 23 сентября 2026: суд признал недействительной продажу 99,9%
ООО «Инфамед» (владелец прав на антисептики «Мирамистин» и «Окомистин»)
от Ирины Хугаевой Виталию Николаеву (январь 2025) и вернул доли по
результатам параллельного спора — 50% Оксане Хейфиц (которой Хугаева
ещё в декабре 2024 продала эту долю, законность договора подтверждена
судами трёх инстанций), 49,9% обратно Хугаевой. Источник: ПРАЙМ.

Запуск: python3 pipeline/build_infamed_miramistin_card_2026_09_23.py --write
"""
import argparse
import json
import os
import sys

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(PIPELINE_DIR)
sys.path.insert(0, os.path.join(PIPELINE_DIR, 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
SRC_URL = 'https://1prime.ru/20260923/sud-873593047.html'

QUOTE_MAIN = (
    'Суд признал незаконной продажу бывшей единоличной собственницей ООО "Инфамед", '
    'владеющего правами на антисептики "Мирамистин" и "Окомистин", Ириной Хугаевой '
    '99,9% компании ее тогдашнему гендиректору Виталию Николаеву и передал 50% '
    'компании Оксане Хейфиц, сообщил РИА Новости источник, знакомый с ходом '
    'разбирательства.'
)

QUOTE_LAWSUIT = (
    'В этом иске, поданном в феврале прошлого года, Оксана и Павел Хейфицы '
    'потребовали признать недействительным договор от 27 января 2025 года, по '
    'которому Хугаева продала Николаеву 99,9% компании, и попросили применить '
    'последствия недействительности сделки в виде возвращения этой доли Хугаевой. '
    'Как пояснил источник, требование о применении последствий суд удовлетворил '
    'частично, а именно вернул Хугаевой 49,9%, а 50% передал Хейфиц.'
)

QUOTE_PRIOR_DEAL = (
    'Ранее в параллельном процессе по иску Хугаевой к Хейфиц арбитражные суды трех '
    'инстанций подтвердили законность договора, по которому Хугаева еще до сделки с '
    'Николаевым, в декабре 2024 года, продала 50%-ную долю в компании Хейфиц.'
)

QUOTE_PENDING = (
    'Арбитражный суд Московской области сейчас рассматривает еще один иск Хейфиц к '
    'Хугаевой – в нем истица требует обязать ответчицу передать ей 50% в "Инфамеде".'
)

QUOTE_COMPANY_COMMENT = (
    'Представлявший интересы "Инфамеда" адвокат Рубен Маркарьян ранее, комментируя '
    'корпоративные споры, заявил РИА Новости, что компания лишь владеет '
    'регистрационными удостоверениями на лекарственные препараты, а самим выпуском '
    'не занимается, и их производству и продаже ничего не угрожает.'
)

QUOTE_EGRUL = (
    'В ЕГРЮЛ собственником 99,9% ООО "Инфамед" указан Николаев. Доля в 0,01% у '
    'Хугаевой, она же является сейчас гендиректором.'
)


def main(write):
    pending = promote.load_pending()
    existing = [c['id'] for c in pending['cards']]
    deal_id = promote.new_id(existing)
    draft = {
        'date': '2026-09-23',
        'title': 'Суд отменил продажу 99,9% «Инфамеда» (владельца «Мирамистина») и передал 50% Оксане Хейфиц',
        'ind': 'Здравоохранение',
        'type': 'M&A',
        'status': 'Закрыта',
        'src': [['ПРАЙМ', SRC_URL]],
        'buyer_name': 'Оксана Хейфиц',
        'asset': 'ООО «Инфамед»',
        'seller': 'Ирина Хугаева',
    }
    card = promote.to_card(draft, deal_id)
    card['seller_src'] = 'text'
    card['party_evidence'] = {
        'buyer': [{'value': draft['buyer_name'], 'field': 'buyer_name',
                   'method': 'human_review', 'url': SRC_URL}],
        'target': [{'value': draft['asset'], 'field': 'asset',
                    'method': 'human_review', 'url': SRC_URL}],
        'seller': [{'value': draft['seller'], 'field': 'seller',
                    'method': 'human_review', 'url': SRC_URL}],
    }
    card['events'] = [{
        'kind': 'closed',
        'date': '2026-09-23',
        'title': 'Суд передал долю Оксане Хейфиц',
        'note': QUOTE_MAIN,
        'source': ['ПРАЙМ', SRC_URL],
    }]
    card['eco']['share'] = (
        'Хугаева ещё в декабре 2024 года продала 50%-ную долю в компании Хейфиц '
        '(законность договора подтверждена судами трёх инстанций); суд вернул '
        'Хугаевой 49,9%, а 50% передал Хейфиц.'
    )
    card['eco']['context'] = QUOTE_PRIOR_DEAL + ' ' + QUOTE_PENDING
    card['eco']['rationale'] = QUOTE_COMPANY_COMMENT
    card['law']['struct'] = QUOTE_LAWSUIT
    card['extra'] = QUOTE_EGRUL
    from datetime import datetime, timezone
    card['pending_since'] = datetime.now(timezone.utc).isoformat()

    assert not any(c['id'] == deal_id for c in pending['cards'])
    pending['cards'].append(card)
    if write:
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано: карточка %s создана.' % deal_id)
    else:
        print('Сухой прогон: карточка %s была бы создана (--write, чтобы записать).' % deal_id)
    return deal_id


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    main(p.parse_args().write)
