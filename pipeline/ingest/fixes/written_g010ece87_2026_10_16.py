# -*- coding: utf-8 -*-
"""Текст карточки g010ece87, написанный по фактам (write_card.py, WRITING_BRIEF.md).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'g010ece87',
  'field': 'eco.context',
  'old': 'Черногорский Adriatic Bank, купивший сербский банк, основан в 2016 году. Сначала он '
         'принадлежал Azmont Investment — структуре азербайджанской инвестиционной компании '
         'Azerbaijan Global Investments. В 2020 году Azmont Investment продал черногорский банк '
         'американской Adriatic Capital. Сделка закрылась в апреле 2023 года, а с 1 сентября 2023 '
         'года сербский банк официально сменил вывеску — Expobank A.D. Belgrade стал называться '
         'Adriatic Bank A.D. Beograd.',
  'new': 'Основанный в 2016 черногорский Adriatic Bank поначалу контролировала Azmont Investment '
         'из структуры азербайджанской Azerbaijan Global Investments, а в 2020 банк перешёл к '
         'американской Adriatic Capital. Сделку по сербскому банку закрыли в апреле 2023, и с 1 '
         'сентября 2023 он называется Adriatic Bank A.D. Beograd вместо Expobank A.D. Belgrade.',
  'quote': 'Черногорский Adriatic Bank, купивший сербский банк, основан в 2016 году. … Сначала он '
           'принадлежал Azmont Investment — структуре азербайджанской инвестиционной компании '
           'Azerbaijan Global Investments. … В 2020 году Azmont Investment продал черногорский '
           'банк американской Adriatic Capital. … Сделка закрылась в апреле 2023 года … с 1 '
           'сентября 2023 года сербский банк официально сменил вывеску — Expobank A.D. Belgrade '
           'стал называться Adriatic Bank A.D. Beograd',
  'why': 'текст написан по фактам 1, 2, 3, 4, 5 (WRITING_BRIEF.md)'},
 {'id': 'g010ece87',
  'field': 'law.struct',
  'old': 'Expobank A.D. Belgrade принадлежал чешскому Expobank CZ. В сентябре 2022 года Игорь Ким '
         'закрыл сделку по продаже банка в Чехии местному игроку Creditas, и сербская «дочка» '
         'перешла в собственность российского Экспобанка.',
  'new': 'Сербская дочка досталась российскому Экспобанку после того, как в сентябре 2022 Игорь '
         'Ким закрыл продажу её прежнего владельца — чешского Expobank CZ — местной Creditas.',
  'quote': 'Expobank A.D. Belgrade принадлежал чешскому Expobank CZ. … В сентябре 2022 года Игорь '
           'Ким закрыл сделку по продаже банка в Чехии местному игроку Creditas … и сербская '
           '«дочка» перешла в собственность российского Экспобанка',
  'why': 'текст написан по фактам 6, 7, 8 (WRITING_BRIEF.md)'}]
