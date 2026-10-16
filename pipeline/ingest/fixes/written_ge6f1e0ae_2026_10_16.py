# -*- coding: utf-8 -*-
"""Текст карточки ge6f1e0ae, написанный по фактам (write_card.py, WRITING_BRIEF.md).

Запуск: python3 pipeline/ingest/review.py --write
"""

FIXES = [{'id': 'ge6f1e0ae',
  'field': 'eco.context',
  'old': 'По данным на 7 апреля 2025 года доля National City Nominees Limited (Великобритания) в '
         'уставном капитале Globaltrans составляла 37,84%, Aqniet Holding Group ltd (Казахстан) — '
         '13,43%, по 11,54% — у Marigold Investments Ltd (ОАЭ) и Onyx Investments ltd DMCC (ОАЭ), '
         'ещё 10,87% — у KSP Capital Asset Management LLC (Россия, Д.У. ЗПИФ «Инвесттранс») и '
         '5,08% — у Litten Investments LTD DMCC (ОАЭ).',
  'new': 'На 7 апреля 2025 года 37,84% Globaltrans принадлежали National City Nominees Limited '
         '(Великобритания). Ещё 13,43% было у Aqniet Holding Group ltd (Казахстан), по 11,54% — у '
         'Marigold Investments Ltd и Onyx Investments ltd DMCC (обе из ОАЭ). KSP Capital Asset '
         'Management LLC (Россия), доверительный управляющий ЗПИФ «Инвесттранс», владела 10,87%, '
         'Litten Investments LTD DMCC (ОАЭ) — 5,08%.',
  'quote': 'По данным на 7 апреля 2025 года доля National City Nominees Limited (Великобритания) в '
           'уставном капитале Globaltrans составляла 37,84% … Aqniet Holding Group ltd (Казахстан) '
           '— 13,43% … по 11,54% — у Marigold Investments Ltd (ОАЭ) и Onyx Investments ltd DMCC '
           '(ОАЭ) … ещё 10,87% — у KSP Capital Asset Management LLC (Россия, Д.У. ЗПИФ '
           '«Инвесттранс») … 5,08% — у Litten Investments LTD DMCC (ОАЭ)',
  'why': 'текст написан по фактам 1, 2, 3, 4, 5 (WRITING_BRIEF.md)'},
 {'id': 'ge6f1e0ae',
  'field': 'eco.target_fin',
  'old': 'Общий парк компании на конец 2024 года составлял 63 584 единицы подвижного состава.',
  'new': 'Парк подвижного состава на конец 2024 года — 63 584 единицы.',
  'quote': 'Общий парк компании на конец 2024 года составлял 63 584 единицы подвижного состава.',
  'why': 'текст написан по фактам 6 (WRITING_BRIEF.md)'},
 {'id': 'ge6f1e0ae',
  'field': 'eco.val',
  'old': 'По данным компании, покупная цена доли БТС составила $247,9 млн, доли ГТИМ — $136,4 млн, '
         'акций НПК — $260,3 млн, акций УВК — $8,7 млн, акций Adaptive — $1; вознаграждение за '
         'уступку прав по договору займа между Globaltrans и ГТИМ — $94,056 млн, между Globaltrans '
         'и Adaptive — $19,4 млн.',
  'new': 'По данным компании, цена складывается из нескольких частей. Доля БТС стоит $247,9 млн, '
         'доля ГТИМ — $136,4 млн; акции НПК — $260,3 млн, УВК — $8,7 млн, а акции Adaptive проданы '
         'за $1. Отдельно оплачивается уступка прав по займам Globaltrans: $94,056 млн — по займу '
         'ГТИМ и $19,4 млн — по займу Adaptive.',
  'quote': 'По данным компании, покупная цена доли БТС составила $247,9 млн … доли ГТИМ — $136,4 '
           'млн … акций НПК — $260,3 млн … акций УВК — $8,7 млн … акций Adaptive — $1 … '
           'вознаграждение за уступку прав по договору займа между Globaltrans и ГТИМ — $94,056 '
           'млн … между Globaltrans и Adaptive — $19,4 млн',
  'why': 'текст написан по фактам 7, 8, 9, 10, 11, 12, 13 (WRITING_BRIEF.md)'}]
