# -*- coding: utf-8 -*-
"""Вторая волна консультантов из дополнительного consultant-only прохода
ChatGPT (14 августа) — 15 карточек, каждая проверена ЧТЕНИЕМ реально
скачанного текста источника (не только совпадением цитаты, но и тем, что
предмет/стороны абзаца — те же, что на карточке).

ДВЕ НАХОДКИ ИЗ ТОГО ЖЕ ПРОХОДА НЕ ВОШЛИ — перепутанные карточки:
- g5880d206 (Игорь Ким/«Фольксваген банк Рус») — цитаты ChatGPT были на
  самом деле про Т-Технологии/Центральный телеграф и «Восход», к этой
  сделке отношения не имеют;
- ga58eb450 (Русал/Pioneer Aluminium, Индия) — цитаты были про холдинг
  «Вертикаль Инвестиции» и Sk Capital, к этой сделке отношения не имеют.
Тот же класс ошибки, что уже ловился в этой сессии (gacc757b6/gad633118).

Запуск: python3 pipeline/enrich_consultants_r1_wave2.py            # сухой
        python3 pipeline/enrich_consultants_r1_wave2.py --write    # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (id, роль, фирма, пояснение, url, заглушка_или_None, роли_до)
PLAN = [
    ('g016f1b13',
     'Консультант сделки',
     'IBC Real Estate',
     'Собственный материал IBC Real Estate называет компанию консультантом '
     'сделки по переходу гостиничного комплекса LesArt Resort под управление '
     'Vizant — конкретная сторона не уточняется. '
     'Источник: https://ibcrealestate.ru/history/odin-iz-krupneyshikh-'
     'gostinichnykh-kompleksov-podmoskovya-pereshel-pod-upravlenie-kompanii-vizant/',
     'https://ibcrealestate.ru/history/odin-iz-krupneyshikh-gostinichnykh-kompleksov-podmoskovya-pereshel-pod-upravlenie-kompanii-vizant/',
     'Стороны сделки',
     ['Стороны сделки']),

    ('gd3769bb9',
     'Финансовый консультант продавца (Е-ПРОМ)',
     'Advance Capital',
     'Advance Capital на своём сайте называет себя эксклюзивным финансовым '
     'консультантом Е-ПРОМ в сделке по продаже 49,99% долей фонду «ВИМ '
     'Инвестиции». Источник: https://advancecapital.ru/news/news/press-releases/433/',
     'https://advancecapital.ru/news/news/press-releases/433/',
     None,
     ['Юридический консультант инвестора («ВИМ Инвестиции»)']),

    ('geb8edd5c',
     'Юридическое сопровождение банкротства продавца (АО «Талион»)',
     'Юридическая группа «Пилот»',
     '«Пилот» осуществляет сопровождение процедуры банкротства АО «Талион» '
     'на стороне конкурсного управляющего и независимых кредиторов — не '
     'консультант сделки купли-продажи как таковой, а юрсопровождение '
     'банкротного процесса, из которого актив продан. '
     'Источник: https://lgpilot.ru/projects/talion-imperial-otel-5-prodan-za-4-4-mlrd-rubley/',
     'https://lgpilot.ru/projects/talion-imperial-otel-5-prodan-za-4-4-mlrd-rubley/',
     'Стороны сделки',
     ['Стороны сделки']),

    ('g7299791f',
     'Финансовый консультант (по данным Forbes)',
     'Strategy Partners',
     'Ведомости со ссылкой на источник Forbes в инвестбанковской среде '
     'называют Strategy Partners консультантом сделки БКС/«Форштадт»; '
     'сторона не уточняется. '
     'Источник: https://www.vedomosti.ru/finance/news/2025/10/06/1144612-gruppa-bks-oprovergla',
     'https://www.vedomosti.ru/finance/news/2025/10/06/1144612-gruppa-bks-oprovergla',
     'Стороны сделки',
     ['Стороны сделки']),

    ('g68975b9d',
     'Финансовый консультант продавца',
     'Aspring Capital',
     'The Moscow Times со ссылкой на источники «Коммерсанта» называет '
     'Aspring Capital финансовым консультантом продавца в продаже холдинга '
     'Sokolov; управляющий партнёр Aspring Capital Сергей Айрапетов '
     'подтвердил факт закрытия сделки. '
     'Источник: https://ru.themoscowtimes.com/2025/08/14/benefitsiar-'
     'yuvelirnogo-kholdinga-sokolov-prodal-ego-chastnomu-investoru-paku-gazeta-a171592',
     'https://ru.themoscowtimes.com/2025/08/14/benefitsiar-yuvelirnogo-kholdinga-sokolov-prodal-ego-chastnomu-investoru-paku-gazeta-a171592',
     'Стороны сделки',
     ['Стороны сделки']),

    ('g8e9d37ba',
     'Консультант по продаже',
     'Astoria Capital',
     'BG.ru называет Astoria Capital (создана экс-сотрудниками Сбербанка) '
     'структурой, привлечённой владельцами ТЦ «Авиапарк» для реализации '
     'продажи. Источник: https://bg.ru/bg/business/comm-news/28500-aviapark',
     'https://bg.ru/bg/business/comm-news/28500-aviapark',
     'Стороны сделки',
     ['Стороны сделки']),

    ('technored',
     'Финансовый консультант (организация сделки)',
     'BSF Partners',
     'TECHNORED на своём сайте называет инвестбанк BSF Partners участником '
     'организации сделки с ГК «Вартон». '
     'Источник: https://technored.ru/news/Varton_TECHNORED_soglashenie/',
     'https://technored.ru/news/Varton_TECHNORED_soglashenie/',
     None,
     ['Сопровождение сделки']),

    ('gf424fa11',
     'Юридический консультант',
     'Stonebridge Legal',
     'Stonebridge Legal на своём сайте относит сделку Wildberries/Russ '
     '(вошла в топ-5 M&A-сделок 2024 года по версии Право.ру) к своим '
     'проектам; конкретная сторона не уточняется. '
     'Источник: https://stonebridgelegal.ru/ru/news/sdelka-stonebridge-legal-voshla-v-top-5-sdelok-m-a/',
     'https://stonebridgelegal.ru/ru/news/sdelka-stonebridge-legal-voshla-v-top-5-sdelok-m-a/',
     'Стороны сделки',
     ['Стороны сделки']),

    ('g68ebf773',
     'Юридический консультант эмитента',
     'Stonebridge Legal',
     'Stonebridge Legal на своём сайте называет себя консультантом IPO '
     '«ВсеИнструменты.ру» на Мосбирже. '
     'Источник: https://stonebridgelegal.ru/ru/news/komanda-stonebridge-legal-soprovozhdala-ipo-krupne/',
     'https://stonebridgelegal.ru/ru/news/komanda-stonebridge-legal-soprovozhdala-ipo-krupne/',
     'Стороны сделки',
     ['Стороны сделки']),

    ('ga218f75c',
     'Советник сделки',
     'Unicorn',
     'Коммерсантъ со ссылкой на инвестбанк Unicorn называет его советником '
     'сделки по покупке «Акульчевым» 95% кондитерской фабрики «Колос». '
     'Источник: https://www.kommersant.ru/doc/8293536',
     'https://www.kommersant.ru/doc/8293536',
     'Стороны сделки',
     ['Стороны сделки']),

    ('gf577d893',
     'Юридический консультант покупателя (АО «Кластер капитал»)',
     'ELWI',
     'Коммерсантъ («Сделки года») прямо называет ELWI консультантом '
     'покупателя, а Denuo — консультантом продавца в продаже 55,44% СДЭК. '
     'Источник: https://www.kommersant.ru/doc/7327316',
     'https://www.kommersant.ru/doc/7327316',
     'Стороны сделки',
     ['Стороны сделки']),

    ('gaa59d3a1',
     'Юридический консультант продавца (АО «Тетра»)',
     'Nektorov, Saveliev & Partners (NSP)',
     'Коммерсантъ («Сделки года») называет NSP консультантом продавца в '
     'продаже ГК «Дон Агро» агрохолдингу «Просторы». '
     'Источник: https://www.kommersant.ru/doc/7327316',
     'https://www.kommersant.ru/doc/7327316',
     'Стороны сделки',
     ['Стороны сделки']),

    ('gf3c5069f',
     'Юридический консультант покупателя',
     'Forward Legal',
     'Коммерсантъ («Сделки года») в описании сделки Росимущества по продаже '
     '40 компаний (актуализировано под нашу карточку — покупатель Александр '
     'Клячин/KR Properties) называет Forward Legal консультантом покупателя. '
     'Источник: https://www.kommersant.ru/doc/8077927',
     'https://www.kommersant.ru/doc/8077927',
     'Стороны сделки',
     ['Стороны сделки']),

    ('g8ed07ff5',
     'Юридический консультант покупателя (частного инвестора)',
     'LEVEL Legal Services',
     'LEVEL Legal Services на своём сайте называет себя консультантом '
     'частного инвестора при приобретении группы компаний «Западная» — '
     'той же сделки, где продавцов вёл BIRCH. '
     'Источник: https://www.level-legal.com/news/yuridicheskaya-firma-level-legal-services-osushestvila-kompleksnoe-yuridicheskoe-konsultirovanie-chastnogo-investora-v-svyazi-s-priobreteniem-gk-zapadnaya',
     'https://www.level-legal.com/news/yuridicheskaya-firma-level-legal-services-osushestvila-kompleksnoe-yuridicheskoe-konsultirovanie-chastnogo-investora-v-svyazi-s-priobreteniem-gk-zapadnaya',
     None,
     ['Юридический консультант продавцов (акционеров МКАО «Западная Голд Майнинг»)']),

    ('cc2929a95',
     'Юридический консультант покупателя (частного инвестора)',
     'LEVEL Legal Services',
     'LEVEL Legal Services на своём сайте называет себя консультантом '
     'частного инвестора при приобретении группы компаний «Западная» — '
     'той же сделки, где продавцов вёл BIRCH (эта карточка — тот же сюжет, '
     'что и g8ed07ff5, под другим id). '
     'Источник: https://www.level-legal.com/news',
     'https://www.level-legal.com/news',
     None,
     ['Юридический консультант']),
]

SRC_LABEL = {
    'g016f1b13': 'IBC Real Estate',
    'gd3769bb9': 'Advance Capital',
    'geb8edd5c': 'lgpilot.ru',
    'g7299791f': 'Ведомости',
    'g68975b9d': 'The Moscow Times',
    'g8e9d37ba': 'BG.ru',
    'technored': 'technored.ru',
    'gf424fa11': 'Stonebridge Legal',
    'g68ebf773': 'Stonebridge Legal',
    'ga218f75c': 'Коммерсантъ',
    'gf577d893': 'Коммерсантъ — «Сделки года»',
    'gaa59d3a1': 'Коммерсантъ — «Сделки года»',
    'gf3c5069f': 'Коммерсантъ — «Сделки года»',
    'g8ed07ff5': 'LEVEL Legal Services',
    'cc2929a95': 'LEVEL Legal Services',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for did, role, firm, note, url, drop, before in PLAN:
        deal = by_id.get(did)
        assert deal is not None, 'карточки %s нет в базе' % did
        adv = (deal.get('law') or {}).get('adv') or []
        names = ' | '.join(str(a[1]) for a in adv if len(a) > 1).lower()
        assert firm.split(' (')[0].lower() not in names, \
            '%s: %s уже записан — перепроверьте' % (did, firm)
        assert [str(a[0]) for a in adv if a] == before, \
            '%s: роли другие (%r), чем ожидалось (%r)' % (
                did, [str(a[0]) for a in adv if a], before)
        if drop:
            assert drop in before, '%s: заглушки «%s» нет' % (did, drop)
        existing_urls = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
        print('%s  %s' % (did, (deal.get('title') or '')[:60]))
        if drop:
            print('    убрать заглушку: %s' % drop)
        print('    + %s — %s' % (role, firm))
        if url in existing_urls:
            print('    (источник уже стоит, src не дублируем)')

    print('\nкарточек к правке: %d' % len(PLAN))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for did, role, firm, note, url, drop, before in PLAN:
        deal = by_id[did]
        law = deal.setdefault('law', {})
        adv = [a for a in (law.get('adv') or []) if not (drop and str(a[0]) == drop)]
        adv.append([role, firm, note])
        law['adv'] = adv
        existing_urls = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
        if url not in existing_urls:
            deal.setdefault('src', []).append([SRC_LABEL[did], url])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
