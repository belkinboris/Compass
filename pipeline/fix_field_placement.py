# -*- coding: utf-8 -*-
"""Бэклог A7: текст стоит не в том поле карточки.

Юрист читает подпись поля и верит ей. Если под «Формой расчётов» написано,
когда компания была основана, а под «Предметом / долей» — месячная выручка,
подпись врёт. Это не косметика: пользователь делает выводы по названию поля.

ОТКУДА ВЗЯЛОСЬ. Поля нарезались из сплошного текста по сделке, и раскладка по
смыслу местами не сработала — особенно у `eco.fin`, куда попало всё, где
встречалось слово «финансирование»: история прошлых раундов, описание бизнеса,
назначение привлечённых средств.

КАК ЧИНИМ. Только руками, таблицей — как в `fix_2026_roles.py`. Автоматическая
раскладка по смыслу здесь запрещена принципом 1: правдоподобная догадка о том,
к какому полю относится фраза, хуже пустоты. Скоринг по ключевым словам
пробовали — он метит «80% выручки» как долю в капитале и пропускает половину
настоящих случаев; он годится только чтобы сузить выборку для чтения глазами.

Действия в таблице:
  * MOVE   — перенести значение целиком в другое поле. Поле-получатель обязано
             быть пустым: затирать существующий текст нельзя, скрипт откажется.
  * APPEND — дописать к непустому полю-получателю. Так сделано там, где текст
             содержательный, а в целевом поле уже есть другие показатели.
  * REPLACE — заменить содержимое поля-получателя. Разрешено, только если то,
             что там лежит, целиком входит в переносимый текст (в поле был
             обрезанный вариант той же фразы) — иначе данные потерялись бы.
  * CLEAR  — очистить: значение дословно дублирует соседнее поле.
  * FIX    — сначала восстановить обрывок из `extra` (та же поломка, что чинил
             `fix_truncated_fields.py`, но эти три начинаются со строчной буквы
             и потому под его правила не попадали), затем перенести.

ЧТО ПРОСМОТРЕНО. Сплошь прочитаны все 67 значений `eco.fin`, 161 —
`eco.target_fin` и 295 — `eco.share` (523 поля). Найдено и исправлено 34.

Запуск:
    python3 pipeline/fix_field_placement.py            # сухой прогон
    python3 pipeline/fix_field_placement.py --write    # записать
"""
import collections
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^(?:—|-|не\s+раскры|публично\s+не|не\s+привлекал|нет\s+данных)', re.I)

