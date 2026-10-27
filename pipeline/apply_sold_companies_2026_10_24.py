"""ИНН проданных компаний в сделках с нераскрытой ценой (24 октября 2026).

Зачем: оценка сделки без цены строится по отчетности проданной компании, а
она есть, только если компания опознана как юрлицо с ИНН. Два читателя
разобрали 217 таких сделок по заданию `data/inbox/valuation/targets/BRIEF.md`,
ответы — `batchA.result.json` и `batchB.result.json` там же. Владелец
24 октября: «Даю добро» — на надежные совпадения (`confidence: high`).
Средние и низкие ждут второй проверки (`doubtful.result.json`) и ответа людей
по `data/inbox/valuation/ПРОВЕРКА.md`.

Что делает скрипт:
  * у профиля предмета сделки нет ИНН (`no_registry`) или его искали и не
    нашли (`no_match`) — строка `confirmed` в `pipeline/fns_registry.py`,
    прежняя `no_match` снимается тем же блоком;
  * у сделки нет профиля предмета — ИНН уже за профилем базы: предмет
    привязывается к нему; нет — новый профиль (имя и описание ниже, вручную)
    и строка реестра.

Не трогает: банки и страховщиков (их ИНН ставится цепочкой ЦБ с регномером,
а оценку банков владелец отложил); профили-лоты; продано несколько юрлиц сразу (группа — ИНН одного из них
показал бы на сайте отчетность части группы как всей) и имущество; ИНН,
который реестр уже держит за ДРУГИМ профилем (это дубль профилей — чинится
отдельно); роль, которая уже занята.

Без ключа — сухой прогон; `--write` перечитывает базу прямо перед записью.
"""
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import link_parties  # noqa: E402
from pipeline import fns_registry  # noqa: E402
from apply_party_profiles_2026_10_23 import inn_ok, new_id, apply_links  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG = os.path.join(ROOT, 'pipeline', 'fns_registry.py')
DIR = os.path.join(ROOT, 'data', 'inbox', 'valuation', 'targets')
DAY = '2026-10-24'

# Новые профили предметов: имя как на витрине и описание — по статье карточки
# и находке читателя (evidence), без домыслов.
NEW = {
    'c011c4ee1': ('ДПД Рус', 'Российская служба доставки посылок DPD (АО «ДПД Рус»), принадлежала GeoPost (DPD Group).'),
    'c07bedf76': ('Газпром СПКА', 'Сборочное производство космических аппаратов группы «Газпром» (ООО «Газпром СПКА»).'),
    'c0b43766f': ('Витязь Авто', 'Рыбопромышленное предприятие на юго-западе Камчатки: вылов и переработка лососевых, завод в Озерновском.'),
    'c0e44fb7b': ('ММЦ «СОГАЗ»', 'Сеть медицинских клиник, принадлежавшая группе СОГАЗ (ООО «ММЦ», бывшее ООО «Международный медицинский центр «СОГАЗ»»).'),
    'c1062263e': ('Метафракс Кемикалс', 'Химическое предприятие в Губахе (Пермский край): метанол и продукты его переработки.'),
    'c151696b4': ('Фин-проект', 'Единственный участник ООО «Ловозерский ГОК» (Мурманская область); собственной операционной выручки нет.'),
    'c1659a21f': ('Упаковочные системы', 'Бывшее российское подразделение Tetra Pak (АО «Тетра Пак», ныне АО «Упаковочные системы») с заводом в Лобне.'),
    'c1aa8b20d': ('Петропавловск-Камчатский морской торговый порт', 'Морской торговый порт в Петропавловске-Камчатском (ООО «ПКМТП»).'),
    'c1d2ba2c0': ('ЧЭМК', 'Челябинский электрометаллургический комбинат, производитель ферросплавов; принадлежал Юрию Антипову.'),
    'c36556448': ('ТД «Библио-Глобус»', 'Книжный магазин «Библио-Глобус» в Москве (ООО «Торговый дом «Библио-Глобус»»).'),
    'c43cb8f80': ('Нижфарм', 'Фармацевтическая компания в Нижнем Новгороде (АО «Нижфарм»).'),
    'c460a1f82': ('Порт Вера', 'Угольный порт в Приморском крае (ООО «Порт «Вера»»).'),
    'c4a6060cd': ('Холдинг ВВСС', 'Холдинг, владеющий 100% оператора аэропорта Пулково ООО «Воздушные ворота Северной столицы».'),
    'cb30dbbc8': ('SolidSoft', 'Российский разработчик средств кибербезопасности (ООО «Солидсофт»).'),
    'cb44ed7f0': ('Рив Гош', 'Сеть парфюмерно-косметических магазинов «Рив Гош» (ООО «Аромалюкс»).'),
    'cbb6ba4c9': ('Пушкинский', 'Владелец кинотеатра «Россия» на Пушкинской площади в Москве (АО «Пушкинский»).'),
    'cd47c5acc': ('Монэкс трейдинг', 'Российская сеть детских товаров Mothercare: 118 магазинов в 30 регионах (ООО «Монэкс трейдинг»).'),
    'cf2375bf5': ('Квартал Герцена', 'Застройщик девелоперского проекта «Квартал Герцена» (ООО «Квартал Герцена»).'),
    'g4fc7af86': ('Инсайт Комкон', 'Российское подразделение исследовательской компании Ipsos (ООО «Ипсос Комкон», ныне ООО «Инсайт Комкон»).'),
    'cfdc0e962': ('Жемчужная плаза', 'Владелец торгово-развлекательного комплекса «Жемчужная плаза» в Санкт-Петербурге (ООО «Жемчужная плаза»).'),
    'gde84040f': ('Исткульт Можайск', 'Завод газобетона в Можайске, 500 тыс. куб. м блоков в год; до 2022 года выпускал продукцию Ytong группы Xella.'),
}
# Профиль с тем же именем в базе уже есть — прочитано глазами 24 октября: та
# же компания, ИНН у нее не было. Предмет привязывается к нему, ИНН — ему же;
# пустое описание заменяется описанием из NEW.
SAME_AS = {'c011c4ee1': 'ge730f6b6', 'c1062263e': 'geef721b8',
           'c43cb8f80': 'g09636d48', 'cb44ed7f0': 'g842a7fd2'}
