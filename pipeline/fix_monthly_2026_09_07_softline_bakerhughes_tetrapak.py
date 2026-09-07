# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), три карточки
июля-августа 2022 года — все три уже описывали фактически состоявшийся
переход (структура/этап закрытия названы в тексте), но `status` не был
проставлен. Проверено ЛИЧНО прямым WebFetch.

1) c43f195a5 (Softline/«Ваш платежный проводник», август 2022): сделка
   закрылась в июле 2022 года. Личный WebFetch (rb.ru): в мае 2025 года
   сменился гендиректор структуры (Александр Шпет вместо Евгения
   Чертихина), а сама компания в ноябре 2024 года вошла в новый
   зонтичный бренд группы Softline — «Сомерс» — вместе с CrestWave и
   Sky Technologies, сохранив юрлицо и название продукта. Выручка ВПП
   в 2024 году выросла на 57% до 162,3 млн ₽. `status` → «Закрыта».

2) cb33a285d (Baker Hughes/буровой сегмент, август 2022): сделка
   закрылась в ноябре 2022 года (после указа президента от 4 ноября).
   Личный WebFetch (interfax.ru/business/881985): собственники новой
   структуры — три бывших топ-менеджера Baker Hughes Russia (Александр
   Монахов, Алексей Аникеев, Наталия Айдарова, поровну). Личный WebFetch
   (interfax.ru/business/876488): тюменский завод продолжил работу под
   брендом «Технологии ОФС». `status` → «Закрыта».

3) c1659a21f (Tetra Pak/завод в Лобне, июль 2022): сделка закрылась,
   юрлицо (АО «Тетра Пак») переименовано в АО «Упаковочные системы».
   Личный WebFetch (sostav.ru): производство полноцветной упаковки
   возобновлено с 1 октября 2022 года. `status` → «Закрыта».

Запуск: python3 pipeline/fix_monthly_2026_09_07_softline_bakerhughes_tetrapak.py
        python3 pipeline/fix_monthly_2026_09_07_softline_bakerhughes_tetrapak.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SL_ID = 'c43f195a5'
SL_OLD_STATUS = None
SL_NEW_STATUS = 'Закрыта'
SL_OLD_CONTEXT = (
    'Группа «Ваш платежный проводник» основана в 2011 году экспертами '
    'из сферы финансовых технологий и телекоммуникаций.'
)
SL_NEW_CONTEXT = (
    SL_OLD_CONTEXT + ' В ноябре 2024 года ВПП вошла в новый зонтичный '
    'бренд группы Softline — «Сомерс» — вместе с двумя другими '
    'финтех-активами группы (CrestWave, Sky Technologies), сохранив '
    'юрлицо и название продукта. В мае 2025 года сменился гендиректор '
    'структуры. Выручка ВПП в 2024 году выросла на 57%, до 162,3 млн ₽.'
)

BH_ID = 'cb33a285d'
BH_OLD_STATUS = None
BH_NEW_STATUS = 'Закрыта'
BH_OLD_TERMS = (
    'Baker Hughes ожидает закрытия сделки до конца года, она потребует '
    'одобрения местных властей.'
)
BH_NEW_TERMS = (
    BH_OLD_TERMS + ' Сделка закрылась в ноябре 2022 года, после указа '
    'президента от 4 ноября. Собственники новой структуры — три '
    'бывших топ-менеджера Baker Hughes Russia (Александр Монахов, '
    'Алексей Аникеев, Наталия Айдарова, доли поровну). Тюменский завод '
    'продолжил работу под брендом «Технологии ОФС», выпускающим '
    'нефтепогружной кабель и оборудование для заканчивания скважин; '
    'позже компания вложила более 3 млрд ₽ в новое производство '
    'роторных управляемых систем там же.'
)

TP_ID = 'c1659a21f'
TP_OLD_STATUS = None
TP_NEW_STATUS = 'Закрыта'
TP_OLD_CONTEXT = 'Статус на момент публикации: в процессе закрытия.'
TP_NEW_CONTEXT = (
    'Сделка закрылась: АО «Тетра Пак» переименовано в АО «Упаковочные '
    'системы», единственный акционер — ООО «Итон Инвестментс» (создано '
    'в июле 2022 года, паритетно принадлежит Александру Криволапову и '
    'Игорю Акимову, бывшим руководителям АО «Тетра Пак»), сумма сделки '
    'составила 1 евро. Производство полноцветной упаковки на заводе в '
    'Лобне возобновлено с 1 октября 2022 года.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    sl = by_id[SL_ID]
    bh = by_id[BH_ID]
    tp = by_id[TP_ID]

    assert sl.get('status') == SL_OLD_STATUS
    assert sl['eco']['context'] == SL_OLD_CONTEXT
    assert bh.get('status') == BH_OLD_STATUS
    assert bh['law']['terms'] == BH_OLD_TERMS
    assert tp.get('status') == TP_OLD_STATUS
    assert tp['eco']['context'] == TP_OLD_CONTEXT

    print('=== c43f195a5: status ===', SL_NEW_STATUS)
    print('=== c43f195a5: eco.context ===')
    print(SL_NEW_CONTEXT)
    print()
    print('=== cb33a285d: status ===', BH_NEW_STATUS)
    print('=== cb33a285d: law.terms ===')
    print(BH_NEW_TERMS)
    print()
    print('=== c1659a21f: status ===', TP_NEW_STATUS)
    print('=== c1659a21f: eco.context ===')
    print(TP_NEW_CONTEXT)

    if write:
        sl['status'] = SL_NEW_STATUS
        sl['eco']['context'] = SL_NEW_CONTEXT
        bh['status'] = BH_NEW_STATUS
        bh['law']['terms'] = BH_NEW_TERMS
        tp['status'] = TP_NEW_STATUS
        tp['eco']['context'] = TP_NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
