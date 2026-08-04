# -*- coding: utf-8 -*-
"""Скудные карточки: разложить «Дополнительную информацию» по своим полям.

ЗАЧЕМ. У 112 карточек нет ни объекта `eco`, ни `law` — на экране это «мало
данных» и один абзац текста. Но факты в них ЕСТЬ, просто лежат не в своём
поле: «Выручка 2021 — 41,8 млрд ₽, чистый убыток — 2,5 млрд ₽» — это
«Финансы предмета», «100% ООО «Гринхаус», томатный комплекс 24,5 га» — это
«Предмет / доля», «Причина продажи — вывод медицинского направления из-под
санкций» — это «Цель сделки». Ровно тот же класс, что уже записан в
CLAUDE.md про карточку «Яндекс»/SolidSoft, где вторая фирма пряталась в
пояснении к первой.

ГРАНИЦА, КОТОРАЯ ЗДЕСЬ ГЛАВНАЯ. Ничего не сочиняется и не переформулируется:
в поле кладётся ДОСЛОВНОЕ предложение из `extra` той же карточки. Проверка —
`assert`, что нормализованный результат является подстрокой нормализованного
исходного текста. Любая попытка «слегка причесать» уронит скрипт.

ПОЧЕМУ ТЕКСТ НЕ БУДЕТ ПОКАЗАН ДВАЖДЫ. `extraHtml()` в интерфейсе отбрасывает
из «Дополнительной информации» предложения, которые дословно повторяют
подписанные поля карточки (доля общих слов плюс абсолютный минимум в три
общих слова). Поэтому перенос не создаёт «один и тот же абзац на двух
подписях» — он именно переносит.

ПОЧЕМУ `eco` И `law` СОЗДАЮТСЯ ЦЕЛИКОМ, А НЕ ЧАСТИЧНО. Интерфейс во многих
местах читает `d.eco.rationale` и `d.law.adv` без проверки на существование
объекта (урок E9 и падение, найденное Playwright на «Обзоре»). Карточка с
половинным `eco` — та же мина, что карточка без него.

СУММА — САМОЕ РИСКОВАННОЕ ПОЛЕ. Берётся только из явной пометки «Сумма: …»,
которую поставил компактный импорт для ЭТОЙ карточки, а не первое число из
текста: число рядом сплошь и рядом относится к другой сделке или к выручке
(урок про «ВТБ продал Holiday Inn»). Если в пометке стоит слово «оценка» или
«эксперты», значение идёт в «Оценку», а не в «Сумму».

Запуск:
    python3 pipeline/split_extra_into_fields.py            # сухой прогон
    python3 pipeline/split_extra_into_fields.py --write    # записать
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

EMPTY_ECO = {'sum': '—', 'share': '—', 'val': '—', 'target_fin': '—',
             'fin': '—', 'rationale': '—', 'context': '—', 'finadv': '—'}
EMPTY_LAW = {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'}

# Точка не значит конец предложения («41,8 млрд руб.», «ООО «Ромашка» и др.»):
# режем только по «точка + пробел + заглавная» — ошибается в безопасную
# сторону, склеивая два предложения вместо того чтобы разрезать одно.
SENTENCE = re.compile(r'(?<=[.!?])\s+(?=(?-i:[А-ЯЁA-Z0-9]))')

# Хвост компактного импорта: «(Иванов (продавец))» — это разметка, а не текст.
ROLE_TAIL = re.compile(r'\s*\([^()]{2,90}\((?:продав|покупат|инвестор|владел|получат)[^)]*\)\)\s*$', re.I)

SUM_MARK = re.compile(r'Сумма:\s*([^.]{2,80}?)\s*(?:\.|$)', re.I)

# «Продавец — Аркадий Абрамович.» — это ПОДПИСЬ стороны, а не предложение о
# сделке. Различает их то, что стоит ПОСЛЕ тире (урок из CLAUDE.md): здесь
# требуется короткое имя без глагола сделки, иначе «Покупатель — Сделка по
# приобретению ЦОД…» уехало бы в поле стороны. Всё предложение целиком, а не
# кусок из середины: имя из середины фразы вырывать нельзя.
PARTY_LINE = re.compile(
    r'^(Продавец|Покупатель|Инвестор)\s*[—–-]\s*([^.;]{2,70})\.?$', re.I)
DEAL_VERB = re.compile(r'приобре|покупа|продаёт|продает|купил|сделк|инвестир', re.I)
ESTIMATE = re.compile(r'оцен|эксперт|по\s+данным|источник', re.I)

# Признаки полей. Проверяются по порядку: первое совпадение решает.
RULES = [
    ('target_fin', re.compile(
        r'\b(?:выручка|EBITDA|чист\w+\s+(?:прибыл|убыт)|активы\s+на|капитал\w*\s+на)\b', re.I)),
    ('val', re.compile(r'\bоцен(?:ива|ка|ку|ки)\w*\b', re.I)),
    ('rationale', re.compile(
        r'\b(?:причина|цель|чтобы|для\s+(?:вывод|развит|расширен|укреплен)|направлен\w*\s+на)\b', re.I)),
    ('share', re.compile(r'\b\d{1,3}(?:[,.]\d+)?\s*%|\bдол(?:ю|и|ей)\b|\bпакет\b', re.I)),
]


def normalize(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip()


def sentences(text):
    body = ROLE_TAIL.sub('', normalize(text))
    return [s.strip() for s in SENTENCE.split(body) if s.strip()]


def classify(deal):
    """(что писать в eco, что писать в sum) для одной карточки."""
    # Сравниваем с текстом БЕЗ хвоста разметки: сам хвост никуда не переносится,
    # и оставлять его в эталоне значило бы сравнивать с тем, чего в полях нет.
    source = ROLE_TAIL.sub('', normalize(deal.get('extra')))
    out, taken = {}, []
    for sent in sentences(deal.get('extra')):
        # Пометку «Сумма: …» разбираем отдельно: это разметка импорта.
        mark = SUM_MARK.search(sent)
        if mark and 'sum' not in out and 'val' not in out:
            value = mark.group(1).strip()
            key = 'val' if ESTIMATE.search(sent) else 'sum'
            out[key] = value if key == 'sum' else sent
            taken.append(sent)
            continue
        party = PARTY_LINE.match(sent)
        if party and not DEAL_VERB.search(party.group(2)):
            role = party.group(1).lower()
            key = 'seller' if role.startswith('прод') else 'buyer_name'
            if key not in out:
                out[key] = party.group(2).strip()
                taken.append(sent)
                continue
        for field, rx in RULES:
            if field in out or not rx.search(sent):
                continue
            out[field] = sent
            taken.append(sent)
            break
    # Всё, что не разошлось по полям, остаётся «Контекстом» — но только если
    # это не весь текст целиком: тогда переносить нечего, поле дублировало бы
    # «Дополнительную информацию» слово в слово.
    left = [s for s in sentences(deal.get('extra')) if s not in taken]
    if left and taken:
        out['context'] = ' '.join(left)
    # Проверка по ПРЕДЛОЖЕНИЯМ, а не по всей строке: «Контекст» склеен из
    # остатков, которые в исходнике могли стоять не подряд, и сплошная
    # проверка не подтвердила бы верную сборку. Каждое предложение обязано
    # лежать в источнике дословно — это и есть граница «переносить можно,
    # сочинять нельзя».
    for key, value in out.items():
        if key == 'sum':
            continue
        for part in sentences(value):
            assert normalize(part) in source, \
                '%s: поле %s не является дословным куском extra' % (deal['id'], key)
    return out


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    targets = [d for d in data['deals'] if not d.get('eco') and not d.get('law')]
    print('скудных карточек: %d' % len(targets))

    plan, empty = [], 0
    counts = {}
    for deal in targets:
        fields = classify(deal)
        if not fields:
            empty += 1
            continue
        for key in fields:
            counts[key] = counts.get(key, 0) + 1
        plan.append((deal, fields))

    print('разобрано: %d, нечего переносить: %d' % (len(plan), empty))
    print('по полям:', dict(sorted(counts.items(), key=lambda kv: -kv[1])))
    print()
    for deal, fields in plan[:3]:
        print('%s  %s' % (deal['id'], str(deal.get('title'))[:58]))
        for key, value in fields.items():
            print('   %-11s %s' % (key, str(value)[:96]))

    # Правило проверяется на себе: чужое предложение на текст не ложится.
    assert normalize('Выручка 2099 — 1 млрд ₽') not in normalize(targets[0].get('extra')), \
        'проверка подстроки не работает'

    print('\nкарточек к правке: %d' % len(plan))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for deal, fields in plan:
        assert not deal.get('eco') and not deal.get('law'), \
            '%s: карточка уже не скудная — перепроверьте' % deal['id']
        eco = dict(EMPTY_ECO)
        for key, value in fields.items():
            if key == 'sum':
                deal['sum'] = value
                eco['sum'] = value
            elif key in ('seller', 'buyer_name'):
                # Сторона — поле карточки, а не линзы. Пишем только в пустое:
                # заполненное значение выверено, и заменять его разбором нельзя.
                if not deal.get(key) and not deal.get('buyer' if key == 'buyer_name' else 'seller_id'):
                    deal[key] = value
            else:
                eco[key] = value
        deal['eco'] = eco
        deal['law'] = dict(EMPTY_LAW)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
