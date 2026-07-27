# -*- coding: utf-8 -*-
"""Бэклог A9: к тексту карточки приклеена подпись стороны.

«Цель сделки» начиналась так: «ГК «Черноголовка» (Алексей Четвергов) —
Структуры ГК «Черноголовка» приобрели 100% долей ООО «Беркана»…». Первая
половина — не предложение, а подпись, оставшаяся от прежнего формата данных.
Сторона и так показана в шапке карточки, поэтому подпись только удлиняет фразу
и заставляет читать одно и то же дважды.

ГЛАВНАЯ ТРУДНОСТЬ — отличить подпись от тире как знака препинания. «Продавец —
«Фаберлик» (производитель парфюмерии)» выглядит так же, но это нормальная
русская конструкция, и трогать её нельзя. Признак, который их разделяет:
после тире начинается САМОСТОЯТЕЛЬНОЕ предложение о сделке («Сделка по
приобретению…», «Структуры ГК… приобрели…», «Арбитражный суд… наложил…»), а не
раскрытие того, что стоит перед тире. Отдельно ловим дословный повтор:
«"Росхим" — "Росхим" приобрел 57,43% акций…».

Проверено на всех 90 местах, где поле начинается с «<что-то> — <Заглавная>»:
правило срабатывает на 40 и молчит на 50, и все 50 — действительно тире как
знак препинания.

СТРАХОВКА ОТ ПОТЕРИ ДАННЫХ. Подпись срезается, только если каждое название из
неё остаётся видно пользователю: либо дальше в тексте, либо в сторонах сделки
(покупатель / продавец / предмет). Иначе скрипт откажется и покажет карточку в
отчёте — единственное упоминание стороны потерять нельзя.

Запуск:
    python3 pipeline/strip_party_label.py            # сухой прогон
    python3 pipeline/strip_party_label.py --write    # записать
"""
import collections
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

PLACEHOLDER = re.compile(r'^(?:—|-|не\s+раскры|публично\s+не|не\s+привлекал|нет\s+данных)', re.I)

# «<подпись> — <Заглавная буква>» в самом начале поля. Заглавная проверяется
# без игнорирования регистра: под re.I класс [А-ЯЁ] совпадает и со строчными.
PREFIX = re.compile(r'^([^.!?]{1,80}?)\s+—\s+(?=(?-i:[А-ЯЁA-Z«]))')

# Слова, с которых начинается самостоятельное предложение о сделке. Список
# закрытый и собран по факту: угадывать «это новое предложение» по части речи
# опаснее, чем перечислить то, что реально встретилось в базе.
RESTART = re.compile(
    r'^(?:Сделка|Статья|Информация|Информационное|Публикация|Сообщение|Структуры|'
    r'Банк\s|Арбитражный|Привлечение|Продажа|Приобретение|Выставление|Закрытие|'
    r'Завершение|Переговоры|Планируемое|Решение|Выкуп)\b')

# Разобранные руками случаи, под правило не подходящие.
# Значение — либо строка-подпись, которую надо срезать, либо пара
# (подпись, чем заменить), когда в подписи есть факт, которого больше нигде нет.
MANUAL = {
    # «Консультант сделки — IBC Real Estate консультировала по сделке…»: после
    # тире не слово из списка, но подлежащее у фразы своё, и подпись ломает
    # согласование. Консультанты у карточки есть в своём поле.
    ('gd75ae46f', 'rationale'): 'Консультант сделки — ',
    ('gd75ae46f', 'extra'): 'Консультант сделки — ',
    # Двойная подпись: «ООО «Формат Инвест» (российский менеджмент); продавец —
    # Faurecia (дочерняя компания PSA Peugeot Citroën) — Сделка по выкупу…».
    # Правило видит только первое тире и до «Сделка» не добирается.
    # Здесь подпись не просто дублирует шапку: принадлежность Faurecia концерну
    # PSA Peugeot Citroën больше нигде в карточке не сказана. Поэтому не срезаем,
    # а переносим этот факт в конец нормальной фразой.
    ('g282be68a', 'rationale'): (
        'ООО «Формат Инвест» (российский менеджмент); продавец — '
        'Faurecia (дочерняя компания PSA Peugeot Citroën) — ',
        'Продавец — Faurecia (дочерняя компания PSA Peugeot Citroën). '),
    ('g282be68a', 'extra'): (
        'ООО «Формат Инвест» (российский менеджмент); продавец — '
        'Faurecia (дочерняя компания PSA Peugeot Citroën) — ',
        'Продавец — Faurecia (дочерняя компания PSA Peugeot Citroën). '),
}

