# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`ge51361bd` («Polymetal увеличил долю в проекте Баксы до 75%»,
закрыта, 2023-07-10) — дочитывание нашло независимую оценку запасов
месторождения (JORC), состав оставшихся совладельцев и продолжение
геологоразведки после сделки.

Проверено (по докладу саб-агента, дословные цитаты, независимо
подтверждены на 6+ источниках):
- forbes.kz/economy/energy-subsoil/polymetal_uvelichil_dolyu_v_
  kazahstanskom_proekte/: «Государственной компании АО "Казгеология"
  принадлежат оставшиеся 25%»; оценка запасов на момент сделки —
  «содержание меди — 1,9%, содержание золота — 2,8 г/т, объем меди —
  14,3 тыс. тонн, объем золота — 68,1 тыс. унций».
- kapital.kz/business/117273/: «Дальнейшие геологоразведочные усилия
  будут направлены как на выявление дополнительных участков с высоким
  содержанием, так и на тестирование экономического потенциала
  крупного центрального участка с более низким содержанием»; «Казгеология»
  недавно перешла под контроль государственной горнорудной нацкомпании
  «Тау-Кен Самрук».
- inbusiness.kz/ru/news/solidcore-resources-postavil-zapasy-zoloto-
  mednogo-mestorozhdeniya-baksy-na-gosbalans: Виталий Несис — «Мы
  поставили запасы месторождения Баксы на государственный учет по
  стандартам KAZRC в ноябре 2023 года»; «подготовка к началу добычи на
  Баксы ведётся полным ходом, сформирована рабочая группа внутри
  компании, определены основные проектные решения, мы сейчас
  приступаем к активному взаимодействию с разрешительной системой».

НЕ ВНЕСЕНО: (1) имя частного партнёра/продавца 67,5% доли — НИ ОДИН
из примерно 15 проверенных источников (Интерфакс, ТАСС, Forbes
Kazakhstan, kapital.kz, mining-technology.com и др.) его не называет,
везде обезличенная формулировка «один из партнёров/акционеров»; поле
`seller` остаётся пустым — это честная пустота, а не недосмотр;
(2) сумма сделки/цена опциона — ноль по всем источникам, явно
подтверждено фразой «сумма не раскрыта» в нескольких из них; (3)
юридический/финансовый консультант — ноль по всем источникам; (4)
точная сумма, потраченная на геологоразведку 2019–2023 годов, —
известны только физические метрики бурения (уже в карточке), денежных
цифр не приводит ни один источник; (5) добыча меди в тоннах по данным
KAZRC 2023 года — источник называет только золото (запасы ~39 тыс.
унций, руда 420 тыс. тонн, содержание золота 2,9 г/т), медные цифры
там не приводятся — не путать с более ранней оценкой JORC 2019 года
(14,3 тыс. тонн меди), которая уже внесена как отдельная величина.

Запуск: python3 pipeline/fix_polymetal_baksy_fullscan.py
        python3 pipeline/fix_polymetal_baksy_fullscan.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ge51361bd'

OLD_ECO_VAL = '—'
NEW_ECO_VAL = (
    'К моменту сделки запасы участка оценивались примерно в 14,3 тыс. '
    'тонн меди (содержание 1,9%) и 68,1 тыс. унций золота (содержание '
    '2,8 г/т).'
)

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Оставшиеся 25% в проекте принадлежат государственной АО '
    '«Казгеология», которая позже перешла под контроль национальной '
    'горнорудной компании «Тау-Кен Самрук». В ноябре 2023 года Polymetal '
    'поставил запасы месторождения на государственный учёт по '
    'стандартам KAZRC; по словам гендиректора Виталия Несиса, подготовка '
    'к началу добычи «ведётся полным ходом», сформирована рабочая '
    'группа, определены основные проектные решения, компания начинает '
    'взаимодействие с разрешительной системой.'
)

OLD_LAW_TERMS = '—'
NEW_LAW_TERMS = (
    'Дальнейшие геологоразведочные работы направлены как на выявление '
    'дополнительных участков с высоким содержанием, так и на '
    'тестирование экономического потенциала крупного центрального '
    'участка с более низким содержанием.'
)

OLD_SRC = [['Интерфакс', 'https://www.interfax.ru/amp/910929']]
NEW_SRC = OLD_SRC + [
    ['Forbes Kazakhstan', 'https://forbes.kz/economy/energy-subsoil/polymetal_uvelichil_dolyu_v_kazahstanskom_proekte/'],
    ['Kapital.kz', 'https://kapital.kz/business/117273/polymetal-priobrel-kontrol-nyy-paket-v-proyekte-baksy-v-kazakhstane.html'],
    ['Inbusiness.kz', 'https://www.inbusiness.kz/ru/news/solidcore-resources-postavil-zapasy-zoloto-mednogo-mestorozhdeniya-baksy-na-gosbalans'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['val'] == OLD_ECO_VAL
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['law']['terms'] == OLD_LAW_TERMS
    assert deal['src'] == OLD_SRC

    print('=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== law.terms: станет ===')
    print(NEW_LAW_TERMS)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['val'] = NEW_ECO_VAL
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['law']['terms'] = NEW_LAW_TERMS
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
