# -*- coding: utf-8 -*-
"""Вычитка 3 ноября 2026, ночь (партия na): правки, которых review.py не умеет.

gedfd4c1e (Herbalife/Bioniq) — предмет стоял на чужом профиле.
  Профиль g06264a27 «Цифровая платформа Bioniq» — это российское ООО «Байоник-Медси»
  (ИНН 9710081787, СП Bioniq и ГК «Медси»; в fns_registry.json подтверждено пресс-релизами
  «Медси» и АФК «Система»), и он верен для своей сделки g6a6de6a6 (Федор Викторов купил 25%
  у «Медси»). Herbalife же купила почти все активы основного бизнеса британской Bioniq у
  BQ Holding Ltd. (Herbalife 10-Q за II квартал 2026: «asset purchase agreement with BQ
  Holding Ltd. and its subsidiaries (Bioniq), a UK-based, personalized supplements company»),
  а российское ООО в сделку не входило: по реестру его участники после 10 февраля 2025 года
  не менялись (75% у СКТ «Бикью Венчурс ЭсЭсПи», 25% у Федора Викторова). Из-за этого
  приемка требовала у предмета имя «ООО «Байоник-Медси»», а пост называл предметом
  «Цифровую платформу Bioniq» с описанием про выход «Медси» из российского СП.
  Правило — docs/company_profiles.md, «Один профиль на две компании»: ошибочная роль
  переносится на новый профиль, исходный не трогается. Новый профиль — «Bioniq»,
  иностранная компания, без ИНН; псевдонимов нет нарочно: «bioniq» ловил бы заголовок
  сделки «Медси» про российское ООО.

ga9aa543c (CVS Health/Oak Street Health) — где искали продавца (accepted_notes.no_profile.seller):
  Oak Street Health — публичная компания (NYSE), CVS выкупила все акции в обращении по $39
  за штуку через слияние; продавцы — все акционеры. Крупнейшие по DEFM14A: General Atlantic
  25,16%, Newlight Partners 13,34%, FMR 10,13%. Находка seller_search не держит отметку, но
  без записи повторяется у каждой проверки.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_na.py            # сухой прогон
    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_na.py --write    # затем facts_derive.py --write
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

HLF_DEAL = 'gedfd4c1e'
OLD_TARGET = 'g06264a27'
NEW_PROFILE = {
    'name': 'Bioniq',
    'ind': 'Здравоохранение',
    'desc': 'Британская компания персонализированных пищевых добавок: подбирает состав по анализу крови и '
            'анкете. Основана в 2019 году в Лондоне Вадимом Федотовым; в России у нее есть дочерняя '
            'структура — ООО «Байоник-Медси».',
    'kpi': [],
}

CVS_DEAL = 'ga9aa543c'
CVS_SELLER_NOTE = ('Публичная компания (NYSE): CVS Health выкупила все акции Oak Street Health в обращении по $39 '
                   'через слияние, продавцы — все акционеры. Крупнейшие перед голосованием (DEFM14A, SEC): '
                   'General Atlantic 25,16%, Newlight Partners 13,34%, FMR 10,13%; отдельного продавца нет.')


def new_id(base):
    cid = 'g' + hashlib.sha1('Bioniq|UK|gedfd4c1e'.encode('utf-8')).hexdigest()[:8]
    assert cid not in base['companies'], cid
    return cid


def deal(base, did):
    return next(d for d in base['deals'] if d['id'] == did)


def plan(base):
    hlf = deal(base, HLF_DEAL)
    assert hlf.get('target') == OLD_TARGET, 'предмет Herbalife уже другой: %r' % hlf.get('target')
    assert base['companies'][OLD_TARGET]['name'] == 'Цифровая платформа Bioniq'
    assert hlf.get('seller') == 'BQ Holding Ltd.'
    cvs = deal(base, CVS_DEAL)
    assert not (cvs.get('seller') or cvs.get('seller_id')), 'у CVS/Oak Street уже есть продавец'
    assert 'seller' not in ((cvs.get('accepted_notes') or {}).get('no_profile') or {})
    return hlf, cvs, new_id(base)


def apply(base):
    hlf, cvs, cid = plan(base)
    base['companies'][cid] = dict(NEW_PROFILE)
    base['match_keys'][cid] = []
    hlf['target'] = cid
    notes = cvs.get('accepted_notes') or {}
    notes.setdefault('no_profile', {})['seller'] = CVS_SELLER_NOTE
    cvs['accepted_notes'] = notes
    return cid


def main(argv):
    base = json.load(open(DATA, encoding='utf-8'))
    hlf, cvs, cid = plan(base)
    print('%s: target %s «Цифровая платформа Bioniq» (ООО «Байоник-Медси») → новый профиль %s «Bioniq»'
          % (HLF_DEAL, OLD_TARGET, cid))
    print('%s: accepted_notes.no_profile.seller ← %s…' % (CVS_DEAL, CVS_SELLER_NOTE[:70]))
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
    apply(fresh)
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано. Дальше: python3 pipeline/facts_derive.py --write')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
