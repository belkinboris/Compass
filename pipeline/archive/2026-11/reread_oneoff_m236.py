# -*- coding: utf-8 -*-
"""Вычитка-марафон 13 ноября 2026, партия m236 (часть 1): правки, которые review.py не принимает.

Статьи открыты заново (curl) и сохранены save_source.py (day 2026-11-12_m236).

g20d4cc38 (Carlyle / LUKOIL International): заголовок по стандарту «X собирается купить Y» (о сделке
  объявил ЛУКОЙЛ); eco.val — «Сама сделка» разговорно, у Шапошникова не было имени и должности
  (Ведомости, 29.01.2026: «советник управляющего фонда «Индустриальный код» Максим Шапошников»),
  оценка в $20 млрд в Право.ru дана без автора.
selectel-itmo (СП Selectel и ИТМО): «более 1 млрд ₽» — сколько Selectel вложит в СП (CNews,
  06.07.2026), то есть инвестиции в проект, а не цена: sum и eco.sum — «Не раскрыта», цифра
  остается в eco.val.
gmru-arnest-reckitt: сделка закрыта 12 ноября 2026 (ТАСС: «Группа "Арнест" купила российский
  бизнес Reckitt», этап closed-2026-11-12 в карточке), дата стояла днем переговоров; заголовок —
  прошедшим временем; law.appr и eco.target_fin — снимок середины сделки («ждут решения британских
  регуляторов», «собирается купить»).
mid-ilyinskaya: заголовок без бенефициара «у Тимура Кулибаева» (продавцы — ТОО «Emdeu Medline» и
  ООО «Раф-Мед»); дня 23 июня нет ни в одном источнике (сообщение компании 24 июня: сделка «уже
  одобрена ФАС России и находится на регистрации», день закрытия не назван) — дата годом.
c1d2ba2c0 (ЧЭМК): обсуждалась передача 25% акций «Ростеху» после изъятия (РБК через www1.ru,
  04.03.2024), а в buyer стояло Росимущество, продавцом — Юрий Антипов, у которого акции изъял суд.
  Покупатель — «Ростех», передает государство (Росимущество, акционер ЧЭМК по ЕГРЮЛ с 13.03.2024);
  «1 марта» в источниках нет — дата годом.

    python3 pipeline/archive/2026-11/reread_oneoff_m236.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m236', '2026-11-13'
VED = 'https://www.vedomosti.ru/business/articles/2026/01/29/1172691-skolko-carlyle-zaplatit'
CNEWS = 'https://www.cnews.ru/news/line/2026-07-06_selectel_investiruet_bolee_1'
TASS = 'https://tass.ru/ekonomika/28311225'
VADEM = 'https://www.vademec.ru/news/2026/06/24/gk-mat-i-ditya-za-8-5-mlrd-rubley-pokupaet-ilinskuyu-bolnitsu/'
WWW1 = ('https://www1.ru/news/2024/03/04/vernut-to-cto-prinadlezit-gosudarstvu-rostexu-mogut-peredat-'
        'cast-akcii-celiabinskogo-kombinata.html')

# (id, путь, старое, новое, цитата, адрес, снять_в_retracted)
EDITS = [
    ('g20d4cc38', 'title', 'ЛУКОЙЛ продает зарубежные активы (LUKOIL International GmbH) компании Carlyle',
     'Carlyle собирается купить LUKOIL International GmbH',
     'ПАО ЛУКОЙЛ договорилось с американской инвестиционной компанией Carlyle о продаже LUKOIL International GmbH',
     VED, None),
    ('g20d4cc38', 'eco.val',
     'По оценке Шапошникова, эти активы стоят около $10 млрд, но Carlyle заплатит за них $3–4 млрд. '
     'Сама сделка оценивается в $20 млрд.',
     'По оценке Максима Шапошникова, советника управляющего фонда «Индустриальный код», эти активы стоят '
     'около $10 млрд, а Carlyle заплатит за них $3–4 млрд. Всю сделку оценивают в $20 млрд, автор этой '
     'оценки не назван.',
     'советник управляющего фонда «Индустриальный код» Максим Шапошников. По оценке Шапошникова, стоимость '
     'указанных активов составляет около $10 млрд. При этом Carlyle заплатит за них $3–4 млрд, полагает эксперт.',
     VED, None),
    ('selectel-itmo', 'sum', '1+ млрд ₽', 'Не раскрыта',
     'Selectel инвестирует более 1 млрд руб. в совместное предприятие с ИТМО — это вложения в проект, а не цена сделки',
     CNEWS, 'sum'),
    ('selectel-itmo', 'eco.sum', 'Более 1 млрд ₽', 'Не раскрыта',
     'Selectel инвестирует более 1 млрд руб. в совместное предприятие с ИТМО — это вложения в проект, а не цена сделки',
     CNEWS, None),
    ('gmru-arnest-reckitt', 'title', '«Арнест» выкупает часть российского бизнеса Reckitt Benckiser',
     '«Арнест» купил у Reckitt завод бытовой химии в Клину',
     'Группа "Арнест" купила российский бизнес Reckitt в сегменте бытовой химии. В периметр сделки вошло '
     'предприятие в Клину в Московской области', TASS, None),
    ('gmru-arnest-reckitt', 'date', '2026-07-27', '2026-11-12',
     'Группа "Арнест" купила российский бизнес Reckitt в сегменте бытовой химии (ТАСС, 12 ноября 2026)',
     TASS, None),
    ('gmru-arnest-reckitt', 'law.appr',
     'Российская правительственная комиссия, как утверждает «Арнест», уже дала согласие. Ждут решения '
     'британских регуляторов — они рассматривают сделку сейчас, а закрытие возможно к концу 2026 года.',
     'Правительственная комиссия по иностранным инвестициям, по словам «Арнеста», дала согласие на сделку; '
     'Reckitt ставила закрытие в зависимость и от одобрения британских регуляторов.',
     'Российская правительственная комиссия, как утверждает «Арнест», уже дала согласие', 
     'https://www.kommersant.ru/doc/8844212', None),
    ('gmru-arnest-reckitt', 'eco.target_fin',
     'Выручка ООО «Рекитт Бенкизер», которое собирается купить «Арнест», в 2023 году снизилась на 18,8%, '
     'до 12,3 млрд ₽; чистая прибыль упала на 42%, до 2,6 млрд ₽. Это последние доступные данные.',
     'Выручка ООО «Рекитт Бенкизер», которое купил «Арнест», в 2023 году снизилась на 18,8%, '
     'до 12,3 млрд ₽; чистая прибыль упала на 42%, до 2,6 млрд ₽. Это последние доступные данные.',
     'Группа "Арнест" купила российский бизнес Reckitt в сегменте бытовой химии', TASS, None),
    ('mid-ilyinskaya', 'title', '«Мать и дитя» приобрела Ильинскую больницу у Тимура Кулибаева',
     '«Мать и дитя» купила Ильинскую больницу',
     'Группа компаний «Мать и дитя» сообщила о приобретении многопрофильного амбулаторно-госпитального центра '
     '«Ильинская больница» в Московской области', VADEM, None),
    ('mid-ilyinskaya', 'date', '2026-06-23', '2026',
     'Сделка стоимостью 8,5 млрд рублей, включая 1,1 млрд рублей долга на балансе актива, уже одобрена ФАС '
     'России и находится на регистрации (24 июня 2026; день закрытия в источниках не назван)', VADEM, None),
    ('c1d2ba2c0', 'buyer', 'g9fd82fee', 'g7802e51e',
     'После национализации 25% ЧЭМК могут отдать «Ростеху», а остальные 75% — продать частному инвестору.',
     WWW1, None),
    ('c1d2ba2c0', 'seller', 'Юрий Антипов', 'Росимущество',
     'ЕГРЮЛ, АО «ЧЭМК» (ИНН 7447010227): 2024-03-13 joined Росимущество, left АО «Компания Эталон» и АО «УСМК»; '
     'передавать «Ростеху» акции будет государство, а не Юрий Антипов, у которого их изъял суд',
     WWW1, 'seller'),
    ('c1d2ba2c0', 'seller_id', None, 'g9fd82fee',
     'ЕГРЮЛ, АО «ЧЭМК» (ИНН 7447010227): 2024-03-13 joined Росимущество', WWW1, None),
    ('c1d2ba2c0', 'date', '2024-03-01', '2024',
     'Ростеху могут передать часть акций Челябинского комбината (04.03.2024, со ссылкой на РБК; дня события нет)',
     WWW1, None),
]
DATE_BASIS = {'gmru-arnest-reckitt': 'closing'}


def get(c, path):
    cur = c
    for k in path.split('.'):
        cur = (cur or {}).get(k)
    return cur


def put(c, path, val):
    ks = path.split('.')
    cur = c
    for k in ks[:-1]:
        cur = cur.setdefault(k, {})
    cur[ks[-1]] = val


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, path, old, new, quote, url, retract in EDITS:
        c = by[cid]
        if get(c, path) == new:
            continue
        assert get(c, path) == old, (cid, path, get(c, path))
        put(c, path, new)
        if retract:
            lst = c.setdefault('retracted', {}).setdefault(retract, [])
            if old not in lst:
                lst.append(old)
        fact_edit_guard.log(c, path, new, quote, url, BY, DAY)
        n += 1
    for cid, basis in DATE_BASIS.items():
        if by[cid].get('date_basis') != basis:
            by[cid]['date_basis'] = basis
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
    sys.exit(main('--write' in sys.argv))
