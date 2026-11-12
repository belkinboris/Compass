# -*- coding: utf-8 -*-
"""Вычитка базы, партия m070 (12 ноября 2026), часть A: то, что не ложится в таблицу FIXES.

gmru-veb-gtlk — дата 2026-06-02 была днем объявления Шувалова; договор подписан «на прошлой неделе» (конец мая),
  дня в источниках нет — дата годом «2026». РБК (первоисточник заметки mergers.ru) — первым в src, плюс Ведомости и
  Эксперт. Профилю ГТЛК — ИНН 7720261827 (ЕГРЮЛ в facts.target и раскрытие ЦБ cbr.ru/rbr/insidedko, RAEX) и имя с
  правовой формой.
  Профилю НСПК — ИНН 7706812159 и «АО «НСПК»» (ЕГРЮЛ через /api/companies/<id>/fns, в досье).
gmru-nspk-privatization — событие «Готовится рыночная оценка»: день заявления Набиуллиной 2 июля (а не номера
  газеты 3 июля), пересказ своими словами (near_copy). Источники: ПРАЙМ (Пьянов, 28 июля), Эксперт (RWB, Ozon, МТС,
  «Яндекс»).
baltika — дата 2024-12-04 ни в одном источнике не названа; по ЕГРЮЛ (история участников) АО «ВГ Инвест» вошло в
  участники 5 декабря 2024 года — дата по реестру. Источники: Интерфакс о мировом соглашении, New Retail о прибыли 2025.
rosatom-mali — дата 2024-07-15 выдумана (в июле 2024 года Мали лишь одобрило передачу разрешения Moketi Mining);
  о покупке малийской компании Лихачев сообщил 30 октября 2026 года — дата объявления. Предмет — текстом; продавец
  и название компании не раскрыты (accepted_notes.no_profile).

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
SETS = [
    ('gmru-veb-gtlk', 'date', '2026-06-02', '2026',
     'Договор о приобретении акций ГТЛК был подписан еще на прошлой неделе, уточнил Шувалов.',
     'https://www.rbc.ru/business/02/06/2026/6a1ea6e79a794702d0df7ee3'),
    ('baltika', 'date', '2024-12-04', '2024-12-05',
     'ЕГРЮЛ, история участников ООО «Пивоваренная компания «Балтика»»: 2024-12-05 — АО «ВГ Инвест» вошло в участники '
     '(98,65%), Carlsberg Sverige Aktiebolag, Carlsberg Deutschland GmbH и ООО «Хоппи Юнион» вышли',
     'https://datanewton.ru/contragents/1147847032838/history/timeline'),
    ('baltika', 'date_basis', None, 'registry', None, None),
    ('rosatom-mali', 'date', '2024-07-15', '2026-10-30',
     'МОСКВА, 30 окт - ПРАЙМ. "Росатом" приобрел малийскую компанию для реализации проекта на литиевом месторождении '
     'Бугула, сообщил гендиректор госкорпорации Алексей Лихачев.', 'https://1prime.ru/20261030/rosatom-874832259.html'),
    ('rosatom-mali', 'date_basis', None, 'announcement', None, None),
    ('rosatom-mali', 'asset', None, 'Малийская компания для проекта на литиевом месторождении Бугула',
     '"В Мали литиевое месторождение Бугула. На сегодняшний день ... мы приобрели непосредственно компанию местную для '
     'реализации этого проекта и в полном ходе идут изыскания", - сказал Лихачев',
     'https://1prime.ru/20261030/rosatom-874832259.html'),
]
SRC = [  # (id, [издание, адрес], первым ли)
    ('gmru-veb-gtlk', ['РБК', 'https://www.rbc.ru/business/02/06/2026/6a1ea6e79a794702d0df7ee3'], True),
    ('gmru-veb-gtlk', ['Ведомости', 'https://www.vedomosti.ru/industry/infrastructure_development/articles/2026/06/03/1202568-gtlk-pereshla-pod-upravlenie-vebrf'], False),
    ('gmru-veb-gtlk', ['Expert.ru', 'https://expert.ru/news/vebrf-zavershil-sdelku-po-priobreteniyu-gosudarstvennoy-lizingovoy-kompanii-gtlk'], False),
    ('gmru-nspk-privatization', ['ПРАЙМ', 'https://1prime.ru/20260728/vtb-871811311.html'], False),
    ('gmru-nspk-privatization', ['Expert.ru', 'https://expert.ru/finance/platformy-khotyat-idti-s-mirom'], False),
    ('baltika', ['Интерфакс', 'https://www.interfax.ru/business/1000191'], False),
    ('baltika', ['New Retail', 'https://new-retail.ru/novosti/retail/chistaya_pribyl_baltiki_za_2025_god_vdvoe_prevysila_ubytok_predydushchego_goda/'], False),
]
EVENTS = [  # (id, номер, поле, старое, новое)
    ('gmru-nspk-privatization', 1, 'date', '2026-07-03', '2026-07-02'),
    ('gmru-nspk-privatization', 1, 'note',
     'Глава Банка России Эльвира Набиуллина заявила об обсуждении с банками частичной приватизации НСПК; планируется рыночная оценка компании.',
     'На Финансовом конгрессе Эльвира Набиуллина сказала, что ЦБ обсуждает с банками продажу части НСПК и сначала закажет рыночную оценку компании.'),
]
NOTES = {
    'rosatom-mali': {'no_profile': {
        'seller': 'Продавец не раскрыт: Лихачев (ПРАЙМ, 30.10.2026) назвал только «компанию местную»; искали в Интерфаксе, '
                  'ПРАЙМ, Neftegaz.ru, отчете АО «Атомэнергопром» за 2025 год и в сообщениях Минпрома Мали о Moketi Mining SARL',
        'target': 'Название купленной малийской компании не раскрыто (ПРАЙМ, Интерфакс, Neftegaz.ru); разрешение на Бугулу '
                  'с июля 2024 года у Moketi Mining SARL (Uranium One), но что куплена именно она, источники не говорят'}},
}
PROFILES = [  # (id профиля, поле, старое, новое)
    ('g2322c829', 'inn', None, '7720261827'),
    ('g2322c829', 'legal_short', None, 'АО «ГТЛК»'),
    ('gc6e1e175', 'inn', None, '7706812159'),
    ('gc6e1e175', 'legal_short', None, 'АО «НСПК»'),
    ('vginvest', 'legal_short', None, 'АО «ВГ Инвест»'),
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
