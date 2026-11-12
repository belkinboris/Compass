# -*- coding: utf-8 -*-
"""Вычитка базы, партия m070 (12 ноября 2026), часть B: то, что не ложится в таблицу FIXES.

technored — по ЕГРЮЛ (история участников ООО «Технорэд», ИНН 5036173648) АО «Инвестиционная компания «Вартон»» вошло
  в участники 25 июня 2025 года с долей 49,02% через увеличение капитала (номинал доли АО «Технорэд» не изменился) —
  дата по реестру, продавца нет. Профиль «ГК «Вартон»» на сайте сопоставлен с чужим ООО ТПК «Вартон» (ИНН 7731470910,
  Фролов вышел из него в 2021 году); настоящий участник — АО «ИК «Вартон»», ИНН 7726468754 (ЕГРЮЛ на сайте и tapki.com).
  ASB Consulting Group работала со стороны продавца (обзор Ъ) — роль клиента в «Команде сделки».
ektos — разрешение Президента 8 мая 2026 года: дата по дню подписания распоряжения.
tokk-metarus — 26 марта 2026 года — день новости BIRCH, дня закрытия нет — дата годом. Инвестконсультант ТОКК —
  ink Advisory (команда управляющего партнера Руслана Измайлова; сообщения участников сделки в LinkedIn).
adv-erlan — 4 июля 2025 года — день заметки Sostav; ADPASS: «Эрлан» вошел «в июле 2025 года» — дата годом.

    python3 pipeline/archive/2026-11/reread_oneoff_m070.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m070.py --write
Повторный запуск ничего не ломает: примененное пропускается.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402

DB = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'reread m070'

# (id, поле, старое, новое, цитата, адрес) — поля-факты с цитатой для fact_edit_guard
REG_TR = ('ЕГРЮЛ, история участников ООО «Технорэд» (ИНН 5036173648): 2025-06-25 — АО «Инвестиционная компания «Вартон»» '
          '(ИНН 7726468754) вошло в участники с долей 49,02%, доля АО «Технорэд» при прежнем номинале 2 617 000 ₽ '
          'уменьшилась со 100% до 50,98%')
LI = ('Investment banking advisory for the transaction was provided by ink Advisory, with the project team led by Managing '
      'Partner Ruslan Izmaylov. Legal advisory services were delivered by BIRCH LEGAL, led by Partner Timur Akhundov.')
SETS = [
    ('technored', 'date', '2025-06-30', '2025-06-25', REG_TR, 'https://projectcompass.ru/api/companies/technored/fns'),
    ('technored', 'date_basis', None, 'registry', None, None),
    ('ektos', 'date_basis', None, 'signing', None, None),
    ('tokk-metarus', 'date', '2026-03-26', '2026',
     'Один из крупнейших в России производителей упаковки из алюминия, жести и пластика ТОКК завершил сделку по '
     'приобретению имущественного комплекса Группы Метарус', 'https://www.birchlegal.ru/news/3318/'),
    ('tokk-metarus', 'eco.finadv', 'Публично не сообщалось', 'ink Advisory (управляющий партнер Руслан Измайлов) — инвестиционный консультант ТОКК',
     LI, 'https://ru.linkedin.com/in/kirillmishaev'),
    ('adv-erlan', 'date', '2025-07-04', '2025',
     'Группа стратегических инвесторов АО «Эрлан» вошла в состав акционеров медийного контура АДВ в июле 2025 года',
     'https://adpass.ru/pochemu-sud-vernul-dmitriyu-korobkovu-doli-v-kompaniyah-adv/'),
    ('technored', 'law.adv',
     [['Сопровождение сделки', 'ASB Consulting Group', 'Структурирование, переговоры, корпоративный договор, устав и опционы (по обзору «Коммерсанта»).']],
     [['Технорэд (сторона продавца)', 'ASB Consulting Group', 'Структурирование, переговоры, корпоративный договор, устав и опционы (по обзору «Коммерсанта»).']],
     'Юридическая фирма, сопровождающая сделку: ASB Consulting Group со стороны продавца', 'https://www.kommersant.ru/doc/8077927'),
    ('tokk-metarus', 'law.adv',
     [['Покупатель — ТОКК', 'BIRCH', 'Партнер Тимур Ахундов, старший юрист Арсен Симонян, юрист Фатиме Куркчи; юридическое консультирование по сделке (по данным сайта фирмы)']],
     [['Покупатель — ТОКК', 'BIRCH', 'Партнер Тимур Ахундов, старший юрист Арсен Симонян, юрист Фатиме Куркчи; юридическое консультирование по сделке (по данным сайта фирмы)'],
      ['Покупатель — ТОКК', 'ink Advisory', 'Инвестиционный консультант; команду возглавлял управляющий партнер Руслан Измайлов (по сообщениям участников сделки)']],
     LI, 'https://ru.linkedin.com/in/kirillmishaev'),
]
SRC = [
    ('technored', ['ComNews', 'https://www.comnews.ru/content/240128/2025-07-11/2025-w28/1007/denis-frolov-astry-vlozhilsya-robototekhniku'], False),
    ('adv-erlan', ['Sostav.ru', 'https://www.sostav.ru/publication/apellyatsiya-otmenila-reshenie-o-vozvrate-adv-korobkovu-chto-reshil-sud-85296.html'], False),
]
EVENTS = []
NOTES = {
    'technored': {'no_profile': {
        'seller': 'Продавца нет: «Вартон» вошел в ООО «Технорэд» через увеличение уставного капитала — по ЕГРЮЛ 25.06.2025 '
                  'номинал доли АО «Технорэд» Артема Лукина не изменился, доля упала со 100% до 50,98%; Ъ называет '
                  'продавцом саму Technored'}},
    'tokk-metarus': {'no_profile': {
        'seller': 'Имущественный комплекс принадлежал компаниям группы «Метарус»; какие юрлица его продали, не раскрыто — '
                  'искали на сайтах BIRCH и ТОКК Металлпак, в сообщениях ink Advisory, в поиске по «Метарус Курганинск»'}},
}
PROFILES = [  # (id профиля, поле, старое, новое)
    ('varton', 'inn', None, '7726468754'),
    ('varton', 'legal_short', None, 'АО «ИК «Вартон»»'),
    ('varton', 'desc', 'Инвестиционно-промышленная группа Дениса Фролова (совладелец ГК «Астра» и «Байкал Электроникс»).',
     'Инвестиционная компания Дениса Фролова, совладельца группы «Астра».'),
    ('technored', 'inn', None, '5036173648'),
    ('technored', 'legal_short', None, 'ООО «Технорэд»'),
    ('kompsystem', 'legal_short', None, 'АО «Композит Систем»'),
]


def get(card, f):
    v = card
    for p in f.split('.'):
        v = (v or {}).get(p)
    return v


def setf(card, f, val):
    parts = f.split('.')
    for p in parts[:-1]:
        card = card.setdefault(p, {})
    card[parts[-1]] = val


def apply(data):
    cards = {c['id']: c for c in data['deals']}
    done = []
    for cid, f, old, new, quote, url in SETS:
        c = cards[cid]
        if get(c, f) == new:
            continue
        assert get(c, f) == old, (cid, f, get(c, f))
        setf(c, f, new)
        if quote:
            fact_edit_guard.log(c, f, new, quote, url, BY)
        done.append('%s %s: %r -> %r' % (cid, f, old, new))
    for cid, src, first in SRC:
        c = cards[cid]
        if any(len(s) > 1 and s[1] == src[1] for s in c.get('src') or []):
            continue
        if first:
            c.setdefault('src', []).insert(0, list(src))
        else:
            c.setdefault('src', []).append(list(src))
        done.append('%s src + %s' % (cid, src[1]))
    for cid, i, f, old, new in EVENTS:
        ev = cards[cid]['events'][i]
        if ev.get(f) == new:
            continue
        assert ev.get(f) == old, (cid, i, f, ev.get(f))
        ev[f] = new
        done.append('%s events[%d].%s' % (cid, i, f))
    for cid, notes in NOTES.items():
        an = cards[cid].setdefault('accepted_notes', {})
        for k, v in notes.items():
            for role, reason in v.items():
                if (an.get(k) or {}).get(role) != reason:
                    an.setdefault(k, {})[role] = reason
                    done.append('%s accepted_notes.%s.%s' % (cid, k, role))
    for pid, f, old, new in PROFILES:
        p = data['companies'][pid]
        if p.get(f) == new:
            continue
        if f == 'legal_short' and p.get(f):
            continue  # имя с правовой формой уже поставил party_legal_names.py
        assert p.get(f) == old, (pid, f, p.get(f))
        p[f] = new
        done.append('профиль %s %s -> %r' % (pid, f, new))
    return done


def main():
    data = json.load(open(DB, encoding='utf-8'))
    done = apply(data)
    print('\n'.join(done) or 'уже применено')
    if '--write' in sys.argv and done:
        data = json.load(open(DB, encoding='utf-8'))  # перечитать прямо перед записью
        apply(data)
        with open(DB, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('записано')


if __name__ == '__main__':
    main()
