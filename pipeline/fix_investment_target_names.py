# -*- coding: utf-8 -*-
"""«Инвестиции X»/«Продажа X» — имя вписано по ИНВЕСТОРУ, а не по
получателю. Продолжение находки из прошлого прогона.

ЧТО СЛОМАНО. У 6 профилей группы «имя — глагол сделки» (найдена в
прошлом прогоне, `fix_deal_composition_company_names.py`) дефект не
только в лишнем слове — сам `target` указывает на профиль ИНВЕСТОРА или
ПРОДАВЦА, а не получателя инвестиции/предмета продажи:

* `g04a9090b` «Инвестиции Hyundai» — деньги получил стартап Arrival
  (Hyundai и Kia — инвесторы, раунд A, 3,33% за €3 млрд оценки), не сам
  Hyundai.
* `gc8e3ac2b` «Инвестиции Gagarin Capital» — получатель — австралийский
  стартап Earth AI (поиск месторождений с помощью ИИ), Gagarin Capital
  и Y Combinator — соинвесторы.
* `geefc84ce` «Инвестиции Дмитрия Потапова» — получатель — ООО
  «Каркрафт» (CarCraft, платформа кредитования автодилеров), Потапов
  купил 16% как частный инвестор.
* `g06755227` «Инвестиция Игоря Рыбакова» — получатель — AMMA Pregnancy
  Tracker (pre-A раунд), Рыбаков — один из инвесторов.
* `gb441595d` «Продажа Roust Corporation» — Roust Corporation (Рустам
  Тарико) в этой сделке ПРОДАВЕЦ, а предмет продажи — его польская
  «дочка» CEDC International, купленная группой Maspex за $1 млрд.

Во всех пяти случаях `buyer`/`seller_id` сделки пусты (не заполнены
никем), и профиль ссылается ровно на ОДНУ сделку — значит, ничего не
сломается, если переименовать сам профиль в верную сторону/предмет, а
не заводить новый id и переносить `target`. Отрасль трогать не
пришлось: `ind` на самом ПРОФИЛЕ уже описывает настоящую цель (Автопром
у Arrival и CarCraft, ГМК и добыча у Earth AI — поиск месторождений,
Здравоохранение у AMMA, Пищепром и напитки у CEDC International) —
она унаследовалась от `ind` сделки, а тот уже был про правильный
предмет, ошибалось только ИМЯ профиля.

ЧТО НЕ ВХОДИТ. Шестой профиль группы, `g9f76045c` «Продажа Михаилом
Прохоровым», ссылается СРАЗУ на две несвязанные сделки (продажа доли в
Brooklyn Nets/Barclays Center Джозефу Цаю и отдельная продажа ГДР TCS
Group трастом Rigi Trust, не имеющим отношения к Прохорову) — простое
переименование тут не работает, нужен НОВЫЙ профиль хотя бы для одной
из двух сделок, а такого приёма в пайплайне ещё не было — решение
переносится в отдельный прогон.

Запуск:
    python3 pipeline/fix_investment_target_names.py            # сухой прогон
    python3 pipeline/fix_investment_target_names.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

# id -> (старое имя, новое имя, [id сделок, где профиль встречается — для проверки изоляции])
RENAMES = {
    'g04a9090b': ('Инвестиции Hyundai', 'Arrival', ['g270c77f8']),
    'gc8e3ac2b': ('Инвестиции Gagarin Capital', 'Earth AI', ['g75d3169c']),
    'geefc84ce': ('Инвестиции Дмитрия Потапова', 'CarCraft', ['gd3202391']),
    'g06755227': ('Инвестиция Игоря Рыбакова', 'AMMA Pregnancy Tracker', ['g37619a9e']),
    'gb441595d': ('Продажа Roust Corporation', 'CEDC International', ['g5bb5271b']),
}

DESCRIPTIONS = {
    'g04a9090b': 'Британский стартап-производитель электромобилей и '
                 'электрофургонов.',
    'gc8e3ac2b': 'Австралийский стартап, использует искусственный '
                 'интеллект для поиска месторождений полезных '
                 'ископаемых.',
    'geefc84ce': 'Российская платформа кредитования для автодилеров '
                 '(ООО «Каркрафт»).',
    'g06755227': 'Платформа для отслеживания беременности и здоровья '
                 'семьи AMMA Family.',
    'gb441595d': 'Польский производитель и дистрибьютор алкогольной '
                 'продукции; в 2021 году продан прежним владельцем '
                 'Roust Corporation группе Maspex.',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    companies = data['companies']
    deals = data['deals']

    for cid, (old_name, new_name, deal_ids) in RENAMES.items():
        c = companies.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert c['name'] == old_name, 'имя %s уже другое: %r' % (cid, c['name'])
        full_text_refs = sorted(d['id'] for d in deals if cid in json.dumps(d, ensure_ascii=False))
        assert full_text_refs == sorted(deal_ids), (
            'профиль %s встречается не только в учтённых сделках: %r' % (cid, full_text_refs))
        print('ПЕРЕИМЕНОВЫВАЕМ  %s: %r -> %r' % (cid, old_name, new_name))
        if write:
            c['name'] = new_name
            data['match_keys'][cid] = [new_name.lower()]

    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = companies.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  ОПИСАНИЕ  %-12s %-26s %s' % (cid, str(c.get('name'))[:26], text[:56]))
        if write:
            c['desc'] = text
        wrote += 1

    print('\nПереименовано: %d, описаний: %d' % (len(RENAMES), wrote))
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
