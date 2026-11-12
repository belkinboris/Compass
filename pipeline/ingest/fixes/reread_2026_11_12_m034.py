# -*- coding: utf-8 -*-
"""Вычитка базы, марафон 12 ноября 2026, партия m034: заголовки по стандарту и новые источники.

Каждый источник открыт заново (curl с обычным браузерным User-Agent) и сохранен save_source.save() в
data/inbox/triage/sources_2026-11-12_m034.json. Проза — write_card.py (written_2026_11_12_m034.py),
профили и суммы «Не раскрыта» — разовый скрипт pipeline/archive/2026-11/reread_profiles_sums_m034.py.

  g1df89416 — «Кардиф»: Ъ 6632849 (ссылается на Интерфакс), Interfax.com 101124 (добавлен), АСН 86192,
              «Эксперт РА» (рэнкинг 2025); defense.insure — 403. ЕГРЮЛ: 4 апреля 2024 года АО «БНП Париба
              Кардиф» 100% → семь физлиц.
  gfde94a49 — «Обед.ру»: AK&M, Ведомости, Интерфакс 1053739, BFM (добавлен); «250–300 млн ₽» нет ни в одном
              источнике (Бурмистров оценил в 200 млн) — сумма снята скриптом.
  gcc054516 — «А Групп»: Интерфакс 953991, Ъ 8195369, «Северсталь Вместе»; ≈10 млрд — оценка аналитиков
              БКС («не превысила 10–15 млрд»), а не цена — снята скриптом, перенесена в eco.val.
  g91d021c6 — Gebr. Heinemann: РБК — 401; пересказы РБК: Право.ru, Sostav (добавлен), Fakti.bg (добавлен).
"""
WHY = 'вычитка 12 ноября 2026 (партия m034) по статье, сохраненной save_source.py; '
_J = ' … '