# (id, откуда) -> (действие, куда, зачем)
# «куда» = None для CLEAR.
TABLE = {
    # --- eco.fin: под «Формой расчётов» лежала история и описание бизнеса ---
    ('gedfd4c1e', 'fin'): ('MOVE', 'context', 'когда и кем основана Bioniq, прошлый раунд Series B'),
    ('g28d62a47', 'fin'): ('MOVE', 'context', 'история: это был второй раунд, первый в 2017 году'),
    ('g5900b49f', 'fin'): ('MOVE', 'context', 'сколько компания привлекла за всё время'),
    ('gd3202391', 'fin'): ('MOVE', 'context', 'описание бизнеса CarCraft, а не расчёты по сделке'),
    ('g62e5dc3e', 'fin'): ('MOVE', 'context', 'суммарные привлечения по PitchBook и прочие инвесторы'),
    ('g8aeb631a', 'fin'): ('MOVE', 'context', 'предыдущий раунд стартапа'),
    ('g74932d41', 'fin'): ('MOVE', 'context', 'предыстория партнёрства ВТБ и «Делимобиля»'),
    ('ge35e2eb2', 'fin'): ('MOVE', 'context', 'что было с компанией после сделки'),
    ('g259866c4', 'fin'): ('MOVE', 'context', 'первая попытка продажи в 2018 году'),
    ('g09d132ef', 'fin'): ('MOVE', 'context', 'состав участников раунда и прошлые инвесторы'),
    ('g7623613c', 'fin'): ('MOVE', 'context', 'сколько компания получила до раунда'),
    ('g774d8b6d', 'fin'): ('MOVE', 'context', 'оценка Счётной палаты, а не форма расчётов'),
    ('g58a1ac17', 'fin'): ('MOVE', 'context', 'совокупный объём привлечений за всё время'),
    ('g66cb145a', 'fin'): ('MOVE', 'context', 'пересказ сделки и сроки закрытия'),
    ('g92c6a8ce', 'fin'): ('MOVE', 'target_fin', 'список клиентов — это показатель актива'),
    ('g34d8c65b', 'fin'): ('MOVE', 'rationale', 'зачем проводили SPO — это цель, а не расчёты'),
    ('gb2ab7521', 'fin'): ('MOVE', 'rationale', 'почему доля размылась — причина сделки'),
    ('g96e561ef', 'fin'): ('MOVE', 'rationale', 'на что пойдут привлечённые средства'),
    ('gc9a96521', 'fin'): ('MOVE', 'rationale', 'на что пойдут привлечённые средства'),
    ('g9180c0a6', 'fin'): ('MOVE', 'rationale', 'на что предназначались средства'),

    # --- eco.target_fin: под «Показателями таргета» лежала цена и оценка ---
    ('gdde6bef5', 'target_fin'): ('MOVE', 'val', 'капитализация объединяемых игроков — это оценка'),
    ('g9c4b80a7', 'target_fin'): ('MOVE', 'val', 'оценка бизнеса EV по расчётам инвестбанкира'),
    ('gc6448a17', 'target_fin'): ('MOVE', 'val', 'цена ниже капитала и мультипликатор P/BV — оценка'),
    ('g6f83d85e', 'target_fin'): ('MOVE', 'val', 'мультипликатор и вытекающая оценка $4–8 млрд'),
    ('gc3d735fc', 'target_fin'): ('MOVE', 'val', 'P/BV сделки в сравнении с рынком — оценка'),
    ('ge8f45161', 'target_fin'): ('MOVE', 'val', 'как рассчитана цена пакета — оценка'),
    # Долговая нагрузка покупателя — не показатель таргета. В «Контексте» уже
    # есть про рейтинг того же покупателя, так что дописываем туда, а не переносим.
    ('ga46c5b15', 'target_fin'): ('APPEND', 'context', 'долг покупателя (АФК «Система»), а не таргета'),
    ('ga7a0b957', 'target_fin'): ('FIX', 'val', 'обрывок «(мультипликатор P/equity implied)»; '
                                                'восстановленная фраза — про оценку'),

    # --- eco.share: под «Предметом / долей» лежали показатели и расчёты ---
    ('g64a94e27', 'share'): ('MOVE', 'fin', 'погашение через выкуп еврооблигаций — форма расчётов'),
    # В «Показателях таргета» лежала обрезанная версия той же фразы («…10–15 млн
    # руб.»), а полная («…, а 80%+ выручки обеспечивал Delivery Club») — в
    # «Предмете / доле». Переносим полную поверх обрезанной: короткая целиком
    # входит в длинную, поэтому ничего не теряется.
    ('gded6fbba', 'share'): ('REPLACE', 'target_fin', 'показатели проекта; в целевом поле лежал '
                                                      'обрезанный вариант той же фразы'),
    ('ge85383b6', 'share'): ('CLEAR', None, 'дословно дублирует «Показатели таргета»'),
    ('g03eb22ba', 'share'): ('APPEND', 'target_fin', 'число исполнителей и клиентов — показатели; '
                                                     'в целевом поле уже есть выручка, дописываем'),
    ('ga845fb01', 'share'): ('FIX', 'context', 'обрывок «у ООО «Донк»…»; восстановленная фраза — '
                                               'история объекта и результаты управления'),
    ('g09d132ef', 'share'): ('FIX', 'target_fin', 'обрывок «работодателей…»; восстановленная фраза — '
                                                  'показатели платформы'),
}


