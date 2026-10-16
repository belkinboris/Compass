# -*- coding: utf-8 -*-
"""Текст карточки g9d134cf4, написанный по фактам (write_card.py, WRITING_BRIEF.md).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'g9d134cf4',
  'field': 'law.struct',
  'old': 'По годовому отчёту HeadHunter за 2021 год (опубликован в апреле 2022 года), Elbrus '
         'Capital через Highworld Investments Limited владела 31,9% HeadHunter, ещё 8,7% — Goldman '
         'Sachs через ELQ Investors VIII Limited.',
  'new': 'Elbrus Capital владела 31,9% HeadHunter через Highworld Investments Limited — так '
         'указано в годовом отчёте компании за 2021 год, вышедшем в апреле 2022 года. Ещё 8,7% '
         'было у Goldman Sachs через ELQ Investors VIII Limited.',
  'quote': 'По годовому отчёту HeadHunter за 2021 год (опубликован в апреле 2022 года), Elbrus '
           'Capital через Highworld Investments Limited владела 31,9% HeadHunter … ещё 8,7% — '
           'Goldman Sachs через ELQ Investors VIII Limited.',
  'why': 'текст написан по фактам 1, 2 (WRITING_BRIEF.md)'},
 {'id': 'g9d134cf4',
  'field': 'law.terms',
  'old': 'Ещё до IPO HeadHunter Таврин, Elbrus Capital и Goldman Sachs заключили договор о '
         'преимущественном праве на выкуп рекрутингового сервиса. Таврин получил это право, '
         'поскольку не реализовал опцион на выкуп HeadHunter, полученный от Mail.ru Group (сейчас '
         'VK) при продаже интернет-холдингу своей доли «ВКонтакте» в 2014 году.',
  'new': 'У Таврина было преимущественное право выкупа сервиса: до IPO HeadHunter он подписал об '
         'этом договор с Elbrus Capital и Goldman Sachs. Право он получил взамен нереализованного '
         'опциона на выкуп HeadHunter у Mail.ru Group (ныне VK). Этот опцион ему дали в 2014 году, '
         'когда он продавал Mail.ru Group свою долю «ВКонтакте».',
  'quote': 'Ещё до IPO HeadHunter Таврин, Elbrus Capital и Goldman Sachs заключили договор о '
           'преимущественном праве на выкуп рекрутингового сервиса. … Таврин получил это право, '
           'поскольку не реализовал опцион на выкуп HeadHunter, полученный от Mail.ru Group '
           '(сейчас VK) … при продаже интернет-холдингу своей доли «ВКонтакте» в 2014 году.',
  'why': 'текст написан по фактам 3, 4, 5 (WRITING_BRIEF.md)'}]
