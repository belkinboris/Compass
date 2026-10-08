"""Переписывает своими словами поля трёх карточек, пойманных
`verbatim_check.py --queue` (8 октября 2026): g51fa80ce (Голдрупп),
g9fed3cb1 (Северная Лисица), g955d2c6b (Курган/бульвар Солнечный) — те
же находки, что уже исправили у Яндекс/VK (`fix_g5850b57f_rewrite.py`):
правило пересказа (docs/sources_legal.md, 3 октября 2026), дословные
цепочки от 12 слов без «ёлочек» и атрибуции. Факты те же, слова наши.

Отпечатки прежних записей FIXES сохраняются в `proofread_absorbed`
(docs/card_editing.md) — так `test_review_table_is_applied_and_not_pending`
не считает их неприменёнными.

Без ключа — сухой прогон; запись — --write.
"""
import importlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static/data/deals_promoted.json')
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))

CARDS = {
    'g51fa80ce': {
        'module': 'fixes.fix_goldrupp_chapa_auction',
        'new': {
            'eco.context': 'За право на участок с запасами 106 кг золота боролись семь компаний. '
                           'Геологическое изучение северной части Енисейского кряжа, где расположен '
                           'участок река Чапа — ручей Цой, началось в 1840-х годах; в советское время '
                           'здесь прошла крупномасштабная геологическая съёмка и другие исследования.',
            'law.terms': 'По условиям лицензии победитель должен оценить запасы полезных ископаемых '
                         'на участке и подать материалы на государственную экспертизу — уточнили в '
                         'министерстве.',
        },
        'old_head': {
            'eco.context': 'За право разведки и добычи полезных ископаемых',
            'law.terms': 'Согласно условиям лицензии',
        },
    },
    'g9fed3cb1': {
        'module': 'fixes.fix_severnaya_lisitsa_claims_sale',
        'new': {
            'eco.context': 'Залог — жилой комплекс премиум-класса «Резиденции Присутствия» на '
                           'Приморском шоссе (участок 26А) в Лисьем Носу: 12 частных резиденций с '
                           'отдельным входом и участком у каждой. Сбербанк держит в залоге 100% доли '
                           'единственного учредителя компании с 2023 года.',
            'law.terms': 'Строили по 214-ФЗ с использованием эскроу-счетов; разрешение на два корпуса '
                         'блокированной застройки получили в ноябре 2023 года. Оценочная стоимость '
                         'строительства — свыше 460,8 млн ₽, Сбербанк выдал под это кредитную линию на '
                         '370 млн ₽. Передачу объектов дольщикам планировали не позднее 26 апреля '
                         '2025 года.',
            'eco.target_fin': 'По итогам 2025 года прибыль компании — 3 млн ₽, на 194% больше год к '
                              'году; выручка в отчётности не отражена — доход разовый, от операций с '
                              'активами, а не от регулярных продаж.',
        },
        'old_head': {
            'eco.context': 'В залоге по обязательствам',
            'law.terms': 'Комплекс на Приморском шоссе строили',
            'eco.target_fin': 'По итогам 2025 года компания показала',
        },
    },
    'g955d2c6b': {
        'module': 'fixes.fix_kurgan_bulvar_solnechny_lot',
        'new': {
            'eco.share': 'Застройщиком до этого была структура бизнесмена Александра Бабочкина — '
                         'стороны долго судились из-за объекта.',
            'eco.val': 'Начальная цена на аукционе — 1 065 573,77 ₽, без учёта земельного участка, '
                       'по отчёту об оценке от 7 сентября.',
        },
        'old_head': {
            'eco.share': 'Прежде стройку вела компания',
            'eco.val': 'Администрация установит начальную цену',
        },
    },
}


def apply(card, companies, spec):
    import review
    batch = importlib.import_module(spec['module'])
    absorbed = card.setdefault('proofread_absorbed', {})
    for field, text in spec['new'].items():
        lens, key = field.split('.')
        cur = card[lens][key]
        if cur == text:
            continue
        assert cur.startswith(spec['old_head'][field]) or cur[:40] == text[:40], (field, cur[:60])
        card[lens][key] = text
        print('%s %s: своими словами' % (card['id'], field))
    for fix in batch.FIXES:
        if fix['id'] != card['id'] or review.already_applied(fix, card, companies):
            continue
        fp = review.fix_fingerprint(fix['new'])
        if fp not in absorbed.setdefault(fix['field'], []):
            absorbed[fix['field']].append(fp)
            print('%s: отпечаток записи %s сохранён' % (card['id'], fix['field']))


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    for cid, spec in CARDS.items():
        card = next(d for d in data['deals'] if d['id'] == cid)
        apply(card, data.get('companies'), spec)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh = json.load(open(DATA, encoding='utf-8'))
    for cid, spec in CARDS.items():
        live = next(d for d in fresh['deals'] if d['id'] == cid)
        apply(live, fresh.get('companies'), spec)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(fresh, f, ensure_ascii=False, indent=1)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
