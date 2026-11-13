# -*- coding: utf-8 -*-
"""Вычитка, марафон 12 ноября 2026, партия m226 (часть c): SEFE, «Розовая коза», Halliburton, Raisio.

Чего не умеет review.py: сумма «Не раскрыта», снятие продавца, смена типа, дата по реестру,
правка этапа events[]. Проза разделов — write_card.py (w/291_*, w/2a4_*).

g2918b022 (SEFE): «≈6 млрд €» — оценка стоимости всей компании со слов Börsen-Zeitung, а не цена
  сделки (покупателя и цены нет) — в eco.val без издания; продавец — правительство Германии
  (Федеральное сетевое агентство управляло компанией в 2022 году, владелец теперь государство);
  law.appr описывал одобрение Еврокомиссией национализации 2022 года — другой сделки, снято.
g2a4e8a51 («Розовая коза»): ООО зарегистрировано Антоном Куликовым 5 июня 2026 года (100%), 1 июля
  2026 года в него вошел Дмитрий Фомин с 30%, доля Куликова стала 70% (ЕГРЮЛ). Вход в новую
  компанию, деньги кому — не раскрыто: тип «Инвестиция», продавца нет; дата — день записи в ЕГРЮЛ.
g6797d158 (Halliburton): по ЕГРЮЛ в пересказе РБК (Сноб): с 8 сентября 2022 года 100% ООО «Апстрим
  Сервисес», которым владела нидерландская Halliburton, принадлежат ООО «БурСервис» (95% которого,
  в свою очередь, у «Апстрим Сервисес»); покупатель — общество, а не «менеджмент», люди — в прозе.
g083ec8ce (Raisio): форма доли ООО.

    python3 pipeline/archive/2026-11/reread_oneoff_m226c.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m226c', '2026-11-12'



V = 'https://www.vedomosti.ru/business/news/2026/10/02/1233912-privatizatsiyu-podrazdeleniya'
I = 'https://www.interfax.ru/business/1119994'
Q_V = ('Правительство Германии запустило процесс приватизации энергетической компании SEFE, ранее работавшей как '
       'Gazprom Germania.')
Q_I = 'По ее данным, власти дали старт процессу подачи заявок на приватизацию компании SEFE. Компания оценивается примерно в 6 млрд евро.'
VD = 'https://www.vedomosti.ru/business/articles/2026/10/01/1233258-osnovatel-kliniki-fomina'
Q_REG = ('ЕГРЮЛ, ООО «Розовая коза» (ИНН 9728174520): 2026-06-05 recorded Куликов Антон Михайлович (None → 100.0); '
         '2026-07-01 joined Фомин Дмитрий Валерьевич (None → 30.0); 2026-07-01 share_changed Куликов Антон '
         'Михайлович (100.0 → 70.0)')
Q_VD = ('Ему принадлежит 70% долей в уставном капитале зарегистрированного в июне ООО «Розовая коза», Фомину – 30%, '
        'по данным «СПАРК».')
SN = 'https://snob.ru/news/nefteservisnaya-kompaniya-halliburton-ushla-iz-rossii/'
Q_SN = ('РБК отметил , что с 8 сентября текущего года 95% ООО «БурСервис» принадлежит ООО «Апстрим Сервисес», которая с '
        'того же дня полностью находится в собственности ООО «БурСервис». Также издание пишет, что ранее 100% '
        '«Апстрим Сервисес» владела зарегистрированная в Нидерландах Halliburton.')
RI = 'https://interfax.com/newsroom/top-stories/79090/'
Q_RI = ('The change in the company\'s ownership has been recorded in the Unified State Register of Legal Entities, which '
        'showed that 100% of Raisio Nutrition is owned by Copacker Agro as of May 12.')

EDITS = [
    ('g2918b022', 'title', 'Германия начала приватизацию SEFE — бывшей «дочки» «Газпрома»',
     'Бывшая Gazprom Germania выставлена на продажу', Q_V, V),
    ('g2918b022', 'seller', 'Правительство Германии (через Федеральное сетевое агентство)', 'Правительство Германии', Q_V, V),
    ('g2918b022', 'sum', '≈6 млрд € (по оценке)', 'Не раскрыта', Q_I + ' — оценка всей компании, не цена сделки.', I),
    ('g2918b022', 'eco.sum', '≈6 млрд € (по оценке)', 'Не раскрыта', Q_I + ' — оценка всей компании, не цена сделки.', I),
    ('g2918b022', 'eco.val', '≈6 млрд € — оценка SEFE, по данным Börsen-Zeitung.',
     'По неофициальной оценке, SEFE стоит около 6 млрд €.', Q_I, I),
    ('g2918b022', 'law.appr', 'В 2022 году Еврокомиссия одобрила переход 100% SEFE под контроль немецкого государства.',
     '—', 'одобрение национализации 2022 года — другая сделка', V),
    ('g2a4e8a51', 'type', 'M&A', 'Инвестиция', Q_REG, ''),
    ('g2a4e8a51', 'title', 'Дмитрий Фомин вошел в капитал ветеринарной сети «Розовая коза» (экс-«ЗооПорт»)',
     'Дмитрий Фомин купил 30% ветеринарной сети «Розовая коза»', Q_VD, VD),
    ('g2a4e8a51', 'date', '2026-10-01', '2026-07-01', Q_REG, ''),
    ('g2a4e8a51', 'date_basis', None, 'registry', Q_REG, ''),
    ('g2a4e8a51', 'asset', '30% долей в ООО «Розовая коза» (бывший «ЗооПорт», сеть из семи ветклиник в Москве)',
     'ООО «Розовая коза»', Q_VD, VD),
    ('g2a4e8a51', 'eco.share',
     'Дмитрию Фомину принадлежит 30% долей в ООО «Розовая коза» (зарегистрировано в июне 2026 года), Антону Куликову — '
     '70%, по данным «СПАРК» и подтверждению обеих сторон.', '30% доли в ООО «Розовая коза»', Q_VD, VD),
    ('g2a4e8a51', 'law.struct',
     'Доли в ООО «Розовая коза» распределены так: Дмитрию Фомину принадлежит 30%, Антону Куликову — 70%, по данным «СПАРК».',
     'Антон Куликов зарегистрировал ООО «Розовая коза» 5 июня 2026 года; по данным ЕГРЮЛ, 1 июля Дмитрий Фомин стал '
     'участником с 30%, доля Куликова уменьшилась до 70%. Купил ли Фомин долю у партнера или внес деньги в капитал '
     'общества, стороны не сообщили.', Q_REG, ''),
    ('g6797d158', 'buyer_name', 'Бывший российский менеджмент Halliburton', 'ООО «БурСервис»', Q_SN, SN),
    ('g6797d158', 'title', 'Бывшие российские менеджеры Halliburton купили ее бизнес в России',
     '«БурСервис» купил российский бизнес Halliburton', Q_SN, SN),
    ('g6797d158', 'asset', 'Российский нефтесервисный бизнес американской группы (теперь ООО «Бурсервис»)',
     'ООО «Апстрим Сервисес» (российский нефтесервисный бизнес Halliburton)', Q_SN, SN),
    ('g6797d158', 'eco.share', 'Весь российский бизнес Halliburton', '100% доли в ООО «Апстрим Сервисес»', Q_SN, SN),
    ('g6797d158', 'date', '2022-09-09', '2022-09-08', Q_SN, SN),
    ('g6797d158', 'date_basis', 'closing', 'registry', Q_SN, SN),
    ('g6797d158', 'law.struct',
     'Покупатель — бывший российский менеджмент Halliburton; бизнес работает под названием ООО «Бурсервис». С 8 сентября '
     '2022 года сменился владелец ООО «Апстрим Сервисес», которым раньше полностью владела нидерландская структура '
     'Halliburton.',
     'По данным ЕГРЮЛ, с 8 сентября 2022 года ООО «Апстрим Сервисес», которым раньше полностью владела нидерландская '
     'структура Halliburton, принадлежит ООО «БурСервис», а 95% «БурСервиса» — самому «Апстрим Сервисес». За этой '
     'конструкцией, по словам Halliburton, стоят ее бывшие российские управленцы.', Q_SN, SN),
    ('g083ec8ce', 'eco.share', '100% ООО «Раисио Нутришн»', '100% доли в ООО «Раисио Нутришн»', Q_RI, RI),
]
RETRACT = {('g2918b022', 'sum'): '≈6 млрд € (по оценке)', ('g6797d158', 'buyer_name'): 'Бывший российский менеджмент Halliburton'}
DROP_SELLER = {
    'g2a4e8a51': ('Антон Куликов',
                  'Продавца нет: Дмитрий Фомин вошел в новое ООО «Розовая коза», которое Антон Куликов зарегистрировал 5 '
                  'июня 2026 года; по ЕГРЮЛ 1 июля 2026 года доля Куликова стала 70%, Фомин получил 30%. Платил ли Фомин '
                  'Куликову или вносил деньги в капитал, в «Ведомостях», Vademecum и «Зооинформе» не сказано.'),
}
NOTES = {
    ('g6797d158', 'buyer'): 'ООО «БурСервис» (бывшая российская дочка Halliburton под управлением ее бывших менеджеров): '
                            'ИНН не найден — egrul.nalog.ru сбрасывает соединение, datanewton закрыт проверкой браузера, '
                            'в статьях Интерфакса и Сноба ИНН и ОГРН нет. Профиль АО «Бурсервис» (g69e44ed5) — другое юрлицо.',
}
EVENTS = {
    'g2918b022': ('2026-10-02', '2026-10-02', 'Приватизация начата',
                  'Правительство Германии дало старт приватизации SEFE: министерство экономики выбирает юристов для '
                  'сделки, свои заявки подают инвестиционные банки.', ['Ведомости', V]),
    'g2a4e8a51': ('2026-10-01', '2026-07-01', 'Доля перешла',
                  'Дмитрий Фомин стал участником ООО «Розовая коза» с долей 30%; о партнерстве совладельцы рассказали 1 '
                  'октября 2026 года, ребрендинг клиник «ЗооПорт» намечен на срок до марта 2027 года.', ['Ведомости', VD]),
}

def get(c, f):
    if '.' in f:
        a, b = f.split('.')
        return (c.get(a) or {}).get(b)
    return c.get(f)


def put(c, f, v):
    if '.' in f:
        a, b = f.split('.')
        c.setdefault(a, {})[b] = v
    else:
        c[f] = v


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, f, old, new, quote, url in EDITS:
        c = by[cid]
        if get(c, f) == new:
            continue
        assert get(c, f) == old, (cid, f, get(c, f))
        put(c, f, new)
        fact_edit_guard.log(c, f, new, quote, url, BY, DAY)
        n += 1
    for (cid, f), old in RETRACT.items():
        r = by[cid].setdefault('retracted', {}).setdefault(f, [])
        if old not in r:
            r.append(old)
    for cid, (old, why) in DROP_SELLER.items():
        c = by[cid]
        if 'seller' not in c:
            continue
        assert c['seller'] == old and not c.get('seller_id'), (cid, c.get('seller'))
        del c['seller']
        c.pop('seller_src', None)
        c.setdefault('retracted', {}).setdefault('seller', []).append(old)
        c.setdefault('accepted_notes', {}).setdefault('no_profile', {})['seller'] = why
        fact_edit_guard.log(c, 'seller', None, why, VD, BY, DAY)
        n += 1
    for (cid, role), text in NOTES.items():
        c = by[cid]
        np_ = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
        if np_.get(role) != text:
            np_[role] = text
            n += 1
    for cid, (old, new, title, note, src) in EVENTS.items():
        c = by[cid]
        e = c['events'][0]
        if e['date'] == new and e['note'] == note:
            continue
        assert e['date'] == old, (cid, e)
        e.update({'date': new, 'title': title, 'note': note, 'source': src})
        n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
