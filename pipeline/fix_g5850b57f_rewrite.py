"""Яндекс/VK (g5850b57f): проза карточки своими словами.

Владелец 8 октября 2026: «переписан ли текст с источника дословно или
пересказано?» — `verbatim_check.py` нашёл дословные куски CNews и Хабра в
шести полях (79, 67, 41, 19, 19 и 13 слов подряд), а правило с 3 октября
2026 — пересказ (docs/sources_legal.md, правило 1). Факты те же, слова наши;
«Цель сделки» больше не начинается с «такой симбиоз» — предложение без
опоры на предыдущий абзац источника.

Поля поставлены записями FIXES (fixes/fix_yandex_vk_b2b_tech_jv.py) — их
отпечатки сохраняются в `proofread_absorbed` (docs/card_editing.md).
Без ключа — сухой прогон; запись — --write.
"""
import importlib
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA = os.path.join(ROOT, 'static/data/deals_promoted.json')
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))

NEW = {
    'eco.share': 'Как разделят доли в объединённом бизнесе, пока не решено; один из обсуждаемых '
                 'вариантов — поровну, по 50% у каждой стороны.',
    'eco.target_fin': 'Yandex B2B Tech выделено в отдельное направление в конце 2024 года; за 2024 год '
                      'его выручка составила 32,2 млрд ₽ (+48,4% к 2023 году — «Яндекс» впервые раскрыл эти '
                      'цифры в марте 2025 года), за первое полугодие 2026 года — 28,9 млрд ₽ (+32% год к году). '
                      'VK Tech за первое полугодие 2026 года заработал 9 млрд ₽ (+35,3%); по выручке за 2024 год '
                      'Yandex B2B Tech в 2,4 раза крупнее.',
    'eco.rationale': 'Объединение двух прямых конкурентов должно дать крупнейшего игрока российского рынка '
                     'облачных и корпоративных ИТ-решений с долей около 30%.',
    'eco.context': 'Какие активы войдут в совместный проект, не раскрыто: со стороны VK это может быть весь '
                   'VK Tech, со стороны «Яндекса» — Yandex Cloud, «Яндекс 360» и один из ИИ-активов Yandex B2B '
                   'Tech. Совокупная выручка объединяемых бизнесов за первое полугодие 2026 года — 37,9 млрд ₽. '
                   'Площадкой для СП может стать ООО «БТБ Тех». VK Tech разрабатывает корпоративное ПО: облако '
                   'VK Cloud, платформу для совместной работы VK WorkSpace, инструменты для данных Tarantool и '
                   'VK Data Platform. Переговоры стороны ведут с июля 2026 года; публично о них стало известно '
                   '23 сентября.',
    'law.struct': 'Условия не раскрыты. По данным АНО «Экспертный центр электронного государства», '
                  'формальности планируется завершить в первом квартале 2027 года, а итоговая форма ещё не '
                  'выбрана: либо совместное предприятие, либо слияние двух направлений — с объединением '
                  'портфеля продуктов для государственных заказчиков.',
    'law.appr': 'Объединение подтвердил замминистра цифрового развития Евгений Филатов на форуме '
                '«Цифровые решения». По словам представителя Минцифры, ведомство следит за процессом и '
                'влияет на него: у обеих компаний общий портфель продуктов для госзаказчиков.',
}
OLD_HEAD = {
    'eco.share': 'Как именно новый актив поделят',
    'eco.target_fin': 'Направление Yandex B2B Tech было создано',
    'eco.rationale': 'Такой симбиоз',
    'eco.context': 'Также пока нет точных данных',
    'law.struct': 'Условия сделки не раскрываются. Известно лишь',
    'law.appr': 'Заместитель министра цифрового развития Евгений Филатов подтвердил',
}


def apply(card, companies):
    import review
    batch = importlib.import_module('fixes.fix_yandex_vk_b2b_tech_jv')
    absorbed = card.setdefault('proofread_absorbed', {})
    for field, text in NEW.items():
        lens, key = field.split('.')
        cur = card[lens][key]
        if cur == text:
            continue
        # Повторный запуск после правки формулировки: прежняя наша версия тоже годится.
        assert cur.startswith(OLD_HEAD[field]) or cur[:40] == text[:40], (field, cur[:60])
        card[lens][key] = text
        print('%s: своими словами' % field)
    for fix in batch.FIXES:
        if fix['id'] != card['id'] or review.already_applied(fix, card, companies):
            continue
        fp = review.fix_fingerprint(fix['new'])
        if fp not in absorbed.setdefault(fix['field'], []):
            absorbed[fix['field']].append(fp)
            print('отпечаток записи %s сохранён' % fix['field'])


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == 'g5850b57f')
    apply(card, data.get('companies'))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh = json.load(open(DATA, encoding='utf-8'))
    live = next(d for d in fresh['deals'] if d['id'] == 'g5850b57f')
    apply(live, fresh.get('companies'))
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(fresh, f, ensure_ascii=False, indent=1)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
