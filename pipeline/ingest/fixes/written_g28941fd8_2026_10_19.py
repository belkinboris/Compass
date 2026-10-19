# -*- coding: utf-8 -*-
"""Текст карточки g28941fd8, написанный по фактам (write_card.py, WRITING_BRIEF.md).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'g28941fd8',
  'field': 'eco.val',
  'old': '—',
  'new': 'В сумму $207 млн входит непогашенный долг Perfectum примерно на $93 млн, который VEON '
         'берёт на себя. Денежную часть сделки VEON оплатит из собственных средств.',
  'quote': 'Общая сумма сделки - порядка $207 млн, включая принятие на себя непогашенной '
           'финансовой задолженности Perfectum в размере примерно $93 млн … The cash consideration '
           "will be funded from VEON's existing cash resources.",
  'why': 'текст написан по фактам 1, 2 (WRITING_BRIEF.md)'},
 {'id': 'g28941fd8',
  'field': 'eco.rationale',
  'old': '—',
  'new': 'По оценке VEON, сделка увеличит радиочастотный ресурс Beeline Uzbekistan примерно на '
         '50%. Интеграция сетей с действующей сетью Beeline Uzbekistan должна снизить будущие '
         'капитальные и операционные расходы.',
  'quote': 'По оценке VEON, приобретение позволит увеличить объем радиочастотных ресурсов ее '
           'дочерней структуры - Beeline Uzbekistan - примерно на 50% … The combination is also '
           'expected to improve the efficiency of future network investment and generate capital '
           "and operating expenditure synergies through integration with Beeline Uzbekistan's "
           'existing network.',
  'why': 'текст написан по фактам 5, 6 (WRITING_BRIEF.md)'},
 {'id': 'g28941fd8',
  'field': 'law.appr',
  'old': '—',
  'new': 'Регуляторы уже дали добро на сделку. Стороны планируют закрыть её до конца октября 2026 '
         'года.',
  'quote': 'необходимые разрешения регулирующих органов уже получены, завершение сделки ожидается '
           'до конца октября 2026 года',
  'why': 'текст написан по фактам 3 (WRITING_BRIEF.md)'}]
# Записи про eco.target_fin и extra сняты: вторым чтением 19.10.2026 найдено,
# что eco.target_fin несла состав лота (спектр, оборудование), а не финансы
# цели — факт перенесён в eco.share; extra дублировала law.appr/eco.rationale
# без нового факта и глушила имя предмета в посте (has_novelty). Оба поля
# очищены (fix_g28941fd8_clear_2026_10_19.py). Записи здесь не оставлены
# парой old=new=None: already_applied() для None-полей не доходит до проверки
# по отпечатку (review.py) — запись навсегда читалась бы как неприменённая.
# Запись про eco.context снята: сведена в одну запись после второго чтения
# 19.10.2026 — см. written_g28941fd8_2026_10_19_2.py (карточка ещё не
# опубликована: держать несколько промежуточных формулировок поля не нужно).
