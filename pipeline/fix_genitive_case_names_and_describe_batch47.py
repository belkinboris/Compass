# -*- coding: utf-8 -*-
"""Сорок седьмая партия: три исправления имени + 10 описаний.

НАЙДЕНО (при чтении G2-кандидатов, карточки старее casing.py — до
августа 2026 падеж предмета вырезался из заголовка механически, без
согласования):

  - `g3d8ab9a6` «Стройпроектхолдинга» — родительный падеж, вырезан из
    «Создание СП ВЭБ.РФ и «Стройпроектхолдинга» Аркадия Ротенберга»
    (конструкция «СП X и Y» требует родительного). Именительный —
    «Стройпроектхолдинг». Отдельного профиля с верным именем в базе нет.
  - `g18fbb5a7` «Юлмарта» — родительный падеж, вырезан из «логистического
    центра «Юлмарта»» (конструкция «центр кого/чего»). Именительный —
    «Юлмарт».
  - `gafecb5bb` «GAMES Venture Capital» — обрезано начало имени:
    источник называет инвестора «MY.GAMES Venture Capital (MGVC)» —
    инвестиционное подразделение MY.GAMES (Mail.ru Group), отдельное от
    уже существующего в базе профиля самой MY.Games (`g7814a42a`) —
    держится отдельным профилем, а не сливается с материнской
    компанией, по той же логике, что «Структуры Игоря Кима» отдельно от
    личных профилей.

Правки — переименование на месте (тот же id, та же единственная
сделка): падеж проверен вручную по управляющей конструкции в исходном
тексте, не пропущен через pymorphy.

Плюс 10 описаний обычным G2-кандидатам.

Запуск:
    python3 pipeline/fix_genitive_case_names_and_describe_batch47.py            # сухой прогон
    python3 pipeline/fix_genitive_case_names_and_describe_batch47.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

RENAMES = {
    'g3d8ab9a6': ('Стройпроектхолдинга', 'Стройпроектхолдинг'),
    'g18fbb5a7': ('Юлмарта', 'Юлмарт'),
    'gafecb5bb': ('GAMES Venture Capital', 'MY.GAMES Venture Capital (MGVC)'),
}
NEW_ALIASES = {
    'g3d8ab9a6': ['стройпроектхолдинг'],
    'g18fbb5a7': ['юлмарт'],
    'gafecb5bb': ['my.games venture capital', 'mgvc'],
}

DESCRIPTIONS = {
    'g33023870': 'Итальянский бизнесмен, конечный бенефициар '
                 '«Делимобиля»; в 2026 году нарастил косвенную долю с '
                 '53,25% до 66,15%.',
    'gafecb5bb': 'Инвестиционное подразделение MY.GAMES (Mail.ru '
                 'Group); в 2021 году вложило €3,5 млн в испанского '
                 'разработчика игр The Breach Studios.',
    'gd09cfeb0': 'В 2023 году купила на банкротных торгах '
                 'производственный комплекс Энгельсского локомотивного '
                 'завода.',
    'ga89f1b20': 'Агрегатор доставки Metaship и онлайн-эквайринг; в '
                 '2021 году привлекла 100 млн ₽ от предпринимателя '
                 'Дмитрия Зобнина при оценке около 2 млрд ₽.',
    'g3d8ab9a6': 'Строительная структура Аркадия Ротенберга; в 2020 '
                 'году вместе с ВЭБ.РФ создала СП «Нацпроектстрой».',
    'g893ef7bc': 'Санаторий в Анапе; признан банкротом в 2016 году, '
                 'имущественный комплекс продан на торгах в 2020 году.',
    'g18fbb5a7': 'Российский маркетплейс электроники; в 2020 году '
                 'продал логистический центр на Пулковском шоссе в '
                 'Петербурге компании «Ситилинк».',
    'g780fdf13': 'Американский InsurTech-стартап, основан в 2015 году; '
                 'в 2020 году долю Fort Ross Ventures выкупила '
                 'страховая платформа Aon за $6,5 млн.',
    'g0644ef60': 'Завод упаковки из гофрокартона в Лебедяни (Липецкая '
                 'обл.); в 2022 году вместе с двумя другими заводами '
                 'Mondi продан группе «Готэк».',
    'gdc33d226': 'Финтех-сервис приёма платежей (ранее — выплаты '
                 'самозанятым); в 2022 году привлёк 23,4 млн ₽ при '
                 'оценке 180 млн ₽.',
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
