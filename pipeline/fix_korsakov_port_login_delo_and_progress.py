# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g941f2b2b
(«Группа компаний «Дело» приобрела контроль в Корсаковском морском торговом
порту»). Проверено лично прямым WebFetch/WebSearch.

1) `buyer` — прямым юридическим покупателем выступила не группа «Дело» как
таковая, а отдельная компания ООО «Логин Дело», учреждённая Шишкаревым.
Interfax, дословно: «ООО «Логин Дело» закрыло сделку по приобретению 64,26%
акций АО «Корсаковский морской торговый порт»»; «Совладелец группы компаний
«Дело» Сергей Шишкарев в декабре 2023 года учредил ООО «Логин Дело» с
уставным капиталом 200 млн рублей». Это тот же принцип, что уже применён к
УГМК-Инвест/УГМК и Экспанте/Ультиматек (см. CLAUDE.md): прямой покупатель —
конкретное юрлицо, а бренд («Дело») — в заголовке и через `holding`. Заведён
новый профиль «ООО «Логин Дело»» с `holding.id` на уже существующий профиль
«Дело» (`delo`).
Источник: https://www.interfax.ru/business/971076

2) `eco.share` — точная доля дополняет уже стоявшее техническое описание
порта: «64,26% акций» (тот же источник).

3) `law.appr` — заменена прозаическая формулировка (пересказ губернатора)
на дословную цитату первоисточника: shishkarev.ru, дословно: «The
transaction had previously received all necessary regulatory approvals,
including clearance from the Federal Antimonopoly Service.»
Источник: https://www.shishkarev.ru/en/news/login-delo-zakrylo-sdelku-po-pokupke-aktsiy-ao-korsakovskiy-morskoy-torgovyy-port/

4) `eco.context` (новое поле) — прогресс реконструкции в 2025-2026:
- korabel.ru, дословно: «Проектно-сметная документация первой очереди
  реконструкции объектов портовой инфраструктуры в морском порту Корсаков
  получила положительное заключение Главгосэкспертизы России.»
- news.ati.su (интервью полпреда Юрия Трутнева, 31.01.2026), дословно:
  «Сейчас в Рыбном порту идет реконструкция причалов, которые находятся в
  ведении ФГУП «Нацрыбресурс».» «Этот этап планируют завершить к концу 2026
  года.» «В 2025 году стартуют работы на объектах ФГУП «Росморпорт» и
  дноуглубление акватории.» «Это позволит увеличить годовой грузооборот до
  4,4 млн тонн» — новая, более точная цифра целевого грузооборота (в
  карточке стояло округлённое «4 млн тонн» из плана 2024 года).
- portnews.ru, дословно: «Первый этап реконструкции порта Корсаков
  планируется завершить в первой половине 2026 года.» «На эти цели из
  федерального бюджета привлечено 6,8 млрд рублей.»

НЕ включены: продавец (прежний владелец АО «КМТП») — не назван ни в одном
из 9 проверенных источников (ЕГРЮЛ/e-disclosure недоступны), честная
пустота; консультанты сделки и независимая оценка суммы — не найдены;
упомянутая роль «Росатома» («мы договорились с Росатомом, что приводим его
в порядок») — источник не называет Росатом ни акционером, ни продавцом,
роль неясна, включать её значило бы гадать; связь Корсакова с другими
дальневосточными активами группы «Дело» — не найдена ни одним источником.

Запуск: python3 pipeline/fix_korsakov_port_login_delo_and_progress.py
        python3 pipeline/fix_korsakov_port_login_delo_and_progress.py --write
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g941f2b2b'

NEW_COMPANY_NAME = 'ООО «Логин Дело»'
NEW_COMPANY_SEED = 'login-delo-2023-korsakov'
NEW_COMPANY = {
    'name': NEW_COMPANY_NAME,
    'ind': 'Порты и инфраструктура',
    'desc': (
        'Инвестиционная компания, учреждённая Сергеем Шишкаревым в декабре '
        '2023 года для покупки и развития портовых активов на Дальнем '
        'Востоке.'
    ),
    'holding': {
        'id': 'delo',
        'confidence': 'disclosed',
        'source': ['Interfax', 'https://www.interfax.ru/business/971076'],
    },
}

