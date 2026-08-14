# -*- coding: utf-8 -*-
"""Сорок девятая партия: неясное имя предмета (Dating) + 10 описаний.

НАЙДЕНО. Профиль `g57829887` «Dating» — предмет сделки ge13d1b5c
(SDVentures продала интеллектуальную собственность Dating.com и ряда
дейтинг-сервисов компании SOL Holdings). Голое «Dating» не поясняет, что
это портфель ИС (патенты, ПО, домены), а не отдельная компания или
сайт — родня уже чинившихся «Арктическое» (батч 45) и «Series C»/«Раунд
A» (батчи 45–46): короткое неполное имя вместо описательного. Правка —
переименование на месте (тот же id, та же единственная сделка), не
смена личности.

Плюс 10 описаний обычным G2-кандидатам.

Запуск:
    python3 pipeline/fix_dating_name_and_describe_batch49.py            # сухой прогон
    python3 pipeline/fix_dating_name_and_describe_batch49.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

RENAMES = {
    'g57829887': ('Dating', 'Dating.com (портфель дейтинг-сервисов)'),
}
NEW_ALIASES = {
    'g57829887': ['dating.com', 'dating'],
}

DESCRIPTIONS = {
    'ga45658d3': 'Структура инвесткомпании Marathon Group Александра '
                 'Винокурова; в 2020 году купила 0,53% акций «Магнита» '
                 'за 2 млрд ₽.',
    'g52d39629': 'Инвестфонд; в 2021 году купил у Елены Батуриной '
                 'дублинский отель Morrison Hotel (бренд DoubleTree '
                 'by Hilton).',
    'g23a1df20': 'В 2026 году купила на торгах складской портфель '
                 'Raven Russia (17 юрлиц, ~2 млн кв. м) за 47,2 '
                 'млрд ₽.',
    'g57829887': 'Портфель прав на Dating.com и другие дейтинг-сервисы; '
                 'в 2019 году продан SOL Holdings за $215 млн и долю в '
                 'Dating.com Group.',
    'gaee91d03': 'Сервис доставки еды формата dark kitchen, основан в '
                 '2018 году; в 2019 году привлёк первый раунд от '
                 'Владимира Христенко и партнёров.',
    'gba35c8d8': 'Бизнес-центр «Легион II»; в 2023 году продан Siemens '
                 'инвесткомпании «Инсайт» за 7–10 млрд ₽ (оценка).',
    'g68e4f1b0': 'Долгосрочная аренда Дома Зингера на Невском проспекте '
                 'в Петербурге; в 2023 году куплена VK у структур '
                 'Альфа-Банка за 2,5 млрд ₽.',
    'g9cbd046c': 'В 2023 году купила четыре российских завода Magna '
                 'International (интерьерные компоненты для авто).',
    'gd096d9d8': 'Холдинг, владевший казахстанскими активами Beeline '
                 '(«КаР-Тел», «КазЕвроМобайл»); в 2022 году «Вымпелком» '
                 'продал 75% акций VEON за 54 млрд ₽.',
    'g14db9bb2': 'Российский бизнес Henkel; в 2023 году продан '
                 'консорциуму Augment Investments, Kismet Capital '
                 'Group и Elbrus Services.',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    mk = data['match_keys']

    for cid, (old, new) in RENAMES.items():
        assert comps[cid]['name'] == old, 'профиль %s уже переименован' % cid
        existing_names = {c.get('name') for c in comps.values()}
        assert new not in existing_names, 'имя %r уже занято' % new
        print('ПЕРЕИМЕНОВАНИЕ  %-12s %r -> %r' % (cid, old, new))
        if write:
            comps[cid]['name'] = new
            mk[cid] = NEW_ALIASES[cid]

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
        print('  ОПИСАНИЕ %-12s %-40s %s' % (cid, str(c.get('name'))[:40], text[:50]))
        if write:
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
