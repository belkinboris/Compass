# -*- coding: utf-8 -*-
"""Тридцать третья партия: 8 описаний. Заодно закрывает систематический
промер (`measure_profile_name_vs_deal_titles.py`) — последние 4
непрочитанных кандидата слабого сигнала (ООО «РВБ», Владимир Воронин,
Russ Outdoor, Александр Рязанов) прочитаны и оказались законными: одна
и та же сторона покупает разное под разными формулировками заголовка,
коллизий нет. Владимир Воронин и Александр Рязанов заодно получили
описания — были без них.

ЧТО ДЕЛАЕТ. 8 описаний.

Запуск:
    python3 pipeline/write_company_descriptions_batch33.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch33.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

DESCRIPTIONS = {
    'ga0cdd290': 'Владелец группы компаний ФСК; инвестирует лично в '
                 'медицинские сервисы («Врач на дом», «АВС-Медицина») и '
                 'консолидирует стекольные активы через ФСК.',
    'ga09351d2': 'Частный инвестор; продал долю в ООО «Меридиан-Сервис» '
                 '(консорциум по выкупу активов «Яндекса») структурам '
                 'Потанина, приобрёл у ЕБРР долю в «Хлебпроме».',
    'g7ce3696d': 'Платформа для поиска подработки и разнорабочих; среди '
                 'инвесторов — ФРИИ и «Ростелеком» (через «Коммит '
                 'Кэпитал»).',
    'gfd02a072': 'Британское подразделение брокера БКС; в 2024 году 75% '
                 'акций выкупил консорциум GBM Holding.',
    'gfd143c7d': 'Элеватор в Орловской области (10 силосов, 50 000 '
                 'тонн хранения); в 2023 году выкуплен '
                 '«Деметра-холдингом».',
    'gfc0e493d': 'Региональный оператор наружной рекламы; в 2023 году '
                 'выкуплен совместной компанией Wildberries и Russ '
                 'Outdoor (РВБ).',
    'gfeb1cca1': 'Предприниматель, ранее блокирующий акционер '
                 'петербургского завода Tensar; в 2023 году выкупил '
                 'оставшиеся 75% акций у американской материнской '
                 'компании.',
    'gfd02e26a': 'Платформа для экспортных B2B-сделок; привлекла $4 млн '
                 'от ганского инвестора Исаака Кваку Фокуо-мл. за 5% '
                 'доли.',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  ОПИСАНИЕ %-12s %-30s %s' % (cid, str(c.get('name'))[:30], text[:50]))
        c['desc'] = text
        wrote += 1

    print('\nОписаний записано: %d' % wrote)
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

    real = sum(1 for v in comps.values()
               if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
    print('Всего профилей с описанием: %d из %d (%d%%)'
          % (real, len(comps), round(100 * real / len(comps))))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
