# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF) — новые источники, найденные
дельта-поиском 24 августа 2026 для g139db8c2 (S8 Capital/«МТ-Интеграция»/
«Аквариус», факты в eco.context —
fix_akvarius_mt_integration_denial_context.py) и g4fc7af86 (Ipsos SA/
«Ипсос Комкон», дата закрытия и структура СП —
fix_ipsos_comcon_closing_date.py, fix_ipsos_comcon_structure_context.py).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [
    dict(id='g139db8c2', field='src', old=None,
         new=['ermolaevv.ru', 'https://ermolaevv.ru/tpost/0ri3as2y11-prodazha-kompanii-akvarius-zagadochnaya'],
         quote='Информация о входе ГК «МТ-Интеграция» в состав акционеров '
               'группы компаний «Аквариус» не соответствует '
               'действительности.',
         why='опровержение МТ-Интеграции'),
    dict(id='g139db8c2', field='src', old=None,
         new=['CTA.ru (со ссылкой на CNews)', 'https://www.cta.ru/news/cta/182329.html'],
         quote='Холдинг S8 Capital, известный как оператор лотерей '
               '«Столото», выделил компании 5 млрд руб. на выплату '
               'зарплат и урегулирование судебных исков.',
         why='экстренное финансирование и продолжающееся упоминание '
             'обеих компаний как совладельцев после опровержения'),
    dict(id='g139db8c2', field='src', old=None,
         new=['Mergers.ru', 'https://mergers.ru/news/Gruppa-kompanij-Maksima-i-S8-Capital-stanut-sovladelcami-Akvariusa-85755'],
         quote='Помимо «Сберинвеста» крупные доли «Аквариуса» '
               'принадлежали Алексею Калинину и президенту группы '
               'Владимиру Степанову',
         why='фон прежних владельцев предмета сделки'),
    dict(id='g4fc7af86', field='src', old=None,
         new=['Ipsos SA (официальный пресс-релиз)', 'https://www.investegate.co.uk/announcement/gnw/ipsos-sa--0ka3/-press-release-sale-of-80-of-ipsos-comcon-l-/9451927'],
         quote="Ipsos SA' Board of Directors announces the Closing of "
               "the sale of 80% of Ipsos Comcon LLC",
         why='источник даты закрытия и структуры СП'),
]