FIXES = [
 # ======================================================================= g1df89416 «Кардиф»
 {'id': 'g1df89416', 'field': 'title',
  'old': 'Группа физлиц приобрела 100% ООО «Страховая компания КАРДИФ» у BNP Paribas Cardif',
  'new': 'Дмитрий Руденко и партнеры купили «Кардиф» у BNP Paribas Cardif',
  'quote': 'Страховая компания «Кардиф», принадлежавшая французской BNP Paribas Cardif (входит в банковскую группу '
           'BNP Paribas), сменила владельцев. По данным «Интерфакса», теперь бывший предправления Почта-банка Дмитрий '
           'Руденко стал владельцем 40% страховой компании.',
  'why': WHY + 'стандарт заголовка закрытой покупки «X купил Y у Z» (pipeline/title_standard.py); «Группа физлиц» — '
         'родовое описание: семь покупателей, крупнейший — Дмитрий Руденко (40%)'},
 {'id': 'g1df89416', 'field': 'src',
  'old': [['Коммерсантъ', 'https://www.kommersant.ru/doc/6632849'], ['ASN', 'https://www.asn-news.ru/news/86192'],
          ['Дефанс Страхование', 'https://www.defense.insure/o-kompanii/']],
  'new': ['Интерфакс', 'https://interfax.com/newsroom/top-stories/101124/'],
  'quote': 'Information about the change of ownership at Cardif Insurance LLC appeared in the Unified State Registry of '
           'Legal Entities (USRLE) on April 4. Rudenko has received a 40% stake in the insurance company',
  'why': WHY + 'первоисточник: Ъ пишет «по данным «Интерфакса»»'},
 {'id': 'g1df89416', 'field': 'src',
  'old': [['Коммерсантъ', 'https://www.kommersant.ru/doc/6632849'], ['ASN', 'https://www.asn-news.ru/news/86192'],
          ['Дефанс Страхование', 'https://www.defense.insure/o-kompanii/'],
          ['Интерфакс', 'https://interfax.com/newsroom/top-stories/101124/']],
  'new': ['Эксперт РА', 'https://raexpert.ru/rankingtable/insurance/2025/1.1.2'],
  'quote': '32 Общество с ограниченной ответственностью "Дефанс Страхование" 7714701780 4104 город Москва 3 956.53',
  'why': WHY + 'премии за 2025 год (вместо цифр с сайта компании, который не открывается)'},
 # ======================================================================= gfde94a49 «Обед.ру»
 {'id': 'gfde94a49', 'field': 'title',
  'old': 'ВкусВилл купил 95% ООО «Обед.ру» – сервис доставки еды в офисы',
  'new': '«ВкусВилл» купил 95% сервиса корпоративного питания «Обед.ру»',
  'quote': '«Вкусвилл» закрыл сделку по приобретению 95% компании «Обед.ру» – это старейший сервис корпоративного питания '
           'в России, сообщил представитель сети.',
  'why': WHY + 'вторая часть заголовка через тире; стандарт «X купил N% Y» (pipeline/title_standard.py)'},
 {'id': 'gfde94a49', 'field': 'src',
  'old': [['АК&М', 'https://www.akm.ru/news/vkusvill_kupil_servis_po_dostavke_edy_v_ofisy_obed_ru/'],
          ['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/04/05/1030173-vkusvill-kupil-stareishii'],
          ['Интерфакс', 'https://www.interfax.ru/business/1053739']],
  'new': ['BFM', 'https://www.bfm.ru/news/547670'],
  'quote': 'Остальные 5% сохраняются за кипрской Transportation Investments Management, сообщили «Интерфаксу» в компании. '
           'Сумму сделки там не раскрыли. Предполагается, что сервис сохранит основную команду.',
  'why': WHY + 'опора условия о команде (law.terms) и того, что сумма не раскрыта'},
 # ======================================================================= gcc054516 «А Групп»
 {'id': 'gcc054516', 'field': 'title',
  'old': 'Северсталь купила 100% ООО «А Групп» — крупного металлосервисного дистрибьютора',
  'new': '«Северсталь» купила металлотрейдера «А Групп»',
  'quote': '"Северсталь" закрыла сделку по покупке металлотрейдера "А Групп"',
  'why': WHY + 'вторая часть через тире и юрлицо вместо бренда; стандарт «X купил Y» (pipeline/title_standard.py)'},
 # ======================================================================= g91d021c6 Gebr. Heinemann
 {'id': 'g91d021c6', 'field': 'title',
  'old': 'Gebr. Heinemann продала магазины Duty free в Шереметьево и Домодедово Аразу Мехдиеву',
  'new': 'Араз Мехдиев купил у Gebr. Heinemann доли в операторах duty free Домодедово и Шереметьево',
  'quote': 'Немецкая компания Gebr. Heinemann, один из крупнейших мировых операторов беспошлинной торговли, продала свои '
           'доли в двух кипрских компаниях, которые управляли магазинами duty free в московских аэропортах Домодедово и '
           'Шереметьево. Активы приобрел азербайджанский предприниматель Араз Мехдиев',
  'why': WHY + 'стандарт «X купил Y у Z» (pipeline/title_standard.py); продавались доли в кипрских холдингах, а не '
         'магазины'},
 {'id': 'g91d021c6', 'field': 'src',
  'old': [['РБК', 'https://www.rbc.ru/business/31/03/2025/67e51b4e9a7947bd49d4183b'], ['pravo.ru', 'https://pravo.ru/news/258030/']],
  'new': ['Sostav', 'https://www.sostav.ru/publication/gebr-heinemann-prodala-doli-v-biznese-duty-free-v-rossii-74144.html'],
  'quote': 'Весной 2024 года Gebr. Heinemann перестала быть акционером фирмы Rubis Holdings Limited.',
  'why': WHY + 'РБК (первоисточник) из контейнера не открывается (401); Sostav пересказывает его подробно'},
 {'id': 'g91d021c6', 'field': 'src',
  'old': [['РБК', 'https://www.rbc.ru/business/31/03/2025/67e51b4e9a7947bd49d4183b'], ['pravo.ru', 'https://pravo.ru/news/258030/'],
          ['Sostav', 'https://www.sostav.ru/publication/gebr-heinemann-prodala-doli-v-biznese-duty-free-v-rossii-74144.html']],
  'new': ['Fakti.bg', 'https://fakti.bg/en/biznes/960718-german-company-leaves-two-largest-airports-in-moscow'],
  'quote': 'The entrepreneur became a shareholder in the companies back in 2021, when he received 25% in Jullianita '
           'Limited and Rubis Holdings Limited.',
  'why': WHY + 'опора 25% Мехдиева с 2021 года (пересказ РБК)'},
]
