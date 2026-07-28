# -*- coding: utf-8 -*-
"""Бэклог A18: у инвестиционного раунда не назван инвестор.

ЧТО СЛОМАНО. Владелец открыл карточку «Блоксели» и спросил, от кого компания
привлекла деньги. Инвесторы названы в заголовке — Synergy Ventures и brainbox_I,
— но в структурных полях карточки инвестора нет: плашка сторон не рисуется, а
в выжимке «Скопировать сделку текстом» покупателя нет вовсе.

ЗАМЕР (прогон 38). Карточек типа «Инвестиция» — 115, из них у **60 поле
покупателя пусто**. Прочитаны все 60: у 49 инвестор назван прямо в заголовке
или в «Дополнительной информации», у 11 — нет («имена инвесторов не
разглашаются», «привлекла 900 млн руб. финансирования», «рассматривает
привлечение стратегического инвестора»). Последние оставлены пустыми: честное
пустое состояние лучше догадки.

ПОЧЕМУ НОВОЕ ПОЛЕ, А НЕ ПРОФИЛИ. `buyer` — ссылка на профиль компании, и у
инвесторов раундов профилей почти нет: из 21 проверенного имени профиль нашёлся
у трёх. Заводить полтора десятка пустых профилей ради ссылки — плодить карточки
без содержания (в базе и так 155 профилей без единой сделки). Поэтому у
покупателя появляется текстовый вариант `buyer_name` — ровно так же, как у
продавца уже есть `seller` рядом с `seller_id`.

ГРАНИЦА. Имя инвестора обязано быть в тексте карточки. Проверка — по частям:
значение режется по запятым и «и», и КАЖДАЯ часть должна ложиться на текст
дословно или слово в слово с точностью до окончаний («от Дениса Цыпулева» ->
«Денис Цыпулев»). Так значение может собрать несколько инвесторов из разных
предложений, но не может назвать никого, кого в карточке нет.

Запуск:
    python3 pipeline/fill_round_investors.py            # сухой прогон
    python3 pipeline/fill_round_investors.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

# id сделки -> инвестор(ы), как названы в карточке
TABLE = {
 'gc5079179':'Insight Partners, Bond Capital и General Catalyst',
 'g5e187743':'Baring Vostok',
 'ga9022ee4':'Starta VC',
 'g58a1ac17':'Fort Ross Ventures и Avatar Growth Capital',
 'g7c41d78c':'TMT Investments, Insta Ventures, Wise Guys Ventures и топ-менеджеры Bolt',
 'g489cc852':'Дмитрий Зобнин',
 'g28d62a47':'Buran Venture Capital',
 'g270c77f8':'Hyundai и Kia',
 'g5900b49f':'LETA Capital и BonAngels',
 'g7261d1fc':'Force Over Mass Capital',
 'gff35947d':'«ТилТех Капитал»',
 'gbfb079af':'Елена Кулигина (банк «Бланк») и Александр Прокофьев (KudaGo)',
 'ge93aefc3':'Synergy Ventures и brainbox_I',
 'gc8157b0b':'Исаак Кваку Фокуо-мл.',
 'g8559b920':'Венчурный фонд МТС',
 'gaa8b9324':'Фёдор Ченков',
 'gf01b71ff':'Sistema VC (АФК «Система»)',
 'g4ff4b24c':'Softline Venture Partners',
 'g47844a63':'«ТилТех Капитал»',
 'g26b16b4b':'The Games Fund и Play Ventures',
 'g2be4d6a0':'ФРИИ и бизнес-ангел Денис Цыпулев',
 'g5ec182fc':'ФРИИ',
 'gd48766d5':'Runtech Ventures, Phystech Ventures',
 'g03eb22ba':'Addventure, DV Capital и LVL1',
 'g938e85ca':'TMT Investments',
 'g7623613c':'Phystech Ventures и Lever VC',
 'g8102258a':'Sistema SmartTech (венчурный фонд АФК «Система»)',
 'gc3abc691':'ВТБ Капитал',
 'geb1cfe85':'Baring Vostok',
 'g62e5dc3e':'Alphemy Capital',
 'g712a7383':'Coatue Management и Altimeter Capital',
 'g2030328e':'«Венчурный фонд Сколково — Индустриальный I» (Skolkovo Ventures)',
 'g1fa8d09e':'Андрей Черногоров и Антон Буздалин',
 'gd82d7839':'Winter Capital Partners, VNV Global и UNIQA Ventures',
 'g8aeb631a':'Дмитрий Гришин и группа бизнес-ангелов',
 'g00e9c766':'Startup Lab и Iskra Ventures',
 'ge35e2eb2':'Cats.vc и группа российских инвесторов',
 'g96e561ef':'Admitad Projects',
 'g37619a9e':'Игорь Рыбаков',
 'gf2162032':'Target Global, AddVenture и LVL1',
 'g84432523':'Acrobator VC',
 'gcab0cda4':'ФРИИ',
 'g92c6a8ce':'Максим Спиридонов',
 'ge85383b6':'«Первый Бит», АО «Здоровье» и 13 бизнес-ангелов',
 'gc09bde7e':'VNV Global, «Авенир», Марк Чанг',
 'gdb28bb81':'Fundwizer Holding AG',
 'g4882cbbe':'Atlas Ventures, ФРИИ и бизнес-ангелы',
 'g2543c41a':'VEB Ventures (венчурный фонд ВЭБ.РФ)',
 'gf0b38a39':'Xploration Capital',
}

# Прочитаны, инвестор не назван: писать нечего.
SKIP = {
    'g5b62a860': 'раунд A Bitrobotics — инвесторы не названы, доли «временно оформлены»',
    'gdd45b5d5': 'учреждение фонда «Восход», а не вложение в компанию',
    'g14356b25': 'закрытая подписка на платформе Rounds — подписчики не названы',
    'gdab53817': 'названы организатор раунда и площадка, но не инвесторы',
    'g19827333': 'запуск фонда Grishin Robotics Fund II, LP не раскрыты',
    'g0591604d': 'MBO: выкуп менеджментом, роль покупателя описана в «Структуре»',
    'gc42167a5': 'посевной раунд «Вэлби» — инвестор описан, но не назван',
    'g9d9e7ab6': 'идут переговоры, инвестор не выбран',
    'ga7298401': 'планируемое привлечение перед IPO, инвесторы не названы',
    'gcef50cb7': '«привлекла 900 млн руб. финансирования» — источник не назван',
    'g3fce1b7d': '«имена инвесторов не разглашаются» — прямо сказано в тексте',
}

WORD = re.compile(r"[\w%,.№-]+", re.U)


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def bare(w):
    return w.strip('«»"(),.;:%').lower()


def same_word(a, b):
    a, b = bare(a), bare(b)
    if not a or not b:
        return False
    if a == b:
        return True
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i >= max(3, int(0.6 * n))


def fits(result, source):
    if norm(result).lower() in norm(source).lower():
        return True
    rw, sw = WORD.findall(result), WORD.findall(source)
    return any(all(same_word(a, b) for a, b in zip(rw, sw[i:i + len(rw)]))
               for i in range(len(sw) - len(rw) + 1))


def parts(value):
    return [p.strip() for p in re.split(r',\s*|\s+и\s+', value) if p.strip()]


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    assert not (set(TABLE) & set(SKIP)), 'карточка одновременно в таблице и в отказах'

    plan, done = [], []
    for deal_id, value in TABLE.items():
        deal = by_id.get(deal_id)
        assert deal is not None, 'нет сделки %s' % deal_id
        if norm(deal.get('buyer_name')) == value:
            done.append(deal_id)
            continue
        assert not deal.get('buyer'), '%s: покупатель уже привязан к профилю' % deal_id
        assert norm(deal.get('type')) == 'Инвестиция', \
            '%s: тип не «Инвестиция», а %r' % (deal_id, norm(deal.get('type')))
        src = ' '.join([norm(deal['title']), norm(deal.get('extra'))])
        missing = [p for p in parts(value) if not fits(p, src)]
        assert not missing, '%s: в тексте карточки нет %r' % (deal_id, missing)
        plan.append((deal_id, value, deal))

    assert len(plan) + len(done) == len(TABLE), 'часть карточек изменилась вне скрипта'
    if not plan:
        print('Уже применено: инвестор записан у всех %d карточек.' % len(TABLE))
        return

    print('Карточек к заполнению: %d (прочитано и отклонено: %d)' % (len(plan), len(SKIP)))
    for deal_id, value, _ in plan:
        print('  %s  %s' % (deal_id, value[:95]))
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return
    for _, value, deal in plan:
        deal['buyer_name'] = value
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    rounds = [d for d in data['deals'] if norm(d.get('type')) == 'Инвестиция']
    known = sum(1 for d in rounds if d.get('buyer') or norm(d.get('buyer_name')))
    print('\nЗаписано. Инвестор известен у %d карточек «Инвестиция» из %d.' % (known, len(rounds)))


if __name__ == '__main__':
    main('--write' in sys.argv)
