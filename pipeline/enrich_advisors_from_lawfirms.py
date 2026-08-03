# -*- coding: utf-8 -*-
"""Дописать консультантов в существующие карточки по объявлениям фирм.

ОТКУДА. Архив канала «РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ» (@LawFirms), собранный
`pipeline/ingest/scan_lawfirms_archive.py`: 5262 поста за 2021-12 – 2026-08.
Канал не парсился ни разу за всё время (на 3 августа 2026 в базе была одна
ссылка на него против 66 у @dealsma), хотя часть сделок публикуется только
здесь, а консультанты платят каналу за объявление о своём участии.

ЧТО ДЕЛАЕТ. Берёт из архива объявления о сопровождении (`advisors.py` —
имя фирмы из начала пресс-релиза), оставляет те, что прошли фильтр сделок
(`classify.py`) и нашли карточку в базе (`match.py`), и дописывает фирму в
`law.adv`, если её там ещё нет. Чужие поля не трогает.

ПОЧЕМУ ЭТО БЕЗОПАСНО — замер прогона 3 августа. Из 5005 постов 2022+ правило
дало 76 объявлений о сделках; 11 из них сопоставились с карточками базы, и у
9 названная фирма УЖЕ была записана — то есть правило независимо переоткрыло
факты, которые человек подтверждал вручную в прошлых волнах. Новых оказалось
две, и обе — тот же дефект, что у сделки Т-Технологии/Авто.ру: одна сторона
записана, другая нет.

ЧЕГО НЕ ДЕЛАЕТ. Не создаёт карточки: 65 объявлений не нашли карточки в базе,
и это отдельная работа через обычную цепочку притока (draft.py + promote.py с
подтверждением человеком), а не молчаливое добавление. Не переписывает уже
записанных консультантов — только дополняет список.

Запуск:
    python3 pipeline/enrich_advisors_from_lawfirms.py            # сухой прогон
    python3 pipeline/enrich_advisors_from_lawfirms.py --write    # записать
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'ingest'))

import advisors                       # noqa: E402
import classify                       # noqa: E402
import match as matcher               # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
ARCHIVE = os.path.join(ROOT, 'data', 'inbox', 'raw', 'lawfirms_archive.jsonl')
SOURCE_LABEL = 'РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ (@LawFirms)'
SINCE = '2022-01-01'   # граница сайта: сделки раньше 2022 года не показываются


def already_listed(deal, firm):
    for a in ((deal.get('law') or {}).get('adv') or []):
        if len(a) > 1 and a[1]:
            known = str(a[1]).lower()
            if firm.lower() in known or known in firm.lower():
                return True
    return False


def proposals(data, rows):
    by_id = {d['id']: d for d in data['deals']}
    idx = matcher.index_base(data['deals'], data.get('companies'), data.get('match_keys'))
    out = []
    for row in rows:
        text = row.get('text') or ''
        if (row.get('date') or '') < SINCE:
            continue
        found = advisors.lead_advisor(text)
        if not found:
            continue
        if not classify.looks_like_deal(text[:200], text[:600]):
            continue
        item = {'title': text[:200], 'summary': text[:600],
                'url': row['url'], 'date': row['date']}
        deal_id, why = matcher.match(item, idx)
        if not deal_id:
            continue
        firms, role, sentence = found
        deal = by_id[deal_id]
        for firm in firms:
            if not already_listed(deal, firm):
                out.append((deal_id, firm, role, sentence, row['url'], why))
    return out


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    rows = [json.loads(l) for l in open(ARCHIVE, encoding='utf-8') if l.strip()]
    by_id = {d['id']: d for d in data['deals']}

    props = proposals(data, rows)
    print('объявлений, дающих НОВОГО консультанта существующей карточке: %d' % len(props))
    for deal_id, firm, role, sentence, url, why in props:
        deal = by_id[deal_id]
        print('\n  %s — %s' % (deal_id, (deal.get('title') or '')[:70]))
        print('    было: %s' % ([a[1] for a in ((deal.get('law') or {}).get('adv') or []) if len(a) > 1] or 'пусто'))
        print('    ставим: %s — %s   [совпадение: %s]' % (role, firm, why))
        print('    источник: %s' % url)

    if write:
        for deal_id, firm, role, sentence, url, why in props:
            deal = by_id[deal_id]
            adv = deal.setdefault('law', {}).setdefault('adv', [])
            # Заглушку «Не раскрывались» заменяем: она означала «неизвестно», а
            # теперь известно. Остальные записи — другие стороны, их не трогаем.
            adv[:] = [a for a in adv if not (len(a) > 1 and str(a[1]).strip().lower().startswith('не раскрыва'))]
            note = '%s Источник: %s' % (sentence[:400], url)
            adv.append([role, firm, note])
            src = deal.setdefault('src', [])
            if not any(len(s) > 1 and s[1] == url for s in src):
                src.append([SOURCE_LABEL, url])
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в %s' % DATA)
    else:
        print('\nСухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