# Карточка — ранний этап сделки, которая лежит в базе второй, закрытой
# карточкой (O'Key Group → менеджмент: «обсуждается» 2024 и «закрыта» 2025).
# Привязка предмета столкнула бы их в test_no_two_cards_claim_one_deal_…;
# сначала слить этапы, потом привязывать.
HOLD = {'ccdd90216'}
# Предмет — группа, у которой в базе уже есть профиль с ИНН операционной
# компании (вторая проверка, doubtful.result.json): только привязка.
# «Волга-Днепр»: продано головное ООО «Волга-Днепр-Москва», а профиль
# g83feabb2 держит ИНН авиакомпании, по отчетности которой и оценивают.
LINK_ONLY = {'c49c9d8b0': 'g83feabb2', 'c6fd3a848': 'g83feabb2'}
EMPTY_DESC = 'Описание компании пока не добавлено.'
# Несколько юрлиц в одном ответе: «ООО «А» и ООО «Б»», «(+ ООО …)», «крупнейшая из».
MANY = re.compile(r'»\s*(?:и|,)\s*(?:ООО|АО|ПАО|«)|\(\+|крупнейш')


def load():
    out = []
    for b in 'AB':
        src = {r['deal']: r for r in json.load(open(os.path.join(DIR, 'batch%s.json' % b), encoding='utf-8'))}
        for r in json.load(open(os.path.join(DIR, 'batch%s.result.json' % b), encoding='utf-8')):
            out.append(dict(r, src=src[r['deal']]))
    # Вторая, более глубокая проверка средних и низких совпадений (24 октября):
    # ее ответ заменяет первый.
    second = os.path.join(DIR, 'doubtful.result.json')
    if os.path.exists(second):
        again = {r['deal']: r for r in json.load(open(second, encoding='utf-8'))}
        out = [dict(again[r['deal']], src=r['src']) if r['deal'] in again else r for r in out]
    return out


def reason(r):
    text = 'Поиск юрлиц проданных компаний (%s): %s' % (DAY, r['legal_name'])
    if r.get('ogrn'):
        text += '; ОГРН %s' % r['ogrn']
    return '%s; ИНН %s. %s' % (text, r['inn'], str(r.get('evidence') or '').strip())


