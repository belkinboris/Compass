# -*- coding: utf-8 -*-
"""Вычитка 17 ноября 2026, партия r1117b: описание профиля Buzzoola; сумма Nomi «Не раскрыта».

g478eb55f (ООО «Баззула интернет технологии», предмет сделки g47189119): описание профиля
рассказывало о сделке, а не о компании, и с ошибкой в доле — «в 2023 году 66% ее купила МТС»,
тогда как МТС купила 67% (Интерфакс, 887334: «стало владельцем 67% группы Buzzoola»; ЕГРЮЛ:
ООО «МТС Рекламные технологии» вошло с 67% 21 февраля 2023 года). Описание — о самой компании,
событие сделки — в карточке (docs/company_profiles.md, «Описание профиля»).

g162de6fb («Гельтек»/Nomi): цена не названа — в сумме стоял прочерк вместо «Не раскрыта», а в
«Оценке» — фраза «Сумму сделки Кирш не раскрыл.», хотя оценки нет (поле, где сказать нечего, — «—»).
Retailer.ru: «Сумму сделки стороны не раскрыли.»; New Retail: «Сумма сделки не раскрывается.»

    python3 pipeline/archive/2026-11/reread_profile_desc_r1117b.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PID = 'g478eb55f'
OLD = ('Платформа нативной видеорекламы (бренд Buzzoola, охват более 100 млн человек в РФ и СНГ); в 2023 году '
       '66% ее купила МТС с колл-опционом на оставшиеся 33% в 2024 году.')
BY, DAY = 'reread_profile_desc_r1117b', '2026-11-17'
NOMI = 'g162de6fb'
NOMI_VAL = 'Сумму сделки Кирш не раскрыл.'
Q_NOMI = ('Shopper’s, с 13 октября 100% долей управляющей компании марки — ООО «Компания новая идея» — принадлежат '
          'ООО «Гельтек РНД». Сумму сделки стороны не раскрыли.')
U_NOMI = 'https://retailer.ru/brend-detskoj-kosmetiki-nomi-pereshjol-pod-kontrol-gelteka/'
NEW = 'Платформа нативной видеорекламы (бренд Buzzoola) с охватом более 100 млн человек в России и странах СНГ.'


def apply(data):
    n = 0
    p = data['companies'][PID]
    if p.get('desc') != NEW:
        assert p.get('desc') == OLD, p.get('desc')
        p['desc'] = NEW
        n += 1
    c = next(x for x in data['deals'] if x['id'] == NOMI)
    if c.get('sum') != 'Не раскрыта':
        assert c.get('sum') in (None, '—') and c['eco'].get('sum') == '—', (c.get('sum'), c['eco'].get('sum'))
        c['sum'] = 'Не раскрыта'
        c['eco']['sum'] = 'Не раскрыта'
        fact_edit_guard.log(c, 'sum', 'Не раскрыта', Q_NOMI, U_NOMI, BY, DAY)
        fact_edit_guard.log(c, 'eco.sum', 'Не раскрыта', Q_NOMI, U_NOMI, BY, DAY)
        n += 1
    if c['eco'].get('val') != '—':
        assert c['eco'].get('val') == NOMI_VAL, c['eco'].get('val')
        c['eco']['val'] = '—'
        fact_edit_guard.log(c, 'eco.val', '—', Q_NOMI + ' — оценки нет, поле пусто.', U_NOMI, BY, DAY)
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
    if not apply(fresh):
        print('Уже применено.')
        return 0
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
