# -*- coding: utf-8 -*-
"""Вычитка марафоном, партия m015 (12 ноября 2026): правки, которые review.py не принимает.

ЧТО ЧИНИТ. review.py не пишет сумму со знаком «≈» и «Не раскрыта», а `sum` и `eco.sum` должны
совпадать; заметки приемки (`accepted_notes`) и снятые значения (`retracted`) тоже не его поля.
Каждая операция — с assert на старое значение; правка факта подтверждается fact_edit_guard.log
(цитата и адрес статьи, сохраненной save_source.py в sources_2026-11-12_m015.json).
Повторный запуск ничего не ломает: уже примененная операция пропускается («уже применено»).

    python3 pipeline/archive/2026-11/reread_oneoff_m015.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m015.py --write   # только из reread_apply.py
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path[:0] = [os.path.join(ROOT, 'pipeline', 'ingest'), os.path.join(ROOT, 'pipeline'), ROOT]
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка 12 ноября 2026, партия m015'

# (id, поле, старое, новое, цитата, адрес) — цитата и адрес нужны правке факта
_CN = 'https://www.comnews.ru/content/240773/2025-08-19/2025-w34/1007/solar-poglotil-90-ooo-soft-plyus-dva-zakhoda'
_VA = 'https://www.vedomosti.ru/finance/articles/2025/08/21/1133342-s8-maksima-sovladeltsami-akvariusa'
SETS = [
 ('g3ece5143', 'sum', '1,8–2 млрд ₽ (по оценке)', '≈1 млрд ₽ (по оценке)',
  'Следовательно, 51%-ная доля могла обойтись «Росспиртпрому» примерно в 1 млрд руб.',
  'https://www.vedomosti.ru/business/articles/2025/08/08/1130442-rosspirtprom-priobrel-vodki'),
 ('g3ece5143', 'eco.sum', '1,8–2 млрд ₽ (по оценке)', '≈1 млрд ₽ (по оценке)',
  'Следовательно, 51%-ная доля могла обойтись «Росспиртпрому» примерно в 1 млрд руб.',
  'https://www.vedomosti.ru/business/articles/2025/08/08/1130442-rosspirtprom-priobrel-vodki'),
 ('g081ac83c', 'sum', '270–750 млн ₽ (по оценке)', '≈500 млн ₽ (по оценке)',
  '"90% компании я оцениваю в 500 млн руб.', _CN),
 ('g081ac83c', 'eco.sum', '270–750 млн ₽ (по оценке)', '≈500 млн ₽ (по оценке)',
  '"90% компании я оцениваю в 500 млн руб.', _CN),
 ('g081ac83c', 'date', '2025-08-01', '2025-08-25',
  'ЕГРЮЛ, история участников ООО «Софт Плюс» (ИНН 7804686897): 2025-08-25 ООО «СОЛАР-ПТ» 42,86% → 90%, '
  'Кудакова Елена Владимировна 57,14% → 10% (python3 pipeline/party_legal_names.py g081ac83c)', _CN),
 ('g081ac83c', 'date_basis', None, 'registry',
  'ЕГРЮЛ: 2025-08-25 доля ООО «СОЛАР-ПТ» в ООО «Софт Плюс» — 90%', _CN),
 ('g139db8c2', 'sum', 'До 100 млрд ₽ (по оценке)', '80–120 млрд ₽ (по оценке)',
  'Эксперты оценивают сделку в 80–120 млрд рублей, а всю компанию – в 100–150 млрд рублей', _VA),
 ('g139db8c2', 'eco.sum', 'До 100 млрд ₽ (по оценке)', '80–120 млрд ₽ (по оценке)',
  'Эксперты оценивают сделку в 80–120 млрд рублей, а всю компанию – в 100–150 млрд рублей', _VA),
 ('g139db8c2', 'date', '2025-08-01', '2025',
  'По данным CNews, средства поступили в сентябре. … S8 Capital и ГК «МТ-интеграция» в совокупности получили 79% '
  'акций компании (CTA.ru, 2 октября 2025); 21 августа 2025 года «Ведомости» писали о сделке в будущем времени — '
  'дня перехода нет ни в одном источнике, реестр акционеров АО скрыт', 'https://www.cta.ru/news/cta/182329.html'),
]
# (id, поле retracted, значение) — снятое проверенно неверное значение, чтобы enrich.py его не вернул
RETRACT = [
 ('g3ece5143', 'sum', '1,8–2 млрд ₽ (по оценке)'),
 ('g081ac83c', 'sum', '270–750 млн ₽ (по оценке)'),
 ('g139db8c2', 'sum', 'До 100 млрд ₽ (по оценке)'),
]
# Старые нарушения text_rules, которые партия исправила (пресс-атрибуция в extra g139db8c2): убрать из
# pipeline/text_rules_baseline.json, иначе test_card_text_follows_the_house_rules требует --rebaseline.
GONE_BASELINE = ['g139db8c2|extra|source_note|00e42852eb']
BASELINE = os.path.join(ROOT, 'pipeline', 'text_rules_baseline.json')
# (id, ключ accepted_notes через точку, текст)
NOTES = []

_MISSING = object()


def get(card, field):
    obj = card
    for p in field.split('.'):
        if not isinstance(obj, dict) or p not in obj:
            return None
        obj = obj[p]
    return obj


def put(card, field, value):
    parts = field.split('.')
    obj = card
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    obj[parts[-1]] = value


def apply(data):
    import fact_edit_guard
    by = {d['id']: d for d in data['deals']}
    done = 0
    for cid, field, old, new, quote, url in SETS:
        card = by[cid]
        cur = get(card, field)
        if cur == new:
            print('  уже применено: %s %s' % (cid, field))
            continue
        assert cur == old, '%s %s: в базе %r, ожидали %r' % (cid, field, cur, old)
        put(card, field, new)
        fact_edit_guard.log(card, field, new, quote, url, BY)
        print('  %s %s: %r → %r' % (cid, field, old, new))
        done += 1
    for cid, field, value in RETRACT:
        lst = by[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
            done += 1
    for cid, key, text in NOTES:
        card = by[cid]
        if get(card, 'accepted_notes.' + key) == text:
            continue
        put(card, 'accepted_notes.' + key, text)
        print('  %s accepted_notes.%s' % (cid, key))
        done += 1
    return done


def main(argv):
    write = '--write' in argv
    data = json.load(open(DATA, encoding='utf-8'))   # перечитана прямо перед записью
    old = copy.deepcopy(data)
    n = apply(data)
    if not write:
        print('Сухой прогон: %d изменений. Запись — --write.' % n)
        return 0
    if n:
        import mass_edit_guard
        mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    base = json.load(open(BASELINE, encoding='utf-8'))
    left = [k for k in base['known'] if k not in GONE_BASELINE]
    if len(left) != len(base['known']):
        base['known'] = left
        with open(BASELINE, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print('  text_rules_baseline.json: снято исправленных нарушений — %d' % len(GONE_BASELINE))
    print('Записано изменений: %d' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
