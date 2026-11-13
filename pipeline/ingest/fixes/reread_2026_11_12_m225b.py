# -*- coding: utf-8 -*-
"""Вычитка базы, марафон 12 ноября 2026, партия m225 (вторая часть): тип, заголовки, итоги торгов.

Статьи открыты заново (curl с обычным браузерным User-Agent) и сохранены save_source.save()
с day='2026-11-12_m225'. Проза — write_card.py (план партии); дата по реестру, суммы, доли,
предмет, источник 404 — pipeline/archive/2026-11/reread_oneoff_m225b.py.

Запуск: REVIEW_ONLY=m225 python3 pipeline/ingest/review.py
"""

CARDS = ['g812a7b3b', 'g1e37f107', 'gf145d639']

SP = 'https://secpost.ru/arzamas-capital-usilivaet-ib-portfel-posle-microolap-investor-vlozhilsya-v-ngr-softlab'
NB = 'https://nationalbusiness.kz/news/kazahstanskiy-investor-vishel-iz-kapitala-popavshey-pod-sanktsii-rossiyskoy-kompanii-bb760a/'
Q_NGR = ('Российский ИБ-вендор NGR Softlab привлек стратегического инвестора: 26% компании получила Arzamas Capital, '
         'следует из данных «Контур.Фокуса».')
Q_FONTE = ('18 сентября 2026 года частная компания Fonte Inceptia Alpha Fund OEIC Limited завершила сделку по продаже '
           'принадлежащего ей пакета порядка 18% обыкновенных голосующих акций')
Q_ARKT = ('При этом комиссия постановила заключить договор с ООО «Авиавторресурс» по цене не менее начальной '
          '(минимальной).')

FIXES = [
 {'id': 'g812a7b3b', 'field': 'title',
  'old': 'Arzamas Capital купила 26% ИБ-компании NGR Softlab',
  'new': 'Arzamas Capital купил 26% NGR Softlab',
  'quote': Q_NGR,
  'why': 'вычитка m225: латинское название без рода — глагол мужского рода (pipeline/title_standard.py, RULES); '
         'без описания предмета'},
 {'id': 'g1e37f107', 'field': 'date', 'old': '2026-09-30', 'new': '2026-09-18', 'quote': Q_FONTE,
  'why': 'вычитка m225: 30 сентября — день статьи о данных СПАРК; продажу, по заявлению Fonte Capital, '
         'завершили 18 сентября'},
 {'id': 'g1e37f107', 'field': 'seller',
  'old': 'Fonte Inceptia Alpha Fund OEIC Limited (структура Fonte Capital)',
  'new': 'Fonte Inceptia Alpha Fund OEIC Limited', 'quote': Q_FONTE,
  'why': 'вычитка m225: сторона — юрлицо целиком, без пометки «структура»'},
 {'id': 'g1e37f107', 'field': 'src', 'old': None, 'new': ['National Business', NB], 'quote': Q_FONTE,
  'why': 'вычитка m225: заявление Fonte Capital о полной продаже пакета 18 сентября 2026 года'},
 {'id': 'g1e37f107', 'field': 'src', 'old': None,
  'new': ['Движение.ру', 'https://dvizhenie.ru/media/9326/forbes-struktura-umara-kremleva-mogla-kupit-i-pereprodat-18-akcij-samoleta'],
  'quote': 'В сентябре доля Fonte Inceptia Alpha Fund сократилась до менее 5%, а к началу октября фонд продал все '
           'принадлежавшие ему акции. Конечный покупатель не раскрывается.',
  'why': 'вычитка m225: вторая версия срока выхода и неофициальные данные о конечном интересанте'},
 {'id': 'g1e37f107', 'field': 'src', 'old': None,
  'new': ['Московская перспектива', 'https://mperspektiva.ru/topics/kazakhstanskiy-fond-sokratil-dolyu-v-gk-samolet-do-5/'],
  'quote': 'В пресс-службе «Самолета» заявили, что компания не комментирует действия отдельных акционеров.',
  'why': 'вычитка m225: первоисточник «Движения» 8735 не открывается (сброс соединения); та же новость'},
 {'id': 'gf145d639', 'field': 'buyer_name', 'old': None, 'new': 'ООО «Авиавторресурс»', 'quote': Q_ARKT,
  'why': 'вычитка m225: покупатель по итогам торгов'},
 {'id': 'gf145d639', 'field': 'title',
  'old': '«Атомфлот» выставил на аукцион корпус атомного ледокола «Арктика»',
  'new': '«Авиавторресурс» купил на торгах корпус ледокола «Арктика»',
  'quote': 'Сам аукцион признали несостоявшимся из-за участия только одного претендента. При этом комиссия '
           'постановила заключить договор с ООО «Авиавторресурс» по цене не менее начальной (минимальной).',
  'why': 'вычитка m225: заголовок по стандарту закрытых торгов «X купил на торгах Y»'},
 {'id': 'gf145d639', 'field': 'src', 'old': None, 'new': ['Би-порт', 'https://b-port.com/news/367211'],
  'quote': 'На участие в аукционе была подана только одна заявка — от ООО «Авиавторресурс», зарегистрированного '
           'в Люберцах.',
  'why': 'вычитка m225: итог торгов; NewsRoom24 отвечает 404 — снят разовым скриптом'},
]
