# -*- coding: utf-8 -*-
"""Вычитка, марафон 12 ноября 2026, партия m030, вторая часть: правки, которые не ложатся в таблицу FIXES.

Что и почему:
  * gfe21a083 — дата 1 июля 2024 без опоры: «Ъ» и Vademecum (октябрь 2024) дня не дают — дата годом. В ЕГРЮЛ
    ООО «Опека-Групп» доли перешли ООО «Опека-МСК» записью 11.05.2021; продажа ли это — источники не говорят,
    а база начинается с 2022 года. Описание профиля Алексея Маврина («при кредите Сбербанка выкупил … акций»)
    без опоры — переписано.
  * gaa59d3a1 — продавец по реестру и «Ъ» — АО «Тетра» (профиль g59b505fe), а не его бенефициар Евгений
    Туголуков; дата — 25.06.2024 (выход АО «Тетра» из ООО «Дон Агро» по ЕГРЮЛ).
  * g428f6180 — предмета не было: европейские заводы «Технониколя»; дата 1 июля без опоры — годом.
  * gd96d269e — продавцом стоял «Росатом»: по WNN компанию продал конкурсный управляющий Nukem Technologies GmbH.

Отдельный файл, а не дописка к reread_oneoff_m030.py: тот уже записан и закоммичен.
Запуск: python3 pipeline/archive/2026-11/reread_oneoff_m030_b.py [--write]
Без ключа — сухой прогон. База перечитывается прямо перед записью; повторный запуск — «уже применено».
Вычитка, марафон 12 ноября 2026, партия m030: правки, которые не ложатся в таблицу FIXES.

Что и почему:
  * gb70b4830 — описание профиля «Владимирского стандарта» называло выручку ГАП «Ресурс» «около 100 млрд ₽»
    (ни один источник этого не пишет) и пересказывало сделку: переписано родом занятий.
  * gefb52584 — продавец по истории участников ЕГРЮЛ ООО «Трансхим» (ИНН 7107136141): 08.08.2024 вышли
    ООО «Дезимпэкс» (50%) и АО «Новопесчанское» (50%); в схеме стоял продюсер Александр Достман —
    бенефициар «Дезимпэкса», а не участник. Дата: 100% у ООО «Оптима Инвест» — запись 21.08.2024
    («Ъ»: «в конце августа»), а не 1 августа. Цитата реестра — в fact_log.
  * ga3e353b1 — продавец снят таблицей правок (Кравцов сохранил 50%); где искали — в accepted_notes.
  * ge292671d — отрасль «Пищепром и напитки» → «Потребительские товары» (туалетная бумага, салфетки):
    отрасль — классификация по предмету, а не факт статьи (docs/card_parties.md, «Отрасль»).
  * g59fbdbf8 — продавцом стояла ЯТЭК (учредитель ЯГПК в 2017 году); по ЕГРЮЛ долю 09.07.2024 передало
    ООО «Глобал Метал Трейдинг», державшее ее с 28.06.2024 (до него — ООО «А-ТЭК»). EastRussia называет ЯТЭК —
    эта версия оставлена в контексте.
  * g941f2b2b — дата 9 июля 2024 без опоры (Интерфакс 11.07: «в июле завершило»): дня нет — дата годом
    (docs/card_status_dates.md); где искали продавца — в accepted_notes.
  * gfe151394 — продавец снят таблицей правок (по реестру Файзуленова вышла из общества в 2022 году) — почему, в
    accepted_notes; описание профиля ООО «Кэрифай» пересказывало сделку — переписано родом занятий.

Запуск: python3 pipeline/archive/2026-11/reread_oneoff_m030.py [--write]
Без ключа — сухой прогон. База перечитывается прямо перед записью; повторный запуск — «уже применено».
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка m030, 12.11.2026'
REG = 'https://projectcompass.ru/api/companies/%s/fns'


def card_edits(by, comps, log):
    c = by['gfe21a083']
    if c.get('date') != '2024':
        assert c.get('date') == '2024-07-01', c.get('date')
        c['date'] = '2024'
        fact_edit_guard.log(c, 'date', '2024',
                            '«Ъ», 30.10.2024: «Совладельцы … «Валента Фарм» вышли из капитала ООО «Опека-групп» … Олег '
                            'Кедровский через представителя пояснил “Ъ”, что совладельцы продали свои доли» — дня сделки '
                            'нет; 1 июля — без опоры. (В ЕГРЮЛ ООО «Опека-Групп» доли перешли ООО «Опека-МСК» записью '
                            '11.05.2021 — продажей ли была эта запись, источники не говорят.)',
                            'https://www.kommersant.ru/doc/7266558', BY)
        log.append('gfe21a083 date')
    p = comps.get('g678e182a') or {}
    new = 'Основатель сети пансионатов для пожилых «Опека»; после выхода акционеров «Валента Фарм» — ее единственный бенефициар.'
    if p and p.get('desc') != new:
        assert 'кредите Сбербанка' in (p.get('desc') or ''), p.get('desc')
        p['desc'] = new
        log.append('g678e182a desc')

    c = by['gaa59d3a1']
    if c.get('seller_id') != 'g59b505fe':
        assert c.get('seller_id') == 'g66c1d4b8', c.get('seller_id')
        c.setdefault('retracted', {}).setdefault('seller', []).append(c.get('seller'))
        c['seller'], c['seller_id'] = 'АО «Тетра»', 'g59b505fe'
        c.pop('seller_src', None)
        q = ('«Ъ», 08.08.2024: «Ранее их контролировало АО «Тетра», бенефициаром которого выступает кипрская Severstone '
             'Invest»; ЕГРЮЛ, ООО «Дон Агро»: 2024-06-25 вышло АО «Тетра» (ИНН 7715883484, 99,99%)')
        c.setdefault('party_evidence', {})['seller'] = {'url': 'https://www.kommersant.ru/doc/6879509', 'quote': q}
        fact_edit_guard.log(c, 'seller', c['seller'], q, 'https://www.kommersant.ru/doc/6879509', BY)
        log.append('gaa59d3a1 seller')
    if c.get('date') != '2024-06-25':
        assert c.get('date') == '2024-07-01', c.get('date')
        c['date'] = '2024-06-25'
        fact_edit_guard.log(c, 'date', '2024-06-25', 'ЕГРЮЛ, ООО «Дон Агро»: 2024-06-25 вышло АО «Тетра» (99,99%); «Ъ»: '
                            '«Основным владельцем ООО «Дон Агро» и «Дон Мучнов» в начале июля стало АО «Агрохолдинг '
                            '"Просторы"»»', REG % c['target'], BY)
        log.append('gaa59d3a1 date')

    c = by['g428f6180']
    if not c.get('asset'):
        c['asset'] = 'Европейские заводы «Технониколя»'
        fact_edit_guard.log(c, 'asset', c['asset'], '«Технониколь» вышла из европейского бизнеса, полностью закрыв сделки '
                            'по продаже заводов Imper, TN Italy в Италии и завода Mida LT в Литве',
                            'https://www.interfax.ru/business/971825', BY)
        log.append('g428f6180 asset')
    if c.get('date') != '2024':
        assert c.get('date') == '2024-07-01', c.get('date')
        c['date'] = '2024'
        fact_edit_guard.log(c, 'date', '2024', 'Интерфакс, 22.07.2024: «"Технониколь" вышла из европейского бизнеса, '
                            'полностью закрыв сделки…» — дня закрытия нет; Mida LT — сообщение 17 июля',
                            'https://www.interfax.ru/business/971825', BY)
        log.append('g428f6180 date')

    c = by['gd96d269e']
    if c.get('seller') != 'Nukem Technologies GmbH':
        assert c.get('seller_id') == 'rosatom', c.get('seller_id')
        c.setdefault('retracted', {}).setdefault('seller', []).append(c.get('seller'))
        c['seller'], c['seller_id'] = 'Nukem Technologies GmbH', None
        q = ("WNN, 01.10.2024: «Muroosystems acquired the company from the insolvency administrator of Nukem's previous "
             "German parent, Nukem Technologies GmbH»; «transferred in 2019 to TVEL … Rosatom»")
        c.setdefault('party_evidence', {})['seller'] = {
            'url': 'https://www.world-nuclear-news.org/articles/muroosystems-completes-purchase-of-nukem-technologies', 'quote': q}
        fact_edit_guard.log(c, 'seller', c['seller'], q, c['party_evidence']['seller']['url'], BY)
        log.append('gd96d269e seller')



def main(write):
    old = json.load(open(DATA, encoding='utf-8'))
    data = json.load(open(DATA, encoding='utf-8'))
    by = {c['id']: c for c in data['deals']}
    log = []
    card_edits(by, data['companies'], log)
    if not log:
        print('уже применено')
        return 0
    print('правки:', ', '.join(log))
    if not write:
        print('Сухой прогон. Запись — --write.')
        return 0
    mass_edit_guard.check(old, data)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
