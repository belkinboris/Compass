# -*- coding: utf-8 -*-
"""Бэклог A6: значения полей карточки обрезаны на середине предложения.

На экране это видно сразу: «Показатели таргета» начинается с закрывающей
скобки — «); мультипликатор P/BV составил около 0,74x.» — а «Предмет / доля»
обрывается на «…по данным СМИ (январь 2022 г.» с незакрытой скобкой.

ОТКУДА ЭТО ВЗЯЛОСЬ. Значения полей нарезаны из `extra` (полного текста по
сделке), и резали их по правилу «точка + пробел = конец предложения». В
русском деловом тексте это правило ломается на сокращениях: «18,8 млрд руб.»,
«январь 2022 г.», «Калужская обл.», «Fortum Russia B.V.», «ВЭБ.РФ». Разрез
проходил внутри предложения, и половина фразы уезжала в соседнее поле или
пропадала совсем.

КАК ЧИНИМ. Полный текст никуда не делся — он лежит в `extra`. Находим обрывок
в `extra` и возвращаем предложение целиком. Ничего не досочиняем: восстановленный
текст дословно взят из того же поля `extra` этой же карточки.

ЧТО СЧИТАЕМ ПРИЗНАКОМ ОБРЫВА (только явные, без догадок):
  * значение начинается с закрывающего знака — `)`, `»`, `,`, `;`, `:`;
  * в значении больше открывающих скобок или кавычек, чем закрывающих.
Оба признака проверяются вместе с обязательным условием: обрывок должен
дословно найтись внутри более длинного предложения в `extra`. Если не нашёлся —
поле не трогаем и показываем в отчёте.

ЧЕГО ЗДЕСЬ НАМЕРЕННО НЕТ. Не чиним «поле начинается со строчной буквы»: таких
около 95, и добрая половина законна («разрешение ФАС получено до закрытия»).
Не переносим текст между полями: если восстановленное предложение по смыслу
ближе к другому полю, это отдельная задача — здесь только целостность текста.

Запуск:
    python3 pipeline/fix_truncated_fields.py            # сухой прогон
    python3 pipeline/fix_truncated_fields.py --write    # записать
"""
import collections
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

FIELDS = ('eco', 'law')
HEAD_CUT = re.compile(r'^\s*[)»,;:.]')
PLACEHOLDER = re.compile(r'^(?:—|-|не\s+раскры|публично\s+не|не\s+привлекал)', re.I)

# Ручные решения по двум карточкам, где механическое восстановление даёт
# формально верный, но негодный результат. Значение None = очистить поле.
OVERRIDE = {
    # «Форма расчётов»: предложение начинается с рыночного позиционирования
    # («Приобретение позволило «Максидому» войти в тройку лидеров…»), к форме
    # расчётов относится только хвост. Голова и так есть в «Дополнительной
    # информации», дублировать её под чужим заголовком незачем.
    ('gc5f9c1d9', 'eco', 'fin'):
        'Финансирование сделки осуществлялось в равных долях из собственных '
        'и заёмных средств покупателя.',
    # Один и тот же обрывок лежал сразу в двух полях. Предложение про закупку
    # устройств и долю курьерского направления в выручке — это показатели, а не
    # предмет сделки; доля в раунде не раскрывалась, поэтому «Предмет / доля»
    # честнее оставить пустым, чем продублировать в нём соседнее поле.
    ('g7533d350', 'eco', 'share'): None,
}


def norm(s):
    return re.sub(r'\s+', ' ', s or '').strip()


def split_sentences(t):
    """Границей считаем точку с пробелом ПЕРЕД заглавной буквой.

    Список сокращений намеренно не ведём: именно попытка отличить «руб.» от
    конца предложения и породила этот дефект. Правило «дальше заглавная»
    ошибается реже и в безопасную сторону — максимум склеит два предложения,
    а не разрежет одно.
    """
    parts = re.split(r'(?<=[.!?])\s+', t)
    out = []
    for p in parts:
        if out and not re.match(r'^[«"(]?[А-ЯЁA-Z]', p):
            out[-1] += ' ' + p
            continue
        out.append(p)
    return out


NESTED_QUOTES = re.compile(r'«[^»]*«')
LATIN_ABBR_END = re.compile(r'\b[A-Za-z]\.[A-Za-z]\.$')


