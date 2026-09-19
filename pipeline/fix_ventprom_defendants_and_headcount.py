# -*- coding: utf-8 -*-
"""Недельная очередь дочитывания (G7, второй уровень), 19 сентября 2026:
карточка `gb98fcce5` («Акции завода «Вентпром» обращены в доход государства
по решению суда») — узкая дельта поверх полного обыска от 13 сентября.

Найдено чтением The Moscow Times (ru.themoscowtimes.com, статья от
3 сентября 2026, ранее в `src` не значилась): полный состав ответчиков по
делу — восемь человек и ДВЕ ИНОСТРАННЫЕ КОМПАНИИ (немецкая RMIS Rhein Main
Industrie Service GmbH и британская Future Invest Ltd), а сам Олег Горшков
прямо назван «бывшим председателем совета директоров «Вентпрома»» — это не
снимает уже стоящую в карточке оговорку про возможного тёзку (в неё не
вносится правка, дословных оснований снять её целиком нет), но добавляет
факт международного масштаба дела, которого раньше в карточке не было:
решение затронуло не только сам завод и его российских аффилированных лиц
(ООО «Вентпром-Инжиниринг», уже в law.struct), но и структуры за рубежом.

Отдельно, Smart-Lab (smart-lab.ru/blog/1347620.php, ранее в `src` не
значилась) называет численность штата предприятия — масштаб компании,
которого не было ни в одном уже стоявшем поле.

Обе цитаты проверены лично прямым WebFetch перед записью (themoscowtimes.com
и smart-lab.ru), дословно совпадают с добавляемым текстом.

Запуск: python3 pipeline/fix_ventprom_defendants_and_headcount.py           # проверка
        python3 pipeline/fix_ventprom_defendants_and_headcount.py --write   # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gb98fcce5'

OLD_APPR = (
    'Акции перешли в доход государства решением Ленинского районного суда '
    'Екатеринбурга от 17 августа 2026 года по делу «о запрете деятельности '
    'общественных объединений» — истцом выступал заместитель прокурора '
    'Свердловской области, иск подан в начале мая 2026 года, по делу '
    'вынесено более 20 исполнительных листов, среди ответчиков — Олег '
    'Горшков (возможно, его полный тёзка, а не тот же человек, что владел '
    'заводом в 2018 году) и другие лица. Основанием для признания '
    'владельцев экстремистским объединением стал денежный перевод '
    'гражданину Украины и то, что Горшков с 2023 года живёт за пределами '
    'России. Судья Елена Мосягина постановила, что решение подлежит '
    'немедленному исполнению, хотя оно ещё может быть обжаловано.'
)
OLD_TARGET_FIN = (
    'По РСБУ за 2025 год чистая прибыль «Вентпрома» составила 139,13 млн ₽ '
    '— в 5,7 раза больше, чем годом ранее; выручка выросла на 5,7%, до '
    '3,03 млрд ₽.'
)

QUOTE_APPR = (
    'Ответчиками по делу стали восемь человек, включая бывшего '
    'председателя совета директоров «Вентпрома» Олега Горшкова, '
    'топ-менеджера Юрия Шмакова и украинского блогера Виктора Литовченко, '
    'а также две компании — немецкая RMIS Rhein Main Industrie Service '
    'GmbH и британская Future Invest Ltd.'
)
QUOTE_FIN = 'В штате предприятия работают 527 человек.'

ADD_APPR = QUOTE_APPR
ADD_FIN = QUOTE_FIN

MOSCOW_TIMES_URL = (
    'https://ru.themoscowtimes.com/2026/09/03/odnogo-izkrupneishih-'
    'rossiiskih-proizvoditelei-promishlennogo-ventilyatsionnogo-'
    'oborudovaniya-natsionalizirovali-posle-dela-obekstremizme-a205211'
)
SMART_LAB_URL = 'https://smart-lab.ru/blog/1347620.php'


def flat(s):
    return re.sub(r'[^0-9a-zа-яё]+', '', str(s or '').lower().replace('ё', 'е'))


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в deals_promoted.json' % CARD_ID
    assert card['law'].get('appr') == OLD_APPR, (
        'law.appr уже другой: %r' % card['law'].get('appr'))
    assert card['eco'].get('target_fin') == OLD_TARGET_FIN, (
        'eco.target_fin уже другой: %r' % card['eco'].get('target_fin'))

    assert flat(ADD_APPR) in flat(QUOTE_APPR), 'ADD_APPR не лежит дословно в цитате'
    assert flat(ADD_FIN) in flat(QUOTE_FIN), 'ADD_FIN не лежит дословно в цитате'

    new_appr = OLD_APPR + ' ' + ADD_APPR
    new_target_fin = OLD_TARGET_FIN + ' ' + ADD_FIN

    print('НОВОЕ law.appr:')
    print(new_appr)
    print()
    print('НОВОЕ eco.target_fin:')
    print(new_target_fin)

    if not write:
        print()
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['law']['appr'] = new_appr
    card['eco']['target_fin'] = new_target_fin
    urls = {s[1] for s in (card.get('src') or []) if isinstance(s, list) and len(s) > 1}
    if MOSCOW_TIMES_URL not in urls:
        card.setdefault('src', []).append(['The Moscow Times', MOSCOW_TIMES_URL])
    if SMART_LAB_URL not in urls:
        card.setdefault('src', []).append(['Smart-Lab', SMART_LAB_URL])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
