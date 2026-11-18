# -*- coding: utf-8 -*-
"""Оценки экспертов — обратно в сумму (владелец, 18 ноября 2026, отмена решения 13 ноября).

По решению 13 ноября 2026 у 158 карточек сумма «N (по оценке)» стала «Не раскрыта», а прежнее
значение ушло в `retracted.sum`. Владелец: «если специалисты давали оценку, то конечно должны
писать в картах цену по оценке» (docs/card_money.md, «Что идет в сумму»).

Возвращается только то, что проверяется механически:
  * сейчас в sum и eco.sum — «Не раскрыта»;
  * в retracted.sum ровно одно значение с «(по оценке)», и формат суммы правильный
    (форма «Не раскрыта (по оценке эксперта N)» переводится в «N (по оценке)»);
  * то же число стоит в тексте карточки (eco.val, eco.context, law.struct, extra) — оценка не
    пропала из карточки при вычитке, то есть снималась именно правилом, а не как ошибка.
Остальное печатается списком «РУКАМИ» и не трогается. Массовая правка — только с ключом пробы
владельца (pipeline/mass_edit_guard.py): MASS_OK=<ключ> ... --write.

    python3 pipeline/archive/2026-11/expert_estimates_back_2026_11_19.py            # сухой прогон
    python3 pipeline/archive/2026-11/expert_estimates_back_2026_11_19.py --sample   # 10 карточек на пробу
    MASS_OK=<ключ> python3 pipeline/archive/2026-11/expert_estimates_back_2026_11_19.py --write
"""
import copy
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
SKIP = {'g1f2895c0', 'g5d3527dd'}      # возвращены отдельно
# Проба 18 ноября: продавец сам назвал цену ниже оценки экспертов — решает человек.
MANUAL = {'g801dd6a9': 'продавец назвал цену меньше 5 млрд ₽, эксперты — от 5,5 млрд ₽'}
OK_FORM = re.compile(r'^(?:≈\s?|До |Более |Примерно |Около )?\$?\d+(?:,\d+)?(?:[–-]\d+(?:,\d+)?)?\s*(?:млн|млрд)'
                     r'(?:\s*(?:₽|\$|€))?\s*\(по оценке\)$')
OLD_FORM = re.compile(r'^Не раскрыта \(по оценке [^—)]*?(?:— )?(?:не выше )?(\d+(?:,\d+)?(?:[–-]\d+(?:,\d+)?)?\s*(?:млн|млрд)\s*₽)\)$')


def normalize(v):
    v = str(v).strip()
    m = OLD_FORM.match(v)
    if m:
        v = m.group(1) + ' (по оценке)'
    v = v.replace('-', '–', 1) if re.match(r'^\D*\d+(?:,\d+)?-\d', v) else v
    return v if OK_FORM.match(v) else None


def prose(d):
    eco, law = d.get('eco') or {}, d.get('law') or {}
    return ' '.join(str(x or '') for x in (eco.get('val'), eco.get('context'), eco.get('rationale'),
                                             law.get('struct'), d.get('extra')))


def first_number(v):
    m = re.search(r'\d+(?:,\d+)?', v)
    return m.group(0) if m else None


def plan(data):
    auto, manual = [], []
    for d in data['deals']:
        if d['id'] in SKIP or not str(d.get('sum') or '').startswith('Не раскрыт'):
            continue
        if d['id'] in MANUAL:
            manual.append((d['id'], d['title'], (d.get('retracted') or {}).get('sum'), MANUAL[d['id']]))
            continue
        est = [v for v in (d.get('retracted') or {}).get('sum') or [] if 'по оценке' in str(v)]
        if not est:
            continue
        if len(est) != 1:
            manual.append((d['id'], d['title'], est, 'в retracted несколько значений'))
            continue
        new = normalize(est[0])
        if not new:
            manual.append((d['id'], d['title'], est, 'формат суммы не разобран'))
            continue
        num = first_number(new)
        text = prose(d)
        m = num and re.search(r'(?<![\d,])' + re.escape(num) + r'(?![\d])', text)
        if not m:
            manual.append((d['id'], d['title'], est, 'числа нет в тексте карточки'))
            continue
        near = text[max(0, m.start() - 120):m.end() + 40]
        if re.search(r'номинал|уставн', near, re.I):
            manual.append((d['id'], d['title'], est, 'число — номинал или уставный капитал, не оценка'))
            continue
        if not re.search(r'оцени|оценк|могл[аио]?\s+состав|может\s+состав|предполага|считает|подсчитал|допуска', near, re.I):
            manual.append((d['id'], d['title'], est, 'рядом с числом нет слов оценки'))
            continue
        if re.search(r'инвестиц|вложени', near, re.I):
            manual.append((d['id'], d['title'], est, 'число — инвестиции или вложения, не цена'))
            continue
        stake = ((d.get('facts') or {}).get('stake') or {}).get('value')
        if stake is None:
            ms = re.match(r'\s*(\d+(?:,\d+)?)\s*%', str((d.get('eco') or {}).get('share') or ''))
            stake = float(ms.group(1).replace(',', '.')) if ms else None
        if stake is not None and stake < 99.5 and (not re.search(r'дол[яиюей]|пакет|акци', near, re.I)
                                                   or re.search(r'100\s*%|\bвесь\b|\bвсю\b|целиком', near, re.I)):
            manual.append((d['id'], d['title'], est, 'куплена доля %s%%, а оценка, похоже, всей компании' % stake))
            continue
        if re.search(r'выставил|выставлен', near, re.I):
            manual.append((d['id'], d['title'], est, 'оценка времен выставления на продажу, не сделки'))
            continue
        if re.search(r'неофициальн|собеседник|по данным источник', text, re.I):
            manual.append((d['id'], d['title'], est, 'в карточке есть неофициальная цена сделки с другим числом'))
            continue
        auto.append((d['id'], d['title'], est[0], new))
    return auto, manual


def apply(data, auto):
    by = {i: (old, new) for i, _t, old, new in auto}
    for d in data['deals']:
        if d['id'] in by:
            old, new = by[d['id']]
            assert str(d['sum']).startswith('Не раскрыт') and str(d['eco'].get('sum')).startswith('Не раскрыт')
            d['sum'] = d['eco']['sum'] = new
            d['retracted']['sum'].remove(old)
            if not d['retracted']['sum']:
                d['retracted'].pop('sum')
            if not d['retracted']:
                d.pop('retracted')


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))      # перечитано прямо перед записью
    auto, manual = plan(data)
    if '--sample' in argv:
        for i, t, old, new in auto[::max(1, len(auto) // 10)][:10]:
            d = next(x for x in data['deals'] if x['id'] == i)
            print('%s  %s\n   сумма: Не раскрыта -> %s\n   текст: %s\n' % (i, t, new, str(d['eco'].get('val', ''))[:300]))
        return 0
    print('Вернуть автоматически: %d' % len(auto))
    for i, t, old, new in auto:
        print('  %-12s %-60s -> %s' % (i, t[:60], new))
    print('\nРУКАМИ: %d' % len(manual))
    for i, t, est, why in manual:
        print('  %-12s %-55s %s — %s' % (i, t[:55], est, why))
    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write и MASS_OK.')
        return 0
    old = copy.deepcopy(data)
    apply(data, auto)
    import mass_edit_guard
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано: %d карточек.' % len(auto))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
