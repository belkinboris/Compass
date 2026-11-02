# -*- coding: utf-8 -*-
"""Пилот полной перечитки, партия «б» (2 ноября 2026): то, что таблица FIXES
не умеет. Пара к pipeline/ingest/fixes/pilot_reread_2026_11_02_b.py
(список ONE_OFF там же — с причиной и источником каждой правки).

- g489b4309 (X5/ВКТ): мертвая ссылка x5.ru (404) снята, Коммерсантъ — первым
  (главная ссылка поста); профили ВКТ и Анны Фомичевой — без «Фудтайм» и
  «100%» (только Forbes, капча; другими изданиями не подтверждено).
- g53bd1536 (Свеза/ЦФУ): этап «Сделка завершена» 29 → 26 июня (29 — дата
  заметки mergers.ru), заметка этапа — своими словами вместо копии релиза.
- g718e3d0e (Flowwow): этап переговоров «5–8 млрд» → «более 8 млрд» (нижней
  границы нет нигде), заметка этапа отмены — своими словами; тема «Уход
  иностранного владельца» снята (владельцы — российские основатели).
- gb92f7119 (Ростех/CarPrice): eco.sum — заглушка без выдуманного «отдельно не
  оценивались»; адвокат ответчика снята из консультантов (docs/card_parties.md);
  где искали продавца — accepted_notes.no_profile.seller.

    python3 pipeline/archive/2026-11/fix_pilot_reread_2026_11_02_b.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NO_ADV = [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не названы']]


def main(argv):
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']

    x5 = deals['g489b4309']
    dead = ['X5 Group (официальный сайт)', 'https://www.x5.ru/ru/news/h5-pokupaet-distribyutora-vkt/']
    kom = ['Коммерсантъ', 'https://www.kommersant.ru/doc/8634923']
    assert dead in x5['src'] and kom in x5['src'], x5['src']
    x5['src'] = [kom] + [s for s in x5['src'] if s not in (dead, kom)]
    for cid, old, new in (
            ('g1fc90a04',
             'Дистрибьютор продуктов питания в Приволжском округе из Нижнего Новгорода, владелец франчайзинговой '
             'сети магазинов «Фудтайм». Юрлицо — ООО «Торговый дом «ВКТ».',
             'Дистрибьютор продуктов питания в Нижегородской области и Приволжье, работает с 1992 года. '
             'Юрлицо — ООО «Торговый дом «ВКТ».'),
            ('g01a9e264',
             'Владелец 100% долей ООО «Торговый дом ВКТ» (дистрибьютор продуктов питания в Приволжье, сеть '
             '«Фудтайм»); в 2026 году продала бизнес X5 Group.',
             'Учредитель ООО «Торговый дом ВКТ» (дистрибьютор продуктов питания в Приволжье) по данным '
             '«Контур.Фокуса»; в 2026 году компанию купила X5.')):
        assert comps[cid].get('desc') == old, (cid, comps[cid].get('desc'))
        comps[cid]['desc'] = new

    sv = deals['g53bd1536']['events'][0]
    assert sv['kind'] == 'closed' and sv['date'] == '2026-06-29' and sv['note'].startswith('Сумма сделки и ее структура')
    sv['date'] = '2026-06-26'
    sv['note'] = '«Свеза» объявила о покупке 100% ЦФУ, сумму не раскрыла.'

    fw = deals['g718e3d0e']
    neg, canc = fw['events'][0], fw['events'][1]
    assert '5–8 млрд ₽' in neg['note'] and ['Оценка', '5–8 млрд ₽ по сообщениям СМИ'] in neg['facts']
    neg['note'] = neg['note'].replace('оценивали в 5–8 млрд ₽', 'оценивали более чем в 8 млрд ₽')
    assert '5–8' not in neg['note']
    neg['facts'] = [['Оценка', 'более 8 млрд ₽ по сообщениям СМИ'] if f == ['Оценка', '5–8 млрд ₽ по сообщениям СМИ']
                    else f for f in neg['facts']]
    assert canc['note'] == ('Стороны не договорились о финансовых условиях. Flowwow сообщил, что готов '
                            'рассматривать предложения других инвесторов.')
    canc['note'] = ('Переговоры сорвались: Flowwow не устроили условия «Яндекса». Компания говорит, что открыта '
                    'к предложениям других инвесторов.')
    assert 'Уход иностранного владельца' in fw['themes']
    fw['themes'] = [t for t in fw['themes'] if t != 'Уход иностранного владельца']

    cp = deals['gb92f7119']
    assert cp['eco']['sum'].startswith('Не раскрыта: CarPrice и доли'), cp['eco']['sum']
    cp['eco']['sum'] = 'Не раскрыта'
    assert cp['law']['adv'] == [['Юридический консультант', 'Кира Корума',
                                 'адвокат Александра Галицкого (сторона ответчика/третьих лиц)']]
    cp['law']['adv'] = NO_ADV
    cp.setdefault('accepted_notes', {}).setdefault('no_profile', {})['seller'] = (
        'Изъятие по решению суда, продажи не было; доли были оформлены на разных лиц (ООО «Селаникар» — '
        'кипрская Vendebita Trading Ltd, ООО «Группа С-Терра» — Юрий Ивашков, Сергей Рябко, Галина Попова и др.; '
        'Ведомости, 26 марта 2026)')

    print('g489b4309 src и 2 профиля; g53bd1536 этап; g718e3d0e 2 этапа и тема; gb92f7119 eco.sum, law.adv, заметка')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(BASE, encoding='utf-8').read() == raw, 'база изменилась во время прогона — перезапустите'
    out = json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
    open(BASE, 'w', encoding='utf-8').write(out)
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
