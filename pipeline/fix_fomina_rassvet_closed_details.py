# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g64e64b49` («Сеть «Клиника Фомина» получает контроль в медицинском
центре «Рассвет»», статус «Обсуждается», 2023) — сделка закрылась, но
заголовок и статус остались в форме предположения.

Проверено (по докладу саб-агента, дословные цитаты):
- vademec.ru/news/2023/05/25/klinika-fomina-priobrela-89-aktsiy-
  stolichnogo-medtsentra-rassvet/: сделка закрыта 22 мая 2023 года;
  «Клиника Фомина» получила «89-процентной доли» ООО «МСЧ 14»
  (управляет «Рассветом»); «в этом году в «Рассвет» планируют
  дополнительно вложить 100 млн рублей, а также открыть круглосуточный
  стационар».
- kommersant.ru/doc/6001292 (источник карточки, перепрочитан полностью):
  «После сделки «Рассвет» сохранит бренд и команду специалистов»;
  «выручку «Рассвета» планируется увеличить до 400 млн руб., а в
  течение трёх лет довести до 1 млрд руб.»; совладелец Евгений Бойченко
  — «полгода искали профильного инвестора для дальнейшего развития
  центра».
- fomin-clinic.ru/blog/set-klinika-fomina-poluchila-kontrol-v-tsentre-
  rassvet/: гендиректор сети объясняет мотив диверсификацией — «профильный
  для «Клиники Фомина» сегмент женского здоровья ограничен и отличается
  сильной конкуренцией».
- gxpnews.net/2025/02: по состоянию на начало 2025 года бренд
  «Рассвет» жив внутри сети — «сеть объединяет 25 медицинских центров
  в 15 регионах России, включая... клинику «Рассвет» в Москве».

НЕ ВНЕСЕНО: (1) состав миноритариев ПОСЛЕ сделки — источники
расходятся: Коммерсантъ пишет, что Бойченко и Парамонов «сохранят
доли», а Vademecum со ссылкой на ЕГРЮЛ называет итоговую структуру
«КДФ Групп 89%, Алексей Парамонов 10%, Евгений Бойченко 1%» и
утверждает, что весь прежний состав (включая Ларису Подгорную,
Татьяну Бардину, Сергея Парамонова, Котэ Гоголадзе) вышел из
учредителей, — расхождение не разрешено, точный состав долей после
сделки не вносится; (2) юридический/финансовый консультант — ноль по
обоим источникам; (3) финансовые показатели сети «Клиника Фомина» за
2024-2025 годы (выручка выросла на десятки процентов, планы IPO на
2027 год) — это уже показатели всей компании, а не эффект конкретно
этой сделки, не вносится в карточку одной сделки.

Запуск: python3 pipeline/fix_fomina_rassvet_closed_details.py
        python3 pipeline/fix_fomina_rassvet_closed_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g64e64b49'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_DATE = '2023'
NEW_DATE = '2023-05-22'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Сделка закрыта 22 мая 2023 года: «Клиника Фомина» получила 89% '
    'долей ООО «МСЧ 14», управляющего медцентром «Рассвет».'
)

OLD_LAW_TERMS = '—'
NEW_LAW_TERMS = (
    'После сделки «Рассвет» сохранит бренд и команду специалистов. В '
    '2023 году в центр планируется дополнительно вложить 100 млн ₽ и '
    'открыть круглосуточный стационар; выручку «Рассвета» рассчитывают '
    'увеличить до 400 млн ₽ в этом году и до 1 млрд ₽ в течение трёх '
    'лет.'
)

OLD_ECO_RATIONALE = (
    'Гендиректор «Клиники Фомина» Дмитрий Фомин рассчитывает, что '
    'покупка «Рассвета» ускорит развитие многопрофильных услуг сети '
    'и усилит её позиции на московском рынке.'
)
NEW_ECO_RATIONALE = (
    OLD_ECO_RATIONALE + ' Покупка также диверсифицирует бизнес: '
    'профильный для «Клиники Фомина» сегмент женского здоровья '
    'ограничен и отличается сильной конкуренцией.'
)

OLD_ECO_CONTEXT = (
    '«Клиника Фомина» работает с 2011 года и специализируется на '
    'женском здоровье. С учётом «Рассвета» в сеть входят 20 клиник в '
    '12 регионах. Выручка сети в 2022 году составила 2,55 млрд ₽, на '
    'текущий год в компании прогнозируют 5 млрд ₽.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' По состоянию на начало 2025 года бренд '
    '«Рассвет» сохраняется внутри выросшей сети (уже 25 центров в 15 '
    'регионах).'
)

OLD_SRC = [['Коммерсантъ', 'https://www.kommersant.ru/doc/6001292']]
NEW_SRC = OLD_SRC + [
    ['Vademecum', 'https://vademec.ru/news/2023/05/25/klinika-fomina-priobrela-89-aktsiy-stolichnogo-medtsentra-rassvet/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['date'] == OLD_DATE
    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['law']['terms'] == OLD_LAW_TERMS
    assert deal['eco']['rationale'] == OLD_ECO_RATIONALE
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== date: станет ===')
    print(NEW_DATE)
    print('\n=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== law.terms: станет ===')
    print(NEW_LAW_TERMS)
    print('\n=== eco.rationale: станет ===')
    print(NEW_ECO_RATIONALE)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['status'] = NEW_STATUS
        deal['date'] = NEW_DATE
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['law']['terms'] = NEW_LAW_TERMS
        deal['eco']['rationale'] = NEW_ECO_RATIONALE
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