FIELDS = (
    ('rationale', lambda d: (d.get('eco') or {}).get('rationale') or '',
     lambda d, v: d['eco'].__setitem__('rationale', v)),
    ('context', lambda d: (d.get('eco') or {}).get('context') or '',
     lambda d, v: d['eco'].__setitem__('context', v)),
    ('extra', lambda d: d.get('extra') or '', lambda d, v: d.__setitem__('extra', v)),
)


def norm(s):
    return re.sub(r'\s+', ' ', s or '').strip()


def names(text):
    """Названия из подписи: в кавычках и латиницей с заглавной."""
    out = set(re.findall(r'«([^»]{3,})»', text))
    # Диапазон латиницы с диакритикой: без него «Citroën» резалось на «Citro»,
    # и страховка ругалась на название, которого в тексте и не было.
    out |= set(re.findall(r'\b([A-Z][A-Za-zÀ-ÿ]{3,}(?:\s+[A-Z][A-Za-zÀ-ÿ]{2,})*)', text))
    return out


def key(name):
    """Название без кавычек и организационной формы — для сверки «то же лицо».

    Без нормализации подпись «ООО «Группа Рексофт»» не узнавалась в покупателе
    «Рексофт», и страховка блокировала правку там, где терять было нечего.
    """
    s = re.sub(r'[«»"\']', ' ', (name or '').lower())
    s = re.sub(r'\b(?:ооо|оао|зао|пао|ао|гк|ук|нк|мкоо|группа|холдинг|компания)\b', ' ', s)
    return re.sub(r'[^\w]+', '', s)


def party_names(deal, comps):
    """Названия сторон сделки — они видны в шапке карточки."""
    out = set()
    for key in ('buyer', 'target', 'seller_id', 'asset_id'):
        cid = deal.get(key)
        if cid and cid in comps:
            out.add(comps[cid].get('name') or '')
    if deal.get('seller'):
        out.add(deal['seller'])
    out.add(deal.get('title') or '')
    return {n for n in out if n}


def label_is_safe(label, rest, deal, comps):
    """Каждое название из подписи должно остаться видно пользователю."""
    visible = key(rest + ' ' + ' '.join(party_names(deal, comps)))
    missing = [n for n in names(label) if key(n) and key(n) not in visible]
    return not missing, missing


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    comps = data['companies']

    planned, blocked = [], []
    stats = collections.Counter()

    for deal in data['deals']:
        for field, get, set_ in FIELDS:
            value = norm(get(deal))
            if not value or PLACEHOLDER.match(value):
                continue

            manual = MANUAL.get((deal['id'], field))
            head = ''
            if isinstance(manual, tuple):
                manual, head = manual
            if manual and value.startswith(manual):
                label = manual.rstrip(' —')
                rest = head + value[len(manual):]
                why = 'разобрано вручную'
            else:
                m = PREFIX.match(value)
                if not m:
                    continue
                label, rest = m.group(1), value[m.end():]
                repeat = any(rest.startswith('«' + n + '»') for n in names(label))
                if RESTART.match(rest):
                    why = 'после тире начинается новое предложение'
                elif repeat:
                    why = 'подпись дословно повторяется в тексте'
                else:
                    stats['оставлено (тире как знак препинания)'] += 1
                    continue

            ok, missing = label_is_safe(label, rest, deal, comps)
            if not ok:
                blocked.append((deal['id'], field, label, missing))
                stats['не тронуто (название есть только в подписи)'] += 1
                continue
            planned.append((deal['id'], field, label, rest, why, set_))
            stats[f'{field}: подпись срезана'] += 1

    print('РЕЗУЛЬТАТ:')
    for k, n in stats.most_common():
        print(f'  {n:4}  {k}')
    print(f'\nполей к правке: {len(planned)}')
    if blocked:
        print('\nНЕ ТРОНУТО — единственное упоминание стороны:')
        for did, field, label, missing in blocked:
            print(f'  {did} [{field}]: {label[:60]!r} — не найдено дальше: {missing}')
    print()
    seen = set()
    for did, field, label, rest, why, _ in planned:
        if did in seen:
            continue
        seen.add(did)
        print(f'### {did} [{field}] — {why}')
        print(f'    срезано: {label[:70]!r}')
        print(f'    осталось: {rest[:120]}')

    if write:
        by = {d['id']: d for d in data['deals']}
        for did, _, _, rest, _, set_ in planned:
            set_(by[did], rest)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