def norm(s):
    return re.sub(r'\s+', ' ', s or '').strip()


def split_sentences(t):
    """Тот же разделитель, что в fix_truncated_fields.py: точка + заглавная."""
    parts = re.split(r'(?<=[.!?])\s+', t)
    out = []
    for p in parts:
        if out and not re.match(r'^[«"(]?[А-ЯЁA-Z]', p):
            out[-1] += ' ' + p
            continue
        out.append(p)
    return out


def recover(extra, frag):
    pos = extra.find(frag)
    if pos < 0:
        return None
    acc, got = 0, []
    for s in split_sentences(extra):
        start, end = acc, acc + len(s)
        if start <= pos < end or (pos < start and start < pos + len(frag)):
            got.append(s)
        acc = end + 1
    rec = ' '.join(got)
    return rec if rec and frag in rec else None


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by = {d['id']: d for d in data['deals']}

    planned, errors, skipped = [], [], []

    for (did, src), (action, dst, why) in TABLE.items():
        deal = by.get(did)
        if deal is None:
            errors.append(f'{did}: сделка не найдена')
            continue
        eco = deal.get('eco') or {}
        value = norm(eco.get(src))
        if not value or PLACEHOLDER.match(value):
            skipped.append(f'{did}/eco.{src}: поле уже пустое — правка, видимо, применена')
            continue

        if action == 'FIX':
            rec = recover(norm(deal.get('extra')), value)
            if rec is None:
                errors.append(f'{did}/eco.{src}: обрывок не найден в extra, восстанавливать не из чего')
                continue
            value = rec

        if action == 'CLEAR':
            # Очищаем только дубли. Проверяем явно: тот же текст должен лежать в
            # другом поле карточки. Иначе «очистка дубля» тихо съест данные —
            # ровно так однажды пропала сумма сделки (см. журнал, прогон 5).
            twin = [k for k, v in eco.items()
                    if k != src and isinstance(v, str) and value in norm(v)]
            if not twin:
                errors.append(f'{did}/eco.{src}: текста нет ни в одном другом поле — это не дубль')
                continue
            planned.append((did, src, None, value, None, why + f' (дубль в eco.{twin[0]})'))
            continue

        target = norm(eco.get(dst))
        if action == 'MOVE' and target and not PLACEHOLDER.match(target):
            errors.append(f'{did}: eco.{dst} занято, перенос затёр бы текст — {target[:60]!r}')
            continue
        if action == 'APPEND' and (not target or PLACEHOLDER.match(target)):
            errors.append(f'{did}: eco.{dst} пусто, APPEND не нужен — это MOVE')
            continue
        if action == 'REPLACE' and target not in value:
            errors.append(f'{did}: eco.{dst} не входит в переносимый текст, REPLACE потерял бы '
                          f'данные — {target[:60]!r}')
            continue
        new = (target + ' ' + value).strip() if action == 'APPEND' else value
        planned.append((did, src, dst, value, new, why))

    if errors:
        print('ОШИБКИ (записывать нельзя):')
        for e in errors:
            print('  ' + e)
        print()
    if skipped:
        print(f'пропущено (уже применено): {len(skipped)}')
        for s in skipped:
            print('  ' + s)
        print()

    kinds = collections.Counter(('очистка' if dst is None else f'-> eco.{dst}')
                                for _, _, dst, _, _, _ in planned)
    print(f'полей к переносу: {len(planned)}  {dict(kinds)}\n')
    for did, src, dst, value, new, why in planned:
        print(f'### {did}: eco.{src} -> {"(очистить)" if dst is None else "eco." + dst}')
        print(f'    почему: {why}')
        print(f'    текст:  {value[:150]}')
        if new and new != value:
            print(f'    итог в поле-получателе: {new[:150]}')

    if write:
        if errors:
            print('\nЕсть ошибки — запись отменена.')
            return 1
        for did, src, dst, _, new, _ in planned:
            eco = by[did]['eco']
            if dst is not None:
                eco[dst] = new
            eco[src] = '—'
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