OLD_SHARE = (
    'Морской порт Корсаков расположен на южном побережье острова Сахалин в '
    'заливе Анива, является одним из ключевых портов дальневосточного '
    'бассейна. Площадь акватории морского порта составляет 113,26 кв. км. '
    'Количество причалов — 30, длина причального фронта — 3,4 тыс. '
    'погонных метров. Пропускная способность грузовых терминалов — более 4 '
    'млн тонн в год, пассажирских — 31,5 тыс. человек в год.'
)
NEW_SHARE = OLD_SHARE + ' ООО «Логин Дело» приобрело 64,26% акций АО «КМТП».'

OLD_APPR = (
    'Летом губернатор Сахалинской области Валерий Лимаренко заявил, что '
    'ФАС России согласовала сделку.'
)
NEW_APPR = (
    '«The transaction had previously received all necessary regulatory '
    'approvals, including clearance from the Federal Antimonopoly '
    'Service» (пресс-релиз shishkarev.ru).'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    'Проектно-сметная документация первой очереди реконструкции «получила '
    'положительное заключение Главгосэкспертизы России» (korabel.ru). По '
    'словам полпреда Юрия Трутнева (31.01.2026): «Сейчас в Рыбном порту '
    'идет реконструкция причалов, которые находятся в ведении ФГУП '
    '«Нацрыбресурс»»; «Этот этап планируют завершить к концу 2026 года»; '
    '«В 2025 году стартуют работы на объектах ФГУП «Росморпорт» и '
    'дноуглубление акватории» — «Это позволит увеличить годовой '
    'грузооборот до 4,4 млн тонн». PortNews (позже): «Первый этап '
    'реконструкции порта Корсаков планируется завершить в первой половине '
    '2026 года», «На эти цели из федерального бюджета привлечено 6,8 млрд '
    'рублей».'
)

NEW_SRC = [
    ['Interfax', 'https://www.interfax.ru/business/971076'],
    ['shishkarev.ru', 'https://www.shishkarev.ru/en/news/login-delo-zakrylo-sdelku-po-pokupke-aktsiy-ao-korsakovskiy-morskoy-torgovyy-port/'],
    ['korabel.ru', 'https://www.korabel.ru/news/comments/glavgosekspertiza_odobrila_proekt_rekonstrukcii_porta_korsakov.html'],
    ['news.ati.su', 'https://news.ati.su/news/2026/01/31/polpred-trutnev-otsenil-hod-modernizatsii-korsakovskogo-morskogo-porta-705673/'],
    ['PortNews', 'https://portnews.ru/news/373048/'],
]


def new_id(seed, existing):
    cid = 'g' + hashlib.sha1(seed.encode('utf-8')).hexdigest()[:8]
    assert cid not in existing, 'коллизия id: %s' % cid
    return cid


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)
    comps = data['companies']

    assert deal['buyer'] == 'delo'
    assert deal['eco']['share'] == OLD_SHARE
    assert deal['law']['appr'] == OLD_APPR
    assert deal['eco']['context'] == OLD_CONTEXT
    existing_names = {c.get('name') for c in comps.values()}
    assert NEW_COMPANY_NAME not in existing_names, 'имя нового профиля уже занято'
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    cid = new_id(NEW_COMPANY_SEED, set(comps.keys()))
    print(f'=== новый профиль {cid}: {NEW_COMPANY_NAME!r} ===')
    print(f'=== buyer: {"delo"!r} -> {cid!r} ===')
    print('=== eco.share: станет ===')
    print(NEW_SHARE)
    print('=== law.appr: было ===')
    print(OLD_APPR)
    print('=== law.appr: станет ===')
    print(NEW_APPR)
    print('=== eco.context (новое поле): станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        comps[cid] = NEW_COMPANY
        deal['buyer'] = cid
        deal['eco']['share'] = NEW_SHARE
        deal['law']['appr'] = NEW_APPR
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