def plan(data, rows):
    comps = data['companies']
    industries = {v.get('ind') for v in comps.values() if v.get('ind')}
    key_index = link_parties.build_index(comps)
    owner = {}
    for row in fns_registry.REGISTRY:
        if row.get('decision') == 'confirmed' and row.get('inn') and row['company_id'] in comps:
            owner.setdefault(str(row['inn']), row['company_id'])
    current = fns_registry.by_company_id()
    new_profiles, reg_rows, links, notes, descs = {}, [], [], defaultdict(list), {}
    for r in rows:
        s, inn = r['src'], str(r.get('inn') or '')
        if r.get('confidence') != 'high':
            notes['ждёт проверки'].append(r['deal']); continue
        if r['deal'] in LINK_ONLY and r.get('confidence') == 'high':
            links.append((r['deal'], 'target', LINK_ONLY[r['deal']], r['legal_name'])); continue
        if r['deal'] in HOLD:
            notes['отложено: дубль карточки'].append(r['deal']); continue
        if r.get('what_sold') == 'asset':
            notes['имущество'].append(r['deal']); continue
        if MANY.search(r.get('legal_name') or ''):
            notes['несколько юрлиц'].append(r['deal']); continue
        if s.get('ind') in ('Банки', 'Страхование'):
            # ИНН банка ставится цепочкой ЦБ → ЕГРЮЛ с регномером (docs/company_data.md),
            # а оценку банков владелец отложил.
            notes['банк или страховщик'].append(r['deal']); continue
        if s.get('target_id') and comps.get(s['target_id'], {}).get('lot'):
            notes['профиль-лот'].append(r['deal']); continue
        if not inn_ok(inn):
            notes['ИНН не проходит контрольную сумму'].append((r['deal'], inn)); continue
        if s['status'] in ('no_registry', 'no_match'):
            cid = s['target_id']
            if owner.get(inn, cid) != cid:
                notes['ИНН уже за другим профилем'].append((r['deal'], comps[owner[inn]]['name'])); continue
            if (current.get(cid) or {}).get('decision') == 'confirmed':
                notes['у профиля уже есть ИНН'].append(r['deal']); continue
            if any(x['company_id'] == cid for x in reg_rows):
                continue                                    # тот же профиль во второй сделке
            reg_rows.append({'company_id': cid, 'decision': 'confirmed', 'inn': inn,
                             'reason': reason(r), 'date': DAY})
            owner[inn] = cid
            continue
        # нет профиля предмета
        if inn in owner:
            links.append((r['deal'], 'target', owner[inn], r['legal_name'])); continue
        if r['deal'] not in NEW:
            notes['группа без профиля — не заводим'].append(r['deal']); continue
        name, desc = NEW[r['deal']]
        if r['deal'] in SAME_AS:
            cid = SAME_AS[r['deal']]
            assert link_parties.company_key(comps[cid]['name']) == link_parties.company_key(name)
            if cid not in current and not any(x['company_id'] == cid for x in reg_rows):
                reg_rows.append({'company_id': cid, 'decision': 'confirmed', 'inn': inn,
                                 'reason': reason(r), 'date': DAY})
                owner[inn] = cid
            if comps[cid].get('desc') == EMPTY_DESC:
                descs[cid] = desc
            links.append((r['deal'], 'target', cid, r['legal_name']))
            continue
        key = link_parties.company_key(name)
        if key and key_index.get(key):
            notes['близнец по имени — разобрать руками'].append((name, sorted(key_index[key]))); continue
        ind = s.get('ind') if s.get('ind') in industries else None
        assert ind, (r['deal'], s.get('ind'))
        cid = new_id(name, set(comps) | set(new_profiles))
        new_profiles[cid] = {'name': name, 'ind': ind, 'desc': desc, 'kpi': []}
        reg_rows.append({'company_id': cid, 'decision': 'confirmed', 'inn': inn, 'reason': reason(r), 'date': DAY})
        owner[inn] = cid
        links.append((r['deal'], 'target', cid, r['legal_name']))
    return new_profiles, reg_rows, links, notes, descs


def write_registry(rows):
    known = {r['company_id'] for r in fns_registry.REGISTRY}
    replaced = sorted({r['company_id'] for r in rows} & known)
    src = open(REG, encoding='utf-8').read()
    marker = "\n\ndef by_company_id() -> dict[str, dict]:"
    assert marker in src
    lines = ['', '', '# Юрлица проданных компаний в сделках с нераскрытой ценой — %s' % DAY,
             '# (pipeline/apply_sold_companies_2026_10_24.py, ответы читателей в',
             '# data/inbox/valuation/targets/).']
    if replaced:
        lines += ['# Эти профили искали раньше и не нашли юрлица — прежние записи заменены.',
                  'REGISTRY = [row for row in REGISTRY if row["company_id"] not in %r]' % (set(replaced),)]
    lines.append('REGISTRY += [')
    for r in rows:
        lines.append('    {"company_id": %r, "decision": %r, "inn": %r,' % (r['company_id'], r['decision'], r['inn']))
        lines.append('     "reason": %r,' % r['reason'])
        lines.append('     "date": %r},' % r['date'])
    lines.append(']')
    open(REG, 'w', encoding='utf-8').write(src.replace(marker, '\n'.join(lines) + marker, 1))


def main(write):
    rows = load()
    data = json.load(open(DATA, encoding='utf-8'))
    new_profiles, reg_rows, links, notes, descs = plan(data, rows)
    data['companies'].update(new_profiles)
    done, skipped = apply_links(data, links)
    print('ответов %d; новых профилей %d; строк реестра %d; привязок %d, пропущено %d; описаний %d'
          % (len(rows), len(new_profiles), len(reg_rows), len(done), len(skipped), len(descs)))
    for k, v in notes.items():
        print('  %s: %d — %s' % (k, len(v), v[:8]))
    for s in skipped:
        print('  пропуск привязки:', s)
    if not write:
        return
    fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
    assert not set(new_profiles) & set(fresh['companies'])
    fresh['companies'].update(new_profiles)
    for cid, desc in descs.items():
        assert fresh['companies'][cid].get('desc') == EMPTY_DESC, cid
        fresh['companies'][cid]['desc'] = desc
    done2, _ = apply_links(fresh, links)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(fresh, f, indent=1, ensure_ascii=False)
        f.write('\n')
    write_registry(reg_rows)
    print('записано: профилей %d, строк реестра %d, привязок %d' % (len(new_profiles), len(reg_rows), len(done2)))


if __name__ == '__main__':
    main('--write' in sys.argv)
