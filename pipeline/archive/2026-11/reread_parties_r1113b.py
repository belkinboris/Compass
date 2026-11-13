# -*- coding: utf-8 -*-
"""Вычитка 13 ноября 2026, партия r1113b: находки party_registry_audit.py (сторона схемы против
истории участников ЕГРЮЛ, docs/card_parties.md, «Покупатель и продавец в схеме — те, кто в реестре»).

g576de71f («Моторика»): находка ложная и уже разобрана при вычитке 13 ноября (accepted_notes.checked):
  в ЕГРЮЛ МК ООО «Хомо Ауктус» 27.12.2024 вошло ООО «Орбита» (ИНН 7727391751, совладелец — Газпромбанк),
  и прежний читатель решил оставить в схеме группу Газпромбанка, которой «Орбита» принадлежит, — не трогаем.
g5880d206 («Фольксваген банк Рус»): ЕГРЮЛ ООО «Пихта банк» 25.02.2025 — вошли ООО «Экспомобилити» (55%) и
  Игорь Ким (45%), вышли Volkswagen Financial Services Overseas AG (99%) и Volkswagen Bank GmbH (1%) —
  AK&M 26.02.2025. «Структуры Игоря Кима» и группа VW FS в схеме заменены сторонами из реестра.
g703c4f62 («Россиум»): 93,14% ООО «Концерн «Россиум»» перешли в ЕГРЮЛ 01.10.2025 к АО «Инвестиционная
  компания «Регион»» (ИНН 7730095858, ОГРН 1027739041153; AK&M 02.10.2025); покупатель в схеме — она
  (профиль «Структуры Сергея Сударикова» был только у этой сделки — переименован). Продавец Роман Авдеев
  остается: его доля была косвенной (через владельцев ООО «ХК «Доминанта»» — ДоминантаФинанс,
  ПрестиссимоФинанс, Гравеинвест, Итатрейд, ЗПИФ «М-Капитал»), реестр Авдеева не показывает.
g37f106cd («Балтийский берег»): ЕГРЮЛ ООО «СБК КЗМ Плюс» (ОГРН 1167746523526) — 04.04.2023 участник
  Михаил Бобров, 100%: покупатель в схеме верен; дата — по реестру; предмет — доля в «СБК КЗМ Плюс»;
  2–3 млрд ₽ — оценка Дмитрия Маркова (ПТЦ), не цена: сумма «Не раскрыта», оценка уже в eco.val.

    python3 pipeline/archive/2026-11/reread_parties_r1113b.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_parties_r1113b', '2026-11-13'

DN = 'https://datanewton.ru/api/v2/history?ogrn=%s&startDate=2000-01-01&attributes=OWNERS'
KS = 'https://www.kommersant.ru/amp/5941195'
AKM_VW = 'https://www.akm.ru/news/folksvagen_bank_rus_smenil_vladeltsa/'
AKM_RS = ('https://www.akm.ru/news/kontsern_rossium_i_kholdingovaya_kompaniya_dominanta_pereshli_pod_kontrol_'
          'ik_region_i_ego_benefitsia/')
GPB = 'https://www.gazprombank.ru/press/7764021/'

Q_SBK = ('ЕГРЮЛ, ООО «СБК КЗМ Плюс» (ОГРН 1167746523526), участники, запись 2023-04-04: «БОБРОВ МИХАИЛ НИКОЛАЕВИЧ '
         '(ИНН: 780508196120) 100.0%» || Михаил Бобров приобрел компанию «СБК КЗМ Плюс», которой принадлежит ООО «ТД '
         '"Балтийский берег"» и ООО «Экопромэкс».')
Q_MARKOV = ('Сумма сделки могла составить 2–3 млрд рублей, оценивает начальник отдела торговых операций компании ПТЦ '
            'Дмитрий Марков. — оценка аналитика, стороны цену не называли.')
Q_VW = ('Игорь Ким с 25 февраля 2025 года владеет 45% ООО «Фольксваген Банк РУС», ООО «Экспомобилити» — 55% '
        '(принадлежит новосибирскому АО «ЦК»). Ранее Фольксваген Банк Гмбх владел 1%, Фольксваген Файненшл Сервисез '
        'Оверсиз Акциенгезелльшафт — 99%.')
Q_RS = ('ООО «Холдинговая компания „Доминанта“» передало принадлежавшие ей 93.14% в ООО «Концерн „Россиум“» новому '
        'собственнику. Им стало АО «Инвестиционная компания „Регион“». Такие изменения произошли в ЕГРЮЛ')

# (id, путь, старое, новое, цитата, адрес); путь с «@» — замена части текста
SETS = [
    ('g37f106cd', 'eco.share', 'ООО «СБК КЗМ Плюс» — владелец ООО «ТД «Балтийский берег»» и ООО «Экопромэкс»',
     '100% доли в ООО «СБК КЗМ Плюс»', Q_SBK, DN % '1167746523526'),
    ('g37f106cd', 'sum', '2–3 млрд ₽ (по оценке)', 'Не раскрыта', Q_MARKOV, KS),
    ('g37f106cd', 'eco.sum', '2–3 млрд ₽ (по оценке)', 'Не раскрыта', Q_MARKOV, KS),
    ('g37f106cd', 'date', '2023', '2023-04-04', Q_SBK + ' || Сделка состоялась в начале апреля, следует из данных '
     'ЕГРЮЛ.', DN % '1167746523526'),
    ('g37f106cd', 'date_basis', None, 'registry', Q_SBK, DN % '1167746523526'),
    ('g5880d206', 'buyer', 'ge370cfae', None, Q_VW, AKM_VW),
    ('g5880d206', 'buyer_name', None, 'ООО «Экспомобилити» и Игорь Ким', Q_VW, AKM_VW),
    ('g5880d206', 'seller', 'Volkswagen Financial Services',
     'Volkswagen Financial Services Overseas AG и Volkswagen Bank GmbH', Q_VW, AKM_VW),
    ('g5880d206', 'seller_id', 'g6617345f', None, Q_VW, AKM_VW),
    ('g703c4f62', 'title', 'Структуры Сергея Сударикова купили долю в «Россиуме» у Романа Авдеева',
     'ИК «Регион» купила долю в «Россиуме» у Романа Авдеева', Q_RS, AKM_RS),
    ('g703c4f62', 'law.struct@', 'Доля Авдеева, по данным Forbes, составляла 62%.',
     'Доля Авдеева, по неофициальным данным, составляла 62%.',
     'По информации Forbes, доля господина Авдеева в «Россиуме» составляла 62%.',
     'https://www.kommersant.ru/doc/7267872'),
]
RETRACT = {('g37f106cd', 'sum'), ('g5880d206', 'seller')}

# профиль стоял только у этой сделки: имя стороны из реестра. Ключ match_keys (псевдоним для
# поиска компании в заголовках) тоже меняется — иначе он остается куском старого заголовка.
PROFILES = {
    'g470a51f2': ('Структуры Сергея Сударикова', {
        'name': 'ИК «Регион»', 'legal_short': 'АО «ИК «Регион»»', 'inn': '7730095858', 'ogrn': '1027739041153',
        'ind': 'Рынок ценных бумаг',
        'desc': 'Инвестиционная компания группы «Регион»; основной бенефициар группы — Сергей Судариков.'}),
}
MATCH_KEYS = {'g470a51f2': ['ик регион']}

NOTES = {
    'g5880d206': {
        'no_profile': {
            'buyer': ('Две стороны по ЕГРЮЛ (25.02.2025): ООО «Экспомобилити» — 55%, Игорь Ким — 45% (AK&M); '
                      'одной ссылкой на профиль их не записать — текстом.'),
            'seller': ('По ЕГРЮЛ вышли Volkswagen Financial Services Overseas AG (99%) и Volkswagen Bank GmbH (1%) '
                       '(AK&M 26.02.2025); иностранные юрлица без ИНН — текстом.')},
    },
    'g703c4f62': {
        'no_profile': {'seller': ('Роман Авдеев — физлицо. Его 62% (по неофициальным данным) были косвенными: '
                                  '93,14% «Россиума» до 01.10.2025 держало ООО «ХК «Доминанта»» (ОГРН 1137746035460), '
                                  'а ее — ДоминантаФинанс 30%, ПрестиссимоФинанс 30%, Гравеинвест 20%, Итатрейд 10%, '
                                  'ЗПИФ «М-Капитал» 10% (ЕГРЮЛ, datanewton); Авдеева реестр не показывает, продавцом '
                                  'он назван сам (Интерфакс, Коммерсантъ).')},
        'checked': {'buyer_entity': ('Покупатель в схеме — АО «ИК «Регион»» (ИНН 7730095858): ему 01.10.2025 перешли '
                                     '93,14% ООО «Концерн «Россиум»» (AK&M по «Контур.Фокусу»); 90% «Доминанты» в '
                                     'тот же день получил Сергей Судариков — это в «Как устроена сделка».')},
    },
}


def _get(c, path):
    o = c
    parts = path.split('.')
    for p in parts[:-1]:
        o = o.setdefault(p, {})
    return o, parts[-1]


def _merge(dst, src):
    n = 0
    for k, v in src.items():
        if isinstance(v, dict):
            n += _merge(dst.setdefault(k, {}), v)
        elif dst.get(k) != v:
            dst[k] = v
            n += 1
    return n


def apply(data):
    by = {d['id']: d for d in data['deals']}
    comps = data['companies']
    n = 0
    for cid, path, old, new, quote, url in SETS:
        c = by[cid]
        part = path.endswith('@')
        o, k = _get(c, path.rstrip('@'))
        cur = o.get(k)
        if part:
            if new in (cur or ''):
                continue
            assert (cur or '').count(old) == 1, (cid, path, cur)
            o[k] = cur.replace(old, new)
            fact_edit_guard.log(c, path.rstrip('@'), o[k], quote, url, BY, DAY)
        else:
            if cur == new:
                continue
            assert cur == old, (cid, path, cur)
            if new is None:
                o.pop(k, None)
            else:
                o[k] = new
            if (cid, path) in RETRACT:
                c.setdefault('retracted', {}).setdefault(path, []).append(old)
            fact_edit_guard.log(c, path, new, quote, url, BY, DAY)
        n += 1
    c = by['g37f106cd']
    if c.get('sum_basis') == 'estimate':
        c.pop('sum_basis')
        n += 1
    for pid, (old_name, fields) in PROFILES.items():
        p = comps[pid]
        if p.get('name') == fields['name']:
            continue
        assert p.get('name') == old_name, (pid, p.get('name'))
        p.update(fields)
        n += 1
    mk = data.get('match_keys') or {}
    for pid, keys in MATCH_KEYS.items():
        if mk.get(pid) != keys:
            mk[pid] = keys
            n += 1
    for cid, notes in NOTES.items():
        n += _merge(by[cid].setdefault('accepted_notes', {}), notes)
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
