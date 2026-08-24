# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g506ea8c4 (покупка контрольного пакета
«Русского лосося»): дельта-поиск нашёл, что фамилия покупателя записана
неверно — «Кудрявый» вместо «Курявый». Ошибка не во ВНЕШНЕМ источнике:
уже процитированный в карточке Коммерсантъ (doc/7808131) сам пишет
«Антон Курявый» дважды («Владельцем компании «Русский лосось» стал
Антон Курявый», «господа Курявый и Казьмин ранее руководили
структурами») — искажение произошло при разборе притока, а не в
источнике. Ещё четыре независимых издания (dp.ru, mergers.ru,
shoppers.media, tadviser.ru) подтверждают «Курявый». Правится в
заголовке, `extra`, `law.terms` и в самом профиле покупателя — везде,
где стоит неверное написание.

Не через `review.py`: смена фамилии в четырёх местах плюс новый факт из
ДРУГОГО источника (dp.ru, майская перепродажа 2026 года) — не
проходит дословную проверку одним источником.

Второй, самостоятельный факт: 16 мая 2026 года «Русский лосось» снова
сменил владельца — 51% в «Биоресурсе» перешли от Курявого к АО
«Эльбрус партнерс» (тому же обществу принадлежат «РРПК» и «Беринг
краб»). Статус и стороны ЭТОЙ карточки не меняются (сделка card описывает
Бобров -> Курявый, июнь 2025, и она реально произошла и закрылась) —
перепродажа добавлена как история в `eco.context`, отдельной карточки
для неё в базе пока нет и заводить её не наша задача.

Источники — читал напрямую (fetch_article_texts.py, закэшированы):
https://www.kommersant.ru/doc/7808131 (уже в src, подтверждает «Курявый»)
https://www.dp.ru/a/2026/05/25/russkij-losos-smenil-osnovnih

Запуск: python3 pipeline/fix_russkiy_losos_kuryavy_name_and_resale.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g506ea8c4'
COMPANY_ID = 'g2d2afb21'

OLD_TITLE = 'Антон Кудрявый приобрел контрольный пакет ООО «Биоресурс» (51% доля), владеющего 100% ООО «Русский лосось»'
NEW_TITLE = 'Антон Курявый приобрел контрольный пакет ООО «Биоресурс» (51% доля), владеющего 100% ООО «Русский лосось»'

OLD_EXTRA = (
    'Сделка закрыта 17 июня 2025 г. Покупатель — Антон Кудрявый (ранее '
    'руководил структурами Глеба Франка). Продавец — Михаил Бобров, '
    'основатель ГК «Русский лосось». Сумма официально не раскрыта; '
    'эксперты (BGP Capital и инвестбанкир Илья Шумов) оценивают EV в '
    '10–12 млрд руб.'
)
NEW_EXTRA = OLD_EXTRA.replace('Антон Кудрявый', 'Антон Курявый')

OLD_TERMS = (
    '4% — сохранил Илья Горбатский, однако эта доля находится в залоге '
    'у нового владельца 51% Антона Кудрявого.'
)
NEW_TERMS = OLD_TERMS.replace('Антона Кудрявого', 'Антона Курявого')

OLD_CONTEXT = 'До середины июня ее основным собственником был совладелец ТД «Балтийский берег» Михаил Бобров.'
NEW_CONTEXT = OLD_CONTEXT + (
    ' 16 мая 2026 года, согласно ЕГРЮЛ, владельцем 51%-ной доли в ООО '
    '«Русский лосось» через ООО «Биоресурс» стало АО «Эльбрус '
    'партнерс» — тому же обществу принадлежат ООО «РРПК» (Русская '
    'рыбопромышленная компания) и АО «Беринг краб»; отдельной карточки '
    'у этой сделки в базе пока нет.'
)

OLD_COMPANY_NAME = 'Антон Кудрявый'
NEW_COMPANY_NAME = 'Антон Курявый'
OLD_COMPANY_DESC = (
    'Ранее руководил структурами Глеба Франка; в 2025 году купил у '
    'Михаила Боброва контрольный пакет (51%) «Биоресурса», владеющего '
    '100% «Русского лосося», по оценке EV в 10–12 млрд ₽.'
)
NEW_COMPANY_DESC = OLD_COMPANY_DESC.replace('Кудрявый', 'Курявый') + (
    ' В мае 2026 года пакет перешёл дальше — к АО «Эльбрус партнерс».'
)

TARGET_ID = 'gae808cc0'
OLD_TARGET_DESC = (
    'Холдинг, владеющий 100% ГК «Русский лосось»; в 2025 году '
    'контрольный пакет (51%) купил Антон Кудрявый у основателя Михаила '
    'Боброва за 10–12 млрд ₽ (по оценке).'
)
NEW_TARGET_DESC = OLD_TARGET_DESC.replace('Кудрявый', 'Курявый')


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)
    company = data['companies'][COMPANY_ID]
    target = data['companies'][TARGET_ID]

    assert deal['title'] == OLD_TITLE, f"title: {deal['title']!r}"
    assert deal['extra'] == OLD_EXTRA, f"extra: {deal['extra']!r}"
    assert deal['law']['terms'] == OLD_TERMS, f"law.terms: {deal['law']['terms']!r}"
    assert deal['eco']['context'] == OLD_CONTEXT, f"eco.context: {deal['eco']['context']!r}"
    assert company['name'] == OLD_COMPANY_NAME, f"company.name: {company['name']!r}"
    assert company['desc'] == OLD_COMPANY_DESC, f"company.desc: {company['desc']!r}"
    assert target['desc'] == OLD_TARGET_DESC, f"target.desc: {target['desc']!r}"

    print(f'{CARD_ID} title: «Кудрявый» -> «Курявый»')
    print(f'{CARD_ID} extra: «Кудрявый» -> «Курявый»')
    print(f'{CARD_ID} law.terms: «Кудрявого» -> «Курявого»')
    print(f'{CARD_ID} eco.context: += перепродажа «Эльбрус партнерс», май 2026')
    print(f'{COMPANY_ID} name: «Кудрявый» -> «Курявый»')
    print(f'{COMPANY_ID} desc: «Кудрявый» -> «Курявый» + перепродажа')
    print(f'{TARGET_ID} desc: «Кудрявый» -> «Курявый»')

    if write:
        deal['title'] = NEW_TITLE
        deal['extra'] = NEW_EXTRA
        deal['law']['terms'] = NEW_TERMS
        deal['eco']['context'] = NEW_CONTEXT
        company['name'] = NEW_COMPANY_NAME
        company['desc'] = NEW_COMPANY_DESC
        target['desc'] = NEW_TARGET_DESC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
