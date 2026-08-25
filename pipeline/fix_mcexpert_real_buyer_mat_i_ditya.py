# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gddc29a8d: тот же класс
дефекта, что уже описан в CLAUDE.md для БКС/«Форштадт» и S8 Capital/
«Аквариус» — ФАС предварительно одобрила покупателя («Медкапитал»,
структура ГК «Медскан»/«Росатом»), но итоговая сделка реализована
ИНАЧЕ: 22 мая 2025 года 100% ООО «МЦ Эксперт» купила МКПАО «МД Медикал
Груп» (сеть «Мать и дитя») за 8,5 млрд руб., через свои юрлица ООО
«Хавен» (99%) и ООО «Клиника Мать и Дитя» (1%). Продавец — Елена
Латышева (сестра экс-мэра Липецка Евгении Уваркиной), владевшая долями
через ООО «Барель» и ООО «УК Центр Эксперт». Единственный источник
карточки (Telegram-канал @dealsma) знал только про предварительное
согласование ФАС и не отследил, что реальным покупателем стал другой
холдинг — отсюда и заголовок, и профиль-покупатель были неверны.

Профиль «Медкапитал» (g63814c8a) создавался специально под эту сделку
(«Покупатель 20 медицинских центров у ГК «Эксперт»») — описание ложно, а
после правки buyer у профиля не останется ни одной сделки. Удаляется, а
не оставляется как призрак с неверным описанием.

Не через review.py: комбинация фактов из ЧЕТЫРЁХ новых источников
(kommersant.ru, mcclinics.ru, rb.ru, center.business-magazine.online) в
структурных полях (title, buyer, seller, sum, date) — за пределами того,
что review.py вообще проверяет.

Запуск: python3 pipeline/fix_mcexpert_real_buyer_mat_i_ditya.py
        python3 pipeline/fix_mcexpert_real_buyer_mat_i_ditya.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gddc29a8d'
WRONG_BUYER_PROFILE_ID = 'g63814c8a'

OLD_TITLE = 'Медкапитал приобрела 20 медицинских центров ГК Эксперт'
NEW_TITLE = '«Мать и дитя» приобрела 20 медицинских центров ГК «Эксперт»'

OLD_DATE = '2025'
NEW_DATE = '2025-05-22'

OLD_BUYER = 'g63814c8a'
NEW_BUYER = 'mid'

OLD_SELLER = None
NEW_SELLER = 'Елена Латышева'

OLD_SUM = 'Не раскрыта'
NEW_SUM = '8,5 млрд ₽'

OLD_ECO_CONTEXT = (
    'В открытых источниках упоминаются две компании с названием '
    '«Медкапитал». Одна из них зарегистрирована в Екатеринбурге в 2016 '
    'году и занимается продажей фармацевтической продукции (выручка в '
    '2024 году составила чуть более 56 млн рублей, владелец – Алексей '
    'Крутаков). Вторая организация зарегистрирована в феврале 2025 года '
    'в Москве и принадлежит Евгении Горбуновой (занимается деятельностью '
    'холдинговых компаний).'
)
NEW_ECO_CONTEXT = (
    'ФАС предварительно согласовала покупку 99% МЦ «Эксперт» ООО '
    '«Медкапитал» — структуре ГК «Медскан» (частный медицинский холдинг '
    'с участием госкорпорации «Росатом»). Но итоговая сделка была '
    'реализована иначе: актив приобрела МКПАО «МД Медикал Груп» (сеть '
    '«Мать и дитя»), через свои юрлица ООО «Хавен» (99%) и ООО «Клиника '
    'Мать и Дитя» (1%). Продавцом выступала Елена Латышева — сестра '
    'экс-мэра Липецка Евгении Уваркиной, владевшая долями через ООО '
    '«Барель» и ООО «УК Центр Эксперт». После продажи ГК «Эксперт» '
    'сосредоточилась на лучевой диагностике под брендом «МРТ-Эксперт» '
    '(43 диагностических центра).'
)

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'ООО «Хавен», принадлежащее МД Медикал Груп, получило 99% в «МЦ '
    'Эксперт», оставшийся 1% — у ООО «Клиника Мать и Дитя» (также входит '
    'в МД Медикал Груп). Сумма оплачена собственными денежными '
    'средствами МД Медикал Груп, которая начала консолидировать периметр '
    'сделки в своей отчётности с мая 2025 года.'
)