def unbalanced(s):
    if s.count('(') - s.count(')') > 0:
        return True
    # Перекос по кавычкам считаем обрывом, только если нет вложенной кавычки:
    # «АО «Завод «Электропульт»» — это типографская особенность записи названий,
    # а не обрезанный текст. Без этой оговорки в «обрывы» попадали 27 совершенно
    # целых «Целей сделки».
    return s.count('«') - s.count('»') > 0 and not NESTED_QUOTES.search(s)


def looks_cut(s):
    return bool(HEAD_CUT.match(s)) or unbalanced(s)


def recover(extra, frag):
    """Предложение(я) из extra, целиком покрывающие обрывок; иначе None."""
    pos = extra.find(frag)
    if pos < 0:
        return None
    sents = split_sentences(extra)
    acc, got, tail = 0, [], []
    for s in sents:
        start, end = acc, acc + len(s)
        if start <= pos < end or (pos < start and start < pos + len(frag)):
            got.append(s)
        elif got:
            tail.append(s)
        acc = end + 1
    rec = ' '.join(got)
    # Правило «дальше заглавная» иногда всё же режет предложение: «Sberbank BH
    # d.d. Sarajevo» и «AIK Banka a.d. Beograd» выглядят как конец фразы.
    # Дотягиваем следующими предложениями, пока видим явный признак разреза:
    # незакрытую скобку или обрыв на латинской аббревиатуре организационной
    # формы («a.d.», «d.d.», «B.V.»), которой предложение кончаться не может.
    # Предел в 8 предложений — страховка от разрастания: цикл и так
    # останавливается, как только текст перестаёт выглядеть обрезанным.
    # Русское «руб.» сюда намеренно не включено: им предложение кончается
    # сплошь и рядом, и по нему мы бы приклеивали лишнее.
    for s in tail[:8]:
        if not unbalanced(rec) and not LATIN_ABBR_END.search(rec):
            break
        rec += ' ' + s
    return rec if rec and frag in rec and rec != frag else None


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    fixed = collections.Counter()
    skipped = collections.Counter()
    changes, misses = [], []

    for d in data['deals']:
        extra = norm(d.get('extra'))
        for grp in FIELDS:
            block = d.get(grp) or {}
            for key, val in list(block.items()):
                if not isinstance(val, str):
                    continue
                cur = norm(val)
                if not cur or PLACEHOLDER.match(cur):
                    continue
                ov = OVERRIDE.get((d['id'], grp, key), False)
                if ov is not False and cur != norm(ov):
                    changes.append((d['id'], f'{grp}.{key}', cur, ov, 'ручное решение'))
                    fixed['ручное решение'] += 1
                    if write:
                        block[key] = '—' if ov is None else ov
                    continue
                if not looks_cut(cur):
                    continue
                rec = recover(extra, cur)
                if rec is None:
                    skipped[f'{grp}.{key}'] += 1
                    misses.append((d['id'], f'{grp}.{key}', cur))
                    continue
                changes.append((d['id'], f'{grp}.{key}', cur, rec, 'восстановлено из extra'))
                fixed[f'{grp}.{key}'] += 1
                if write:
                    block[key] = rec

    print('ВОССТАНОВЛЕНО ПО ПОЛЯМ:')
    for k, n in fixed.most_common():
        print(f'  {n:4}  {k}')
    print(f'\nвсего изменится: {len(changes)}')
    if skipped:
        print('\nНЕ НАЙДЕНО в extra (поле не тронуто):')
        for k, n in skipped.most_common():
            print(f'  {n:4}  {k}')

    still = sum(1 for _, _, _, new, _ in changes if new and looks_cut(norm(new)))
    print(f'осталось с признаком обрыва после правки: {still}')

    print('\nПРИМЕРЫ:')
    for did, field, old, new, why in changes[:6]:
        print(f'  {did} [{field}] — {why}')
        print(f'    было:  {old[:130]}')
        print(f'    стало: {"(поле очищено)" if new is None else new[:130]}')
    if misses:
        print('\nНЕ ВОССТАНОВЛЕНЫ (первые 8):')
        for did, field, cur in misses[:8]:
            print(f'  {did} [{field}]: {cur[:110]}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
