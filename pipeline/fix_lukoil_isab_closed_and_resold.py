# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g547ff4b8` («ЛУКОЙЛ продаёт нефтеперерабатывающий завод ISAB в Италии
группе G.O.I. ENERGY») несла явное внутреннее противоречие: статус
«Обсуждается» на дату 2022-12-01, а собственные `law.struct`/`law.appr`
уже говорили в ПРОШЕДШЕМ времени («ЗАКРЫЛА сделку», «ВЫПОЛНИЛА
отлагательные условия») — эти два поля дописаны позже из более
позднего материала, чем единственный источник в `src` (kommersant.ru,
09.01.2023, описывает только объявление и план закрыть «до конца марта
2023 года»), но статус и дата карточки не были обновлены следом.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- lukoil.ru/PressCenter/Pressreleases/Pressrelease/lukoil-zakryl-sdelku-po-prodazhe-npz-isab-v-italii
  (4 мая 2023 года): «ПАО "ЛУКОЙЛ" сообщает, что LITASCO S.A., 100%
  дочернее общество Группы "ЛУКОЙЛ", и G.O.I. ENERGY S.r.l. ... закрыли
  сделку по продаже ISAB S.r.l. ... G.O.I. ENERGY после выполнения
  отлагательных условий, включая получение необходимых согласований со
  стороны итальянских властей»; «Инвесторы G.O.I. ENERGY владеют
  контрольным пакетом BAZAN GROUP, одной из крупнейших энергетических
  компаний Израиля»;
- goi.energy/?page_id=944: «BonelliErede acted as GOI's legal advisor»,
  «Ernst & Young acted as its financial advisor»; «G.O.I. Energy
  [is] the energy sector arm of the ARGUS New Energy Fund» (кипрский
  фонд); совет директоров ISAB — «Chairman Angelo Taraborelli,
  Vice-Chairman Michael Bobrov and Directors Ioannis Psichogios and
  Massimo Nicolazzi»;
- hydrocarbonengineering.com/refining/15052026/ludoil-energy-signs-agreement-to-acquire-isab
  (май 2026): Ludoil Capital подписал соглашение о покупке доли в ISAB
  у G.O.I. Energy; первый этап — «a 51% stake», требует прохождения
  итальянского Golden Power и антимонопольного согласования; цена не
  раскрыта.

Статус переведён в «Закрыта», дата — в дату реального закрытия
(2023-05-04), а не объявления (2022-12-01, дата единственного
имевшегося источника).

НЕ ВНЕСЕНО: (1) официальная финальная сумма — не раскрыта ни ЛУКОЙЛом,
ни G.O.I. Energy ни тогда, ни позже; оценка €1,5 млрд остаётся именно
оценкой СМИ (Reuters/Financial Times), а не согласованной ценой —
поле `sum` не менялось; (2) конфликт между Economou (крупнейший
инвестор Argus/G.O.I.) и Trafigura, кризисная процедура завода в
2024-2025 годах и конкретные цифры о долге/убытках — саб-агент нашёл
их только на источниках сомнительного качества (не проверены
авторитетными изданиями), не вносится без отдельной проверки; (3)
консультанты ЛУКОЙЛ/Litasco — не названы ни в одном источнике; (4)
цена перепродажи Ludoil Energy (2026) — прямо не раскрыта.

Запуск: python3 pipeline/fix_lukoil_isab_closed_and_resold.py
        python3 pipeline/fix_lukoil_isab_closed_and_resold.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g547ff4b8'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_DATE = '2022-12-01'
NEW_DATE = '2023-05-04'

OLD_ECO_CONTEXT = (
    'Из-за нерешённых проблем с кредитованием поставки нероссийской '
    'нефти на НПЗ были ограничены. В последние месяцы ISAB получал '
    'почти всю сырую нефть напрямую от ЛУКОЙЛа.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Сделка закрылась 4 мая 2023 года — «после '
    'выполнения отлагательных условий, включая получение необходимых '
    'согласований со стороны итальянских властей». Юридическим '
    'консультантом G.O.I. Energy выступила BonelliErede, финансовым — '
    'Ernst & Young; сама G.O.I. Energy — подразделение кипрского фонда '
    'Argus New Energy Fund, её инвесторы контролируют израильскую '
    'BAZAN GROUP. В мае 2026 года завод перепродан дальше: G.O.I. '
    'Energy договорилась о продаже итальянской Ludoil Capital, первый '
    'этап сделки — 51% доли, цена не раскрыта.'
)

OLD_SRC = [['Коммерсантъ', 'https://www.kommersant.ru/doc/5759356']]
NEW_SRC = OLD_SRC + [
    ['ЛУКОЙЛ', 'https://lukoil.ru/PressCenter/Pressreleases/Pressrelease/lukoil-zakryl-sdelku-po-prodazhe-npz-isab-v-italii'],
    ['GOI Energy', 'https://goi.energy/?page_id=944'],
    ['Hydrocarbon Engineering', 'https://www.hydrocarbonengineering.com/refining/15052026/ludoil-energy-signs-agreement-to-acquire-isab'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['date'] == OLD_DATE
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== date: станет ===')
    print(NEW_DATE)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['status'] = NEW_STATUS
        deal['date'] = NEW_DATE
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
