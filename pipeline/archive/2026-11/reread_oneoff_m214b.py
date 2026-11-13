# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m214 (вторая часть): то, чего не умеет review.py.

g97a481d8 (РНКО «Деньги.Мэйл.Ру»):
  * покупатель — ООО «Компания ВК» (профиль g2ed1a259), а не МКПАО «ВК»: АК&М (20.02.2023) — «Путин разрешил
    ООО «Компания ВК» приобрести 100%»; ЕГРЮЛ (datanewton.ru, ОГРН РНКО 1127711000042): 06.03.2023 вышла
    «Пи.Джей.Ви. Диджитал Форсис Лтд» (100%, 90 000 000 руб.), вошло ООО «Компания ВК» (ОГРН 1097746572813, 100%).
  * «90 млн ₽ (по оценке)» — номинальная стоимость 100% доли по ЕГРЮЛ (Sostav: «Доля … оценивается в 90 млн
    руб.»), не цена сделки: сумма «Не раскрыта», номинал — в eco.val; дата 06.03.2023 — по реестру.
  * ИНН предмета 7750005718 (ОГРН 1127711000042): справочник Банка России по кредитным организациям и
    OpenSanctions (РНКО «ВК Платежные решения»); описания профилей предмета и продавца — без нашего вывода
    «перевод внутри группы» и непроверенного «указ подписан 17 февраля».
gec757ede (Fix Price): статья «Коммерсанта» 8764989 — о невыплате дивидендов за 2025 год (2026 год), не об
  обмене ГДР; источник снят, финансы оттуда сняты правкой eco.target_fin.

    python3 pipeline/archive/2026-11/reread_oneoff_m214b.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
BY, DAY = 'reread_oneoff_m214b', '2026-11-12'
EGRUL = ('ЕГРЮЛ, РНКО «Деньги.Мэйл.Ру» (ОГРН 1127711000042), история участников (datanewton.ru): 2023-03-06 '
         'left ПИ.ДЖЕЙ.ВИ. ДИДЖИТАЛ ФОРСИС ЛТД 100.0% (90 000 000 руб.); 2023-03-06 joined ООО «КОМПАНИЯ ВК» '
         '(ОГРН 1097746572813) 100.0% (90 000 000 руб.)')
AKM = 'https://www.akm.ru/news/v_putin_razreshil_vk_kupit_dengi_meyl_ru/'
SOSTAV = 'https://www.sostav.ru/publication/vk-59320.html'
VAL = 'Номинальная стоимость 100% доли по ЕГРЮЛ — 90 млн ₽; цена сделки не раскрыта.'
TARGET_DESC = ('Расчетная небанковская кредитная организация группы VK; в феврале 2024 года переименована в '
               'РНКО «ВК Платежные решения».')
SELLER_DESC = ('Кипрская компания международного холдинга VK Company Limited; до марта 2023 года владела 100% '
               'РНКО «Деньги.Мэйл.Ру».')
REG_ROW = {'company_id': 'g03bd26c1', 'decision': 'confirmed', 'inn': '7750005718', 'date': '2026-11-13',
           'reason': 'РНКО «Деньги.Мэйл.Ру» (с февраля 2024 года — РНКО «ВК Платежные решения» (ООО)), ИНН '
                     '7750005718, ОГРН 1127711000042: справочник кредитных организаций Банка России и '
                     'OpenSanctions (ru-bik-044525701); по тому же ОГРН история участников ЕГРЮЛ (datanewton.ru) — '
                     'с 06.03.2023 единственный участник ООО «Компания ВК». Вычитка m214.'}
LEGAL = 'РНКО «Деньги.Мэйл.Ру» (ООО)'   # АК&М: «РНКО «Деньги.Мэйл.Ру» (ООО)»; ЕГРЮЛ — ООО, ОГРН 1127711000042
KOMM = ['Коммерсантъ', 'https://www.kommersant.ru/doc/8764989']


def apply(data):
    by = {d['id']: d for d in data['deals']}
    comps = data['companies']
    n = 0
    c = by['g97a481d8']
    if c.get('buyer') != 'g2ed1a259':
        assert c.get('buyer') == 'g4e694234', c.get('buyer')
        c['buyer'] = 'g2ed1a259'
        fact_edit_guard.log(c, 'buyer', 'g2ed1a259', EGRUL, AKM, BY, DAY)
        n += 1
    if c['sum'] != 'Не раскрыта':
        old = '90 млн ₽ (по оценке)'
        assert c['sum'] == old and c['eco']['sum'] == old, c['sum']
        c['sum'] = c['eco']['sum'] = 'Не раскрыта'
        c.setdefault('retracted', {}).setdefault('sum', []).append(old)
        q = 'Доля «Компании ВК» в РНКО оценивается в 90 млн руб. — это номинал 100% доли по ЕГРЮЛ (' + EGRUL + '), не цена.'
        fact_edit_guard.log(c, 'sum', 'Не раскрыта', q, SOSTAV, BY, DAY)
        fact_edit_guard.log(c, 'eco.sum', 'Не раскрыта', q, SOSTAV, BY, DAY)
        n += 1
    if c['eco'].get('val') != VAL:
        assert c['eco'].get('val') == '—', c['eco'].get('val')
        c['eco']['val'] = VAL
        fact_edit_guard.log(c, 'eco.val', VAL, EGRUL, '', BY, DAY)
        n += 1
    if c.get('date_basis') != 'registry':
        assert c['date'] == '2023-03-06', c['date']
        c['date_basis'] = 'registry'
        fact_edit_guard.log(c, 'date', '2023-03-06', EGRUL, '', BY, DAY)
        n += 1
    for pid, new in (('g03bd26c1', TARGET_DESC), ('gd6f2d2a5', SELLER_DESC)):
        if comps[pid].get('desc') != new:
            assert comps[pid].get('desc', '').startswith(('Небанковская кредитная', 'Кипрская структура')), pid
            comps[pid]['desc'] = new
            n += 1
    if comps['g03bd26c1'].get('legal_short') != LEGAL:
        assert not comps['g03bd26c1'].get('legal_short')
        comps['g03bd26c1']['legal_short'] = LEGAL
        n += 1
    c = by['gec757ede']
    if KOMM in c['src']:
        c['src'] = [s for s in c['src'] if s != KOMM]
        n += 1
    return n


def apply_reg(rows):
    if any(r.get('company_id') == 'g03bd26c1' for r in rows):
        return 0
    rows.append(dict(REG_ROW))
    return 1


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data) + apply_reg(json.load(open(REG, encoding='utf-8')))
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
    reg_raw = open(REG, encoding='utf-8').read()
    rows = json.loads(reg_raw)
    if apply_reg(rows):
        with open(REG, 'w', encoding='utf-8') as f:
            f.write(json.dumps(rows, ensure_ascii=False, indent=1) + ('\n' if reg_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
