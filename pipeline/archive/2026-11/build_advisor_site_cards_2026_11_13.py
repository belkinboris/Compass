# -*- coding: utf-8 -*-
"""Карточки сделок, найденных сверкой с сайтами Advance Capital и Aspring Capital
(бэклог E17, 13 ноября 2026; владелец: «Все сделки которых у нас нет надо
проработать»).

Сверка показала сделки, которых не было ни в базе, ни в очереди. Лента их не
приносила (сделки 2022–2024 годов), поэтому карточки заводятся тем же путем, что
у прежних «вне очереди» (`build_salmon_group_round_2026_10_20.py`): этот скрипт
кладет в очередь (`static/data/pending.json`) оболочку со структурными полями,
текст пишется по фактам (`write_card.py`), дальше приемка и второе чтение.

Структурные поля — по прочитанным источникам (тексты забраны на диск
`fetch_article_texts.py --write` / `save_source.py`); у каждого значения ниже
в комментарии — цитата. Финансовый консультант — со страницы сделок самой
фирмы (advancecapital.ru/sdelki/, aspring.capital/services) и из ее
пресс-релиза.

id — от ключа карточки (sha1), чтобы повторный запуск не плодил дублей.

    python3 pipeline/archive/2026-11/build_advisor_site_cards_2026_11_13.py            # сухой прогон
    python3 pipeline/archive/2026-11/build_advisor_site_cards_2026_11_13.py --write
    python3 pipeline/archive/2026-11/build_advisor_site_cards_2026_11_13.py --write --only nms-medsi
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
ASPRING = 'https://aspring.capital/services'
ADV_PR = 'https://advancecapital.ru/news/news/press-releases/%d/'
ADV_DEALS = 'https://advancecapital.ru/sdelki/'


def fin_adv(side, firm, url):
    return ['Финансовый консультант ' + side, firm,
            'Финансовый консультант в сделке, по сообщению самой фирмы. Источник: ' + url]


CARDS = [
    # 12. «Медси» / «Национальная медицинская сеть».
    #   Пресс-релиз «Медси», 11.01.2022: «сообщает о приобретении 100% долей в уставном
    #   капитале сети «Промедицина» в Уфе и сети «Диалайн» в Волгограде у текущих
    #   владельцев Национальной медицинской сети».
    #   Коммерсантъ, 12.01.2022: «Группа компаний «Медси» и «Национальная медицинская
    #   сеть» (НМС) закрыли сделку купли-продажи… Продавцами выступили фонд прямых
    #   инвестиций «Эльбрус капитал» и миноритарии «Промедицины». Сумму сделки «Медси»
    #   не раскрывает»; «в конце декабря 2021 года за «Медси» были зарегистрированы
    #   права на доли» — дня регистрации нет, дата карточки — день объявления.
    #   aspring.capital/services: «Aspring Capital выступил в сделке эксклюзивным
    #   инвестиционным консультантом владельцев НМС».
    {'key': 'nms-medsi',
     'match': ('Промедицин', 'Диалайн'),
     'draft': {
         'date': '2022-01-11',
         'title': '«Медси» купила сети клиник «Промедицина» и «Диалайн» у «Национальной медицинской сети»',
         'ind': 'Здравоохранение', 'type': 'M&A', 'status': 'Закрыта',
         'src': [['«Медси»', 'https://medsi.ru/press-centr/news/medsi-priobrela-kliniki-natsionalnoy-meditsinskoy-seti-v-ufe-i-volgograde/'],
                 ['Коммерсантъ', 'https://www.kommersant.ru/doc/5158318'],
                 ['РБК', 'https://ufa.rbc.ru/ufa/12/01/2022/61deb1979a79471e7dc5f5d7'],
                 ['Vademecum', 'https://vademec.ru/news/2022/01/11/medsi-zakryla-sdelku-po-pokupke-aktivov-natsionalnoy-meditsinskoy-seti/'],
                 ['Aspring Capital', ASPRING]],
         'buyer_name': '«Медси»',
         'asset': 'Сети клиник «Промедицина» и «Диалайн»',
         'seller': '«Национальная медицинская сеть»',
         'sum': 'Не раскрыта'},
     'set': {'kind': 'acquisition', 'date_basis': 'announcement'},
     'finadv': 'Aspring Capital — эксклюзивный инвестиционный консультант владельцев «Национальной медицинской сети»',
     'adv': [fin_adv('продавца (владельцы «Национальной медицинской сети»)', 'Aspring Capital', ASPRING)]},
    # 11. VK / YClients.
    #   Интерфакс, 20.12.2023: «VK приобрел 100% долей в группе компаний YCLIENTS… говорится в
    #   сообщении холдинга. Сумма сделки не называется».
    #   Интерфакс, 22.03.2024: «Сумма сделки по покупке интернет-холдингом VK ООО "Уайклаентс"…
    #   составляет 3,94 млрд рублей, сообщается в финансовой отчетности VK».
    #   CNews, 22.03.2024: «Сделка была завершена в конце 2023 г.» — дня закрытия нет, дата — день объявления.
    #   aspring.capital/services: «эксклюзивным финансовым советником владельцев компании YClients».
    #   Продавцы поименно в источниках не названы — поле пустое, поиск записан в заметке приемки.
    {'key': 'vk-yclients',
     'match': ('yclients',),
     'draft': {
         'date': '2023-12-20',
         'title': 'VK купил YClients',
         'ind': 'ИТ и интернет', 'type': 'M&A', 'status': 'Закрыта',
         'src': [['Интерфакс', 'https://www.interfax.ru/business/937269'],
                 ['Интерфакс', 'https://www.interfax.ru/business/951796'],
                 ['vc.ru', 'https://vc.ru/money/961189-vk-kupila-servis-dlya-onlain-zapisi-v-sfere-uslug-yclients'],
                 ['CNews', 'https://www.cnews.ru/news/top/2024-03-22_vk_potratil_39_milliarda_na'],
                 ['Aspring Capital', ASPRING]],
         'buyer_name': 'VK',
         'asset': 'YClients',
         'sum': '3,94 млрд ₽'},
     'set': {'kind': 'acquisition', 'date_basis': 'announcement', 'sum_basis': 'disclosed'},
     'finadv': 'Aspring Capital — эксклюзивный финансовый советник владельцев YClients',
     'adv': [fin_adv('продавцов (владельцы YClients)', 'Aspring Capital', ASPRING)]},
    # 10. «Лента» / «Улыбка радуги».
    #   Коммерсантъ, 02.12.2024: «Ритейлер «Лента» объявил о приобретении 100% акций АО «Торговый дом
    #   Эра», которое владеет сетью… «Улыбка радуги». Сделка уже получила одобрение ФАС… В сообщении
    #   «Ленты» сумма сделки не приводится».
    #   Ведомости (Северо-Запад), 02.12.2024: ««Лента» купила петербургскую сеть магазинов «Улыбка
    #   радуги»… «Лента» начнет консолидировать приобретенный бизнес в своей отчетности уже с декабря».
    #   aspring.capital/services: «эксклюзивным финансовым советником… компании «Улыбка радуги» в сделке
    #   по продаже в пользу Ленты».
    #   Продавцы акций в источниках о сделке не названы — поле пустое, поиск записан в заметке приемки.
    {'key': 'lenta-ulybka-radugi',
     'match': ('улыбка радуги', 'торговый дом'),
     'draft': {
         'date': '2024-12-02',
         'title': '«Лента» купила сеть магазинов «Улыбка радуги»',
         'ind': 'Ритейл', 'type': 'M&A', 'status': 'Закрыта',
         'src': [['Коммерсантъ', 'https://www.kommersant.ru/doc/7344356'],
                 ['РБК', 'https://www.rbc.ru/business/02/12/2024/674d67f69a79473bf84d9a3f'],
                 ['Ведомости', 'https://spb.vedomosti.ru/business/articles/2024/12/02/1078570-lenta-kupila-peterburgskuyu-set-magazinov-ulibka-radugi'],
                 ['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/12/03/1078710-lenta-zahodit-v-format-magazinov-drogeri'],
                 ['Aspring Capital', ASPRING]],
         'buyer_name': '«Лента»',
         'asset': '«Улыбка радуги»',
         'sum': 'Не раскрыта'},
     'set': {'kind': 'acquisition', 'date_basis': 'announcement'},
     'finadv': 'Aspring Capital — эксклюзивный финансовый советник «Улыбки радуги»',
     'adv': [fin_adv('продавца («Улыбка радуги»)', 'Aspring Capital', ASPRING)]},
    # 3. «Р-Инвестиции» / Sloplast.
    #   Коммерсантъ, 17.06.2024: «Холдинг «Р-Инвестиции» выкупил производителя HPL-пластиков… Sloplast,
    #   сообщил “Ъ” финансовый консультант продавца Advance Capital. Стоимость сделки не раскрывается…
    #   По данным СПАРК, подконтрольное АО «Р-Инвестиции» ООО «Перспектива» 23 мая получило 100% в ООО
    #   «Завод слоистых пластиков» (ЗСП), ООО «Дизайнинвест» и ООО «Инновационные технологии». Прежде ЗСП
    #   владел Дмитрий Зайцев, следует из СПАРК».
    #   Пресс-релиз Advance Capital, 16.06.2024: «эксклюзивного финансового консультанта продавца,
    #   юридическим консультантом выступила юридическая компания Алруд» (чьим — не сказано).
    {'key': 'r-invest-sloplast',
     'match': ('sloplast',),
     'draft': {
         'date': '2024-05-23',
         'title': '«Р-Инвестиции» купили производителя пластика Sloplast',
         'ind': 'Химия и удобрения', 'type': 'M&A', 'status': 'Закрыта',
         'src': [['Коммерсантъ', 'https://www.kommersant.ru/doc/6772900'],
                 ['Advance Capital', ADV_PR % 419]],
         'buyer_name': '«Р-Инвестиции»',
         'asset': 'Sloplast',
         'seller': 'Дмитрий Зайцев',
         'sum': 'Не раскрыта'},
     'set': {'kind': 'acquisition', 'date_basis': 'registry'},
     'finadv': 'Advance Capital — эксклюзивный финансовый консультант продавца',
     'adv': [fin_adv('продавца (Дмитрий Зайцев)', 'Advance Capital', ADV_PR % 419),
             ['Юридический консультант (сторона не названа)', 'АЛРУД',
              'По пресс-релизу Advance Capital: «юридическим консультантом выступила юридическая компания Алруд». '
              'Источник: ' + ADV_PR % 419]]},
    # 5. Milestone Capital / Kodix Auto (UDP Auto).
    #   Denuo, 01.03.2023: «Denuo выступила консультантом российского инвестиционного фонда Milestone
    #   Capital в связи с приобретением мажоритарной доли Kodix Auto… проведен ребрендинг Kodix Auto,
    #   новое наименование компании — UDP Auto».
    #   Пресс-релиз Advance Capital, 07.02.2023: «об успешном привлечении стратегического инвестора в
    #   компанию UDP Auto (ранее называвшуюся Kodix Auto)… Advance Capital выступил в роли эксклюзивного
    #   финансового консультанта UDP Auto. Сумма сделки не раскрывается». Размер доли не назван; день
    #   закрытия не назван — дата по объявлению (7 февраля 2023 года).
    {'key': 'milestone-udp-auto',
     'match': ('kodix',),
     'draft': {
         'date': '2023-02-07',
         'title': 'Фонд Milestone Capital купил контрольную долю в Kodix Auto',
         'ind': 'ИТ и интернет', 'type': 'M&A', 'status': 'Закрыта',
         'src': [['Advance Capital', ADV_PR % 407],
                 ['Denuo', 'https://denuo.legal/ru/insights/releases/230301/'],
                 ['Mergers.ru', 'https://mergers.ru/news/Kodix-Auto-menyaet-nazvanie-na-UDP-Auto-i-privlekaet-investicii-na-konsolidaciyu-IT-kompanij-avtootrasli-80638']],
         'buyer_name': 'Milestone Capital',
         'asset': 'UDP Auto (бывшая Kodix Auto)',
         'sum': 'Не раскрыта'},
     'set': {'kind': 'acquisition', 'date_basis': 'announcement'},
     'finadv': 'Advance Capital — эксклюзивный финансовый консультант UDP Auto',
     'adv': [fin_adv('компании (UDP Auto)', 'Advance Capital', ADV_PR % 407),
             ['Юридический консультант покупателя (Milestone Capital)', 'Denuo',
              'Фирма сопровождала покупку: структурирование, документы, регуляторные разрешения, подписание и '
              'закрытие. Источник: https://denuo.legal/ru/insights/releases/230301/']]},
    # 8. «Альтаир Медиа» / «Пикабу».
    #   vc.ru, 29.09.2022: «27 сентября 2022 года владельцем 100% ООО «Пикабу» стало АО «Альтаир Медиа»,
    #   следует из данных «Контур.Фокуса»… Сумма сделки не называется».
    #   CNews, 30.09.2022: «В 2018 г. Хрящев учредил ООО «Пикабу», 2020–2021 гг. выделил ключевым
    #   сотрудникам… Павлу Санникову и… Всеволоду Кирову – доли в проекте, которые выросли к августу
    #   2022 г. до 5% и 8,5 % соответственно».
    #   advancecapital.ru/sdelki/: «Продажа медиа-портала Пикабу стратегическому инвестору… Финансовый
    #   консультант продавца. Сентябрь 2022».
    {'key': 'altair-pikabu',
     'match': ('пикабу',),
     'draft': {
         'date': '2022-09-27',
         'title': '«Альтаир Медиа» купила «Пикабу»',
         'ind': 'Медиа', 'type': 'M&A', 'status': 'Закрыта',
         'src': [['CNews', 'https://www.cnews.ru/news/top/2022-09-30_lider_novyh_lyudej_v_gosdume'],
                 ['vc.ru', 'https://vc.ru/social/510915-kompaniya-vladelec-sportsru-kupila-pikabu'],
                 ['Sostav', 'https://www.sostav.ru/publication/vladelets-sports-ru-kupil-pikabu-56781.html'],
                 ['Коммерсантъ', 'https://www.kommersant.ru/doc/6196841'],
                 ['Advance Capital', ADV_DEALS]],
         'buyer_name': 'АО «Альтаир Медиа»',
         'asset': '«Пикабу»',
         'seller': 'Максим Хрящев, Всеволод Киров и Павел Санников',
         'sum': 'Не раскрыта'},
     'set': {'kind': 'acquisition', 'date_basis': 'registry'},
     'finadv': 'Advance Capital — финансовый консультант продавца',
     'adv': [fin_adv('продавца (владельцы «Пикабу»)', 'Advance Capital', ADV_DEALS)]},
    # 15. «Медисорб» / «Кинетик-фарм» (добавка к E17: сайт Althaus Group).
    #   Коммерсантъ (Прикамье), 26.05.2025: «Структура… АО «Медисорб групп» получила 80% долей в
    #   уставном капитале… «Кинетик-фарм». Согласно сервису «СПАРК-Интерфакс», переход долей…
    #   состоялся 16 мая… Ранее компанию контролировали господин Шоболов (80%) и госпожа Балаянц
    #   (20%)… Сумма сделки не раскрывается».
    #   althausgroup.ru/news/, 04.06.2025: «Альтхаус сопровождал сделку по покупке «Кинетик-фарм»
    #   фармкомпанией «Медисорб»» (чьим консультантом — в ленте не сказано).
    {'key': 'medisorb-kinetik-farm',
     'match': ('кинетик-фарм',),
     'draft': {
         'date': '2025-05-16',
         'title': '«Медисорб» купил 80% лаборатории «Кинетик-фарм»',
         'ind': 'Фармацевтика', 'type': 'M&A', 'status': 'Закрыта',
         'src': [['Коммерсантъ', 'https://www.kommersant.ru/doc/7754643'],
                 ['GxP News', 'https://gxpnews.net/2025/05/medisorb-stal-osnovnym-vladelczem-moskovskoj-laboratorii/'],
                 ['Althaus Group', 'https://althausgroup.ru/news/']],
         'buyer_name': '«Медисорб»',
         'asset': '«Кинетик-фарм»',
         'seller': 'Дмитрий Шоболов и Тамара Балаянц',
         'sum': 'Не раскрыта'},
     'set': {'kind': 'acquisition', 'date_basis': 'registry'},
     'adv': [['Юридический консультант (сторона не названа)', 'Althaus Group',
              'По сообщению фирмы: «Альтхаус сопровождал сделку по покупке «Кинетик-фарм» фармкомпанией '
              '«Медисорб»». Источник: https://althausgroup.ru/news/']]},
    # 17. «Новые башни» / «Прайм Телеком» (добавка к E17: сайт ALUMNI Partners).
    #   Коммерсантъ, 05.11.2025: «Инфраструктурный оператор ГК «Новые башни» купил регионального
    #   оператора антенно-мачтовых сооружений «Прайм Телеком», следует из данных «Спарк-Интерфакс».
    #   Покупка включает четыре юридических лица… В «Новых башнях» “Ъ” подтвердили факт сделки… ООО
    #   «Прайм Телеком»… На 60% принадлежало… Мураду Бениаминову… и на 40% Марине Тамминен». День
    #   сделки не назван — дата годом.
    #   alumnipartners.ru/projects/: «Консультирование группы компаний «Новые башни» в связи с
    #   приобретением Группы компаний «Прайм Телеком», владеющей сетью из около 350 антенно-мачтовых
    #   сооружений».
    {'key': 'novye-bashni-prime-telecom',
     'match': ('прайм телеком',),
     'draft': {
         'date': '2025',
         'title': '«Новые башни» купили оператора вышек связи «Прайм Телеком»',
         'ind': 'Телеком', 'type': 'M&A', 'status': 'Закрыта',
         'src': [['Коммерсантъ', 'https://www.kommersant.ru/doc/8179818'],
                 ['ALUMNI Partners', 'https://www.alumnipartners.ru/projects/']],
         'buyer_name': '«Новые башни»',
         'asset': '«Прайм Телеком»',
         'seller': 'Мурад Бениаминов и Марина Тамминен',
         'sum': 'Не раскрыта'},
     'set': {'kind': 'acquisition'},
     'adv': [['Юридический консультант покупателя («Новые башни»)', 'ALUMNI Partners',
              'По сообщению фирмы: консультирование группы «Новые башни» в связи с приобретением группы '
              '«Прайм Телеком». Источник: https://www.alumnipartners.ru/projects/']]},
]


# Поправки к уже заведенным оболочкам: (ключ, поле, было, стало) — с assert на старое.
FIXUPS = [
    # Продавец в схеме — фонд (профиль Elbrus Capital привязан приемкой): текст роли
    # должен называть того же, кого профиль (docs/card_parties.md, «ссылку и текст правят вместе»).
    ('nms-medsi', 'seller', '«Национальная медицинская сеть»', 'Elbrus Capital'),
]


# 2. РБК / Hyper AdTech: оболочка уже лежала в очереди непрочитанной (gba225690, из поста BIRCH
#   от 30 января 2025 года, статус «Обсуждается»). Новая карточка не заводится — правится эта.
#   Пресс-релиз Advance Capital, 19.12.2024: «рад объявить о завершении сделки по продаже 60% долей в
#   ведущей программатик-платформе… Hyper AdTech. Инвестором выступила группа компаний РБК…
#   в роли эксклюзивного финансового консультанта Hyper AdTech. Сумма сделки не раскрывается».
#   Коммерсантъ, 14.09.2026: «у ГК РБК уже есть 60% долей в ООО, компания закрыла сделку по
#   приобретению этого пакета в декабре 2024 года. Тогда стороны не раскрывали сумму сделки».
#   BIRCH: «Команда BIRCH консультировала РБК в ходе заключения сделки по вхождению РБК в капитал Hyper».
#   День закрытия не назван — дата по объявлению (19 декабря 2024 года).
HYPER_ID = 'gba225690'
HYPER_BIRCH = 'https://t.me/BIRCHLEGAL/1358'


def patch_hyper(pending):
    card = next((c for c in pending['cards'] if c['id'] == HYPER_ID), None)
    if card is None or card.get('date') == '2024-12-19':
        return 0
    assert card['date'] == '2025-01-30' and card['status'] == 'Обсуждается', (card['date'], card['status'])
    assert card['title'] == 'РБК вошел в капитал платформы мобильной видеорекламы Hyper', card['title']
    assert card['asset'] == 'платформы мобильной видеорекламы Hyper' and not card.get('reviewed')
    assert card['src'] == [['Телеграм-канал @BIRCHLEGAL', HYPER_BIRCH]] and not card['law']['adv']
    card['date'] = '2024-12-19'
    card['date_basis'] = 'announcement'
    card['status'] = 'Закрыта'
    card['kind'] = 'acquisition'
    card['title'] = 'РБК купил 60% Hyper AdTech'
    card['asset'] = 'Hyper AdTech'
    card['eco']['sum'] = 'Не раскрыта'
    card['src'] = [['РБК', 'https://www.rbc.ru/technology_and_media/19/12/2024/6761685e9a7947e494fbf5fb'],
                   ['Advance Capital', ADV_PR % 424],
                   ['Коммерсантъ', 'https://www.kommersant.ru/doc/8953886'],
                   ['Телеграм-канал @BIRCHLEGAL', HYPER_BIRCH]]
    card['eco']['finadv'] = 'Advance Capital — эксклюзивный финансовый консультант Hyper AdTech'
    card['law']['adv'] = [
        ['Юридический консультант покупателя (РБК)', 'BIRCH',
         'Команда фирмы консультировала РБК при заключении сделки; руководил партнер Никита Бутенко. '
         'Источник: t.me/BIRCHLEGAL/1358'],
        fin_adv('продавца (Hyper AdTech)', 'Advance Capital', ADV_PR % 424)]
    for ev in card['party_evidence'].get('target', []):
        ev['value'] = 'Hyper AdTech'
    print('ПОПРАВКА   %s: оболочка Hyper приведена к прочитанным источникам' % HYPER_ID)
    return 1


def card_id(key):
    return 'g' + hashlib.sha1(('advisor-site:' + key).encode('utf-8')).hexdigest()[:8]


def build(row):
    card = promote.to_card(row['draft'], card_id(row['key']))
    card['src'] = [list(s) for s in row['draft']['src']]      # подписи изданий — как записаны здесь
    for k, v in (row.get('set') or {}).items():
        card[k] = v
    if row['draft'].get('sum'):
        card['eco']['sum'] = row['draft']['sum']
    if row.get('finadv'):
        card['eco']['finadv'] = row['finadv']
    card['law']['adv'] = [list(r) for r in row.get('adv') or []]
    card['pending_since'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    return card


def main(write=False, only=None):
    pending = json.load(open(PENDING, encoding='utf-8'))      # читается прямо перед записью
    base = json.load(open(DATA, encoding='utf-8'))
    everything = pending['cards'] + base['deals']
    ids = {c['id'] for c in everything}
    added = 0
    for row in CARDS:
        if only and row['key'] not in only:
            continue
        cid = card_id(row['key'])
        if cid in ids:
            print('УЖЕ ЕСТЬ   %s %s' % (cid, row['key']))
            continue
        twins = [c['id'] for c in everything
                 if all(m.lower() in json.dumps(c, ensure_ascii=False).lower() for m in row['match'])]
        if twins:
            print('ОТКАЗ      %s: похожая карточка уже есть — %s' % (row['key'], ', '.join(twins)))
            continue
        card = build(row)
        print('НОВАЯ      %s %s: %s' % (cid, row['key'], card['title']))
        pending['cards'].append(card)
        added += 1
    fixed = 0
    by_id = {c['id']: c for c in pending['cards']}
    for key, field, old, new in FIXUPS:
        card = by_id.get(card_id(key))
        if only and key not in only or card is None or card.get(field) == new:
            continue
        assert card.get(field) == old, (key, field, card.get(field))
        card[field] = new
        for ev in (card.get('party_evidence') or {}).get(field, []):
            if ev.get('value') == old:
                ev['value'] = new
        print('ПОПРАВКА   %s %s: %r -> %r' % (card['id'], field, old, new))
        fixed += 1
    added += fixed
    if not only or 'rbc-hyper' in only:
        added += patch_hyper(pending)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0
    if added:
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nЗаписано карточек и поправок: %d.' % added)
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    only = None
    if '--only' in args:
        only = set(args[args.index('--only') + 1].split(','))
    sys.exit(main(write='--write' in args, only=only))
