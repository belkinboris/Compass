# -*- coding: utf-8 -*-
"""«Концентрация» (g2ab91f78), 3 ноября 2026: карточка ушла в консоль с одним
источником (mergers.ru). Владелец нашел за минуту пост консультанта (Buzko Legal)
и разборы — исследователь собрал семь источников. Пересказ — по ним.

    python3 pipeline/archive/2026-11/fix_kontsentratsiya_sources_2026_11_03.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

SRC = [
    ['Buzko Legal (Telegram)', 'https://t.me/BuzkoLegal/260'],
    ['Агентство Бизнес Новостей', 'https://abn.agency/2026/11/02/konczentracziya-privlekla-12-mlrd-rublej-na-razrabotku-himicheskih-produktov/'],
    ['M&A Новости (Telegram)', 'https://t.me/dealsma/7531'],
    ['GxP News', 'https://gxpnews.net/2026/11/konczentracziya-privlekla-12-mlrd-rublej-na-razrabotku-himproduktov-dlya-farmaczevtiki/'],
    ['Фармпром', 'https://pharmprom.news/koncentraciya-privlekla-12-mlrd-rublej-na-razvitie-malotonnazhnoj-ximii/'],
    ['Русский венчур (Telegram)', 'https://t.me/rusven/7820'],
]


def main(argv):
    raw = open(PENDING, encoding='utf-8').read()
    data = json.loads(raw)
    c = [x for x in data['cards'] if x['id'] == 'g2ab91f78'][0]
    assert c['title'] == 'Химический холдинг «Концентрация» привлек 1,2 млрд рублей инвестиций'
    assert len(c['src']) == 1 and not c['law']['adv']
    c['title'] = 'Российские фонды проинвестировали 1,2 млрд рублей в химический холдинг «Концентрация»'
    c['src'] = SRC + c['src']
    c['law']['adv'] = [['Юридический консультант', 'Buzko Legal',
                        'консультант «Концентрации»: партнер Ирина Карева, юрист Анастасия Максимова']]
    c['law']['struct'] = ('Раунд построен по модели cash-in: все деньги поступают в саму компанию, долю у '
                          'прежних акционеров никто не выкупает. Средства пойдут на разработку технологий, '
                          'обновление действующих мощностей и новые производства, в том числе завод '
                          'поливинилпирролидона в Томской области. Какую долю получили инвесторы, не раскрывается.')
    c['eco']['rationale'] = ('Сооснователь Александр Панов говорит, что холдинг не строит заводы с нуля, а '
                             'собирает производство из уже существующих мощностей, и что новый раунд показывает: '
                             'инвесторы верят в отрасль и в эту модель.')
    c['eco']['target_fin'] = ('Выручка группы за 2025 год — 4,6 млрд ₽, на 21% больше, чем годом раньше; чистая '
                              'прибыль — 95 млн ₽. На 2026 год компания ждет выручку 6,5 млрд ₽.')
    c['eco']['context'] = (
        '«Концентрация» — бывшая AppScience: в июне 2026 года компания сменила название и из поставщика '
        'реактивов стала холдингом со своим производством. За три года она хочет выпустить не меньше 30 своих '
        'продуктов для фармацевтики, косметики и нефтехимии. Сейчас у нее контрактные производства в '
        'Петербурге, Волгограде, Москве и области и своя площадка в Тульской области.\n\n'
        'В начале октября 2026 года Московский венчурный фонд объявил, что вложит в «Концентрацию» 150 млн ₽. '
        'Входит ли эта сумма в раунд 1,2 млрд ₽, компания не сообщала.\n\n'
        'В апреле 2026 года «Концентрация» вместе с ООО «Трансхим» создала ООО ПК «Интермедиат»: 51% у '
        '«Концентрации», 49% у «Трансхима».')
    notes = c.setdefault('accepted_notes', {})
    notes['no_profile'] = {'buyer': 'названия фондов не раскрыты: Buzko Legal — «синдикат профильных российских '
                                    'фондов», abn.agency, M&A Новости, GxP News, Фармпром, Русский венчур, '
                                    'Mergers.ru, conc.ru, moscow.vc'}
    notes['searched'] = ['Buzko Legal (Telegram)', 'abn.agency', 'M&A Новости (Telegram)', 'GxP News', 'Фармпром',
                         'Русский венчур', 'conc.ru', 'moscow.vc', 'Telegram-каналы юрфирм (консультант инвесторов)',
                         'Forbes, РБК, Ведомости, Коммерсант — материалов о раунде нет']
    for k in ('accepted', 'accepted_hash', 'second_read', 'second_read_hash', 'post_preview'):
        c.pop(k, None)
    print('g2ab91f78: заголовок, 6 источников, консультант, struct, rationale, target_fin, context')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(PENDING, encoding='utf-8').read() == raw
    open(PENDING, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