OLD_LAW_APPR = (
    'ФАС России одобрила приобретение компанией Медкапитал 99% долей в '
    'ООО МЦ Эксперт (входит в ГК Эксперт).'
)
NEW_LAW_APPR = (
    'ФАС России предварительно одобрила приобретение 99% долей в ООО '
    '«МЦ Эксперт» другому кандидату — ООО «Медкапитал» (структура ГК '
    '«Медскан»/«Росатом»); эта сделка не состоялась, актив реально купила '
    'МД Медикал Груп. Отдельного публичного решения ФАС по сделке с МД '
    'Медикал Груп не найдено.'
)

OLD_EXTRA = (
    'ФАС России одобрила приобретение компанией Медкапитал 99% долей в '
    'ООО МЦ Эксперт (входит в ГК Эксперт). Сделка касается 20 '
    'медицинских центров в 12 городах России, включая Курск, Воронеж и '
    'Борисоглебск. (Федеральная антимонопольная служба России '
    'согласовала сделку)'
)
NEW_EXTRA = (
    'ФАС предварительно согласовывала покупку структуре ГК «Медскан»/'
    '«Росатом» (ООО «Медкапитал»), но реальным покупателем стала сеть '
    '«Мать и дитя» (МД Медикал Груп). Сделка касается 20 медицинских '
    'центров в 12 городах России, включая Курск, Воронеж и Борисоглебск.'
)

NEW_SRC = [
    ['kommersant.ru', 'https://www.kommersant.ru/doc/7738819'],
    ['mcclinics.ru', 'https://www.mcclinics.ru/media/news/Expert-deal/'],
    ['rb.ru', 'https://rb.ru/news/mat-i-ditya-kupila/'],
    ['center.business-magazine.online', 'https://center.business-magazine.online/fn_1662721.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['title'] == OLD_TITLE
    assert deal['date'] == OLD_DATE
    assert deal['buyer'] == OLD_BUYER
    assert deal.get('seller') == OLD_SELLER
    assert deal['sum'] == OLD_SUM
    assert deal['eco']['sum'] == OLD_SUM
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['law']['appr'] == OLD_LAW_APPR
    assert deal['extra'] == OLD_EXTRA
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'
    assert 'mid' in data['companies']
    assert WRONG_BUYER_PROFILE_ID in data['companies']

    other_refs = [d['id'] for d in data['deals']
                  if d['id'] != DEAL_ID
                  and WRONG_BUYER_PROFILE_ID in (d.get('buyer'), d.get('seller_id'), d.get('target'))]
    assert not other_refs, f'профиль {WRONG_BUYER_PROFILE_ID} используется ещё где-то: {other_refs}'

    print('=== title ===', NEW_TITLE)
    print('=== date ===', NEW_DATE)
    print('=== buyer ===', NEW_BUYER)
    print('=== seller ===', NEW_SELLER)
    print('=== sum / eco.sum ===', NEW_SUM)
    print('=== eco.context ===')
    print(NEW_ECO_CONTEXT)
    print('=== law.struct ===')
    print(NEW_LAW_STRUCT)
    print('=== law.appr ===')
    print(NEW_LAW_APPR)
    print('=== extra ===')
    print(NEW_EXTRA)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)
    print('=== удаляется профиль ===', WRONG_BUYER_PROFILE_ID, data['companies'][WRONG_BUYER_PROFILE_ID]['name'])

    if write:
        deal['title'] = NEW_TITLE
        deal['date'] = NEW_DATE
        deal['buyer'] = NEW_BUYER
        deal['seller'] = NEW_SELLER
        deal['seller_src'] = 'text'
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_SUM
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['law']['appr'] = NEW_LAW_APPR
        deal['extra'] = NEW_EXTRA
        deal['src'].extend(NEW_SRC)
        del data['companies'][WRONG_BUYER_PROFILE_ID]
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
