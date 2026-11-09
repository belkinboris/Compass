# -*- coding: utf-8 -*-
"""Короткая проверка 9 ноября 2026, хвост: находки приемки, которые открылись после записи партий.

ЧТО ЧИНИТ. `reread_queue.py --stamp` после review.py, разового скрипта и
party_legal_names.py отказал в отметке по двум находкам:
  * date_unbased — g19410fc2 («Каппа РУС») и gfc3e1ae2 («Онтэкс РУ»): партия sc перенесла
    дату на 15 октября 2026 года — день, когда указ № 738 подписан и вступил в силу (ppt.ru);
    основание дня — подписание указа, date_basis = signing.
  * share_form — у предмета появился legal_short (party_legal_names.py), и доля должна быть
    записана долей в обществе. Там, где число доли и общество уже стоят в тексте, меняется
    только форма, факты те же:
      g90ccbac0 «100% ООО «Полигрин»…» → «100% доли в ООО «Полигрин»…»;
      g162de6fb «Куплено 100% ООО «Компания новая идея» — …» → «100% доли в ООО «Компания
        Новая Идея» — …» (имя по реестру: ООО "КОМПАНИЯ НОВАЯ ИДЕЯ");
      g5b2cf7bd «100%» → «100% доли в ООО «Амбрелла Альянс»» (Абирег: «приобретает 100%
        московского ООО «Амбрелла альянс»»);
      g5e1a7c24 «Куплено 75% долей; …» → «75% доли в ООО «Аврора-Ресурс»; …».
    Где доли в тексте нет (g62577a1d, g3555ea6e, ge9d4edaa, gc44a1e70) или обществ несколько
    (g24fe6d49), формы не выдумываем — причина в ok_findings ответа на отметку.

Поля eco.share у этих карточек несли записи FIXES — их отпечатки ложатся в
proofread_absorbed (docs/card_editing.md, «Правка поля мимо таблицы синхронизирует запись»).

    python3 pipeline/archive/2026-11/fix_short_check_2026_11_09_tail.py            # сухой прогон
    python3 pipeline/archive/2026-11/fix_short_check_2026_11_09_tail.py --write

Каждая операция проверяет старое значение (`assert`); база перечитывается прямо перед записью.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)
import review  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OPS = [
 ('g19410fc2', 'date_basis', None, 'signing'),
 ('gfc3e1ae2', 'date_basis', None, 'signing'),
 ('g90ccbac0', 'eco.share',
  '100% ООО «Полигрин»: по записи в ЕГРЮЛ от 23 октября 2026 года единственным участником общества стало ООО '
  '«Группа Логика Молока», четыре прежних участника вышли из общества.',
  '100% доли в ООО «Полигрин»: по записи в ЕГРЮЛ от 23 октября 2026 года единственным участником общества стало '
  'ООО «Группа Логика Молока», четыре прежних участника вышли из общества.'),
 ('g162de6fb', 'eco.share',
  'Куплено 100% ООО «Компания новая идея» — управляющей компании бренда Nomi; саму покупку провела «Гельтек РНД», '
  'дочка «Гельтека», с 13 октября.',
  '100% доли в ООО «Компания Новая Идея» — управляющей компании бренда Nomi; саму покупку провела «Гельтек РНД», '
  'дочка «Гельтека», с 13 октября.'),
 ('g5b2cf7bd', 'eco.share', '100%', '100% доли в ООО «Амбрелла Альянс»'),
 ('g5e1a7c24', 'eco.share', 'Куплено 75% долей; еще 25% осталось у «Аврора-Менеджмента».',
  '75% доли в ООО «Аврора-Ресурс»; еще 25% осталось у «Аврора-Менеджмента».'),
]


def _apply(data, log):
    cards = {d['id']: d for d in data['deals']}
    for cid, field, old, new in OPS:
        card = cards[cid]
        assert review.get_field(card, field) == old, (cid, field, review.get_field(card, field))
        if '.' in field:
            a, b = field.split('.')
            card[a][b] = new
        else:
            card[field] = new
        log.append('%s %s' % (cid, field))
        # Записи FIXES этого поля, которые теперь не применены, — отпечатком в proofread_absorbed.
        for f in review.FIXES:
            if (f['id'], f['field']) != (cid, field) or f['new'] is None:
                continue
            if review.already_applied(f, card, data['companies']):
                continue
            marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)
                log.append('  %s.%s: отпечаток %s' % (cid, field, fp))


def main(write=False):
    log = []
    _apply(json.load(open(DATA, encoding='utf-8')), log)
    print('\n'.join(log))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    fresh = json.load(open(DATA, encoding='utf-8'))
    _apply(fresh, [])
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
