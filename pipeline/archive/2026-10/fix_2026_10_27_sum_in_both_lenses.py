"""Сумма названа в «Экономисте» (eco.sum), а на «Обзоре» (sum) пусто —
«Обзор» показывал «Не раскрыта» при 1,427 млрд ₽ в соседней вкладке
(владелец, 27 октября 2026, «Агропромкредит»: «в обзоре не раскрыта сумма,
а в экономисте написана»). Копирует eco.sum в sum, когда eco.sum начинается
с числа или оценочного слова («более», «около», «не менее», «≈»); пояснения
вида «Не раскрыта (…)» не трогает — там пустой sum верен.

Та же карточка: контекст про уголовное дело заменен на историю самой
сделки (изъятие банка, продажа ПСБ на повторных торгах).

    python3 pipeline/fix_2026_10_27_sum_in_both_lenses.py            # сухой прогон
    python3 pipeline/fix_2026_10_27_sum_in_both_lenses.py --write    # затем facts_derive.py --write
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PRICE_LIKE = re.compile(r'^\s*(?:≈|~|более|около|не менее|свыше|до)?\s*\d', re.I)
CONTEXT_OLD = ('Это не первый актив той же истории, который меняет владельца: раньше уже разошлись энергоактивы Артема Бикова '
               'и Алексея Боброва в трех регионах — их забрали «Россети». По уголовному делу о мошенничестве сейчас проходит '
               'только Бобров; Биков фигурантом не является и, по информации СМИ, не находится под стражей.')
CONTEXT_NEW = ('Банк «Агропромкредит» был изъят у Артема Бикова и Алексея Боброва по иску Генпрокуратуры и достался ПСБ. '
               'На повторных торгах лот — 50% банка напрямую и две компании, владеющие оставшейся долей, — купила «ЭсЭфАй» '
               'за 1,427 млрд ₽. Ранее тем же путем ушли энергоактивы Бикова и Боброва в трех регионах — их получили «Россети».')


def has(v):
    v = str(v or '').strip()
    return bool(v) and v not in ('—', '-', '–', 'None', 'Не раскрыта')


def plan(base):
    out = []
    for d in base['deals']:
        eco_sum = (d.get('eco') or {}).get('sum')
        if not has(d.get('sum')) and has(eco_sum) and PRICE_LIKE.search(str(eco_sum)):
            out.append((d, str(eco_sum).strip()))
    return out


def main(argv):
    write = '--write' in argv
    base = json.load(open(DATA, encoding='utf-8'))
    items = plan(base)
    for d, s in items:
        print('  %s %s — sum ← %r' % (d['id'], d['title'][:50], s))
    print('Карточек: %d.' % len(items))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh = json.load(open(DATA, encoding='utf-8'))
    for d, s in plan(fresh):
        s = re.sub(r'\s*(?:рублей|руб\.?)\b', ' ₽', s).replace('  ', ' ')      # валюта — знаком, как в обложке
        s = s.split(';')[0].strip()                                             # в sum — только цена, без истории торгов
        s = s.replace('(стартовая цена аукциона)', '(начальная цена)')
        d['sum'] = s
        if re.search(r'рублей|руб\.', str(d['eco'].get('sum') or '')):
            d['eco']['sum'] = s
    agro = next(x for x in fresh['deals'] if x['id'] == 'g1f8414a3')
    assert agro['eco'].get('context') == CONTEXT_OLD, 'контекст Агропромкредита уже менялся'
    agro['eco']['context'] = CONTEXT_NEW
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
