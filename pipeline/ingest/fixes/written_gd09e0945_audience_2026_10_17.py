# -*- coding: utf-8 -*-
"""Дочитывание gd09e0945 (Леста Игры): RB.ru назвал размер аудитории
проектов студии — факта не было ни в одной из прежних правок.

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'gd09e0945',
  'field': 'extra',
  'old': None,
  'new': 'По собственным данным «Леста Игр», в 2025 году у трёх игр студии — «Мир '
         'танков», «Мир кораблей» и Tanks Blitz — было 6,5 млн игроков в месяц.',
  'quote': 'Аудитория проектов «Леста Игр» достигла 6,5 млн человек в месяц в 2025 '
           'году … По собственным данным «Леста Игр», в 2025 году ежемесячная '
           'аудитория её проектов составляла 6,5 млн человек.',
  'why': 'новый факт сверх уже записанного — размер аудитории, RB.ru'},
 {'id': 'gd09e0945',
  'field': 'src',
  'old': [['Frank Media', 'https://frankmedia.ru/310494'],
          ['Коммерсантъ', 'https://www.kommersant.ru/doc/9027870'],
          ['Ведомости', 'https://www.vedomosti.ru/media/articles/2026/10/16/1237602-vladeltsem-gk-lesta'],
          ['CNews', 'https://www.cnews.ru/news/top/2026-10-16_u_natsionalizirovannogo_sozdatelya'],
          ['Коммерсантъ', 'https://www.kommersant.ru/doc/8925020'],
          ['Коммерсантъ', 'https://www.kommersant.ru/doc/7775832'],
          ['Коммерсантъ', 'https://www.kommersant.ru/doc/8534062'],
          ['Frank Media', 'https://frankmedia.ru/303016'],
          ['RB.ru', 'https://rb.ru/news/minfin-rasschityvaet-prodat-razrabotchika-lesta-chastnomu-investoru-sdelku-planiruyut-zakryt-osenyu/'],
          ['RB.ru', 'https://rb.ru/news/ao-dhamma-zainteresovalos-pokupkoj-razrabotchika-igry-mir-tankov-u-gosudarstva-aktiv-ocenili-v-50-mlrd-rublej/']],
  'new': ['RB.ru', 'https://rb.ru/news/gosudarstvo-prodalo-lesta-igry-novyj-vladelec-vlozhit-v-igrovuyu-industriyu-do-10-mlrd/'],
  'quote': 'Аудитория проектов «Леста Игр» достигла 6,5 млн человек в месяц в 2025 году',
  'why': 'источник нового факта об аудитории — добавлен в список'}]
