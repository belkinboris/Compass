# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m065 (часть 2): правки, которые не ложатся в таблицу FIXES.

Зачем: review.py не разбирает часть форматов суммы («€1», «Не раскрыта») и не ставит основание даты,
заметки приемки и описания профилей. Каждое поле-факт пишется с fact_edit_guard.log (цитата и адрес
статьи, сохраненной save_source.py в sources_2026-11-12_m065.json). Повторный запуск ничего не ломает:
уже записанное значение пропускается («уже применено»), иначе assert на старое значение.

    python3 pipeline/archive/2026-11/reread_oneoff_m065b.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m065b.py --write    # запись (перечитывает базу перед записью)
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(PIPE)
for p in (os.path.join(PIPE, 'ingest'), PIPE):
    if p not in sys.path:
        sys.path.insert(0, p)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
_BY = 'reread m065b'

_KO_VR = 'https://www.kommersant.ru/doc/6147405'
_IF_BL = 'https://www.interfax.ru/business/914356'
_AKM_MS = 'https://www.akm.ru/news/rusatom_khelskea_uvelichil_dolyu_v_medskane_do_50/'
_IF_INK = 'https://www.interfax.ru/business/910063'
_Q_INK = ('Goldman Sachs International был акционером компании с 2013 года", - сообщается в отчете без уточнения нового '
          'собственника доли.')
_Q_INK_SUM = ('По данным источника "Интерфакса", знакомого с ситуацией, в прошлом году обсуждался вариант выкупа доли '
              'Goldman Sachs на баланс ООО "ИНК" за сумму около $150 млн. Информации о том, какой сценарий в итоге был '
              'реализован, у источника агентства нет')

_VED_BL = 'https://www.vedomosti.ru/business/news/2023/05/19/975894-blavatnik-prodal-dolyu-uc-rusal'
_KO_EX = 'https://www.kommersant.ru/doc/5939524'
_SH_EX = 'https://schoenherr.eu/content/serbia-schoenherr-advises-on-acquisition-of-expobank-a-d-belgrade'
_BDK_EX = 'https://bdkadvokati.com/bdk-advokati-advises-on-the-sale-of-expobank'
_KO_RNL = 'https://www.kommersant.ru/doc/5887461'
_Q_BL = 'При этом кто именно купил долю – не уточняется. Другие подробности сделки также не раскрываются.'
_Q_EX = ('Expobank A.D. Belgrade принадлежал чешскому Expobank CZ, однако в сентябре 2022 года Игорь Ким закрыл сделку по '
         'продаже банка в Чехии местному игроку Creditas, поэтому сербская «дочка» была переведена в собственность '
         'российского Экспобанка, сообщил собеседник издания.')
_Q_RNL = ('Французский RCI Banque — «дочка» Renault — 11 октября 2022 года договорился о продаже своей лизинговой компании в '
          'России «РНЛ Лизинг», следует из отчетности кредитной организации')
_Q_RNL_SUM = 'Лизинговая компания может быть продана по цене до €22 млн.'

_ADV_OLD = [['Консультанты сделки', 'Schoenherr (юридический) и KPMG Белград (финансовый)',
             'Коммерсантъ: «Об этом сообщила юридическая фирма Schoenherr, которая является одним из консультантов '
             'сделки»; «В Schoenherr уточнили, что финансовым консультантом сделки было белградское отделение KPMG». '
             'Источник: https://www.kommersant.ru/doc/5939524']]
_ADV_NEW = [['Юридический консультант покупателя (владельца Adriatic Bank A.D. Podgorica)',
             'Schoenherr (Moravčević Vojnović and partners)',
             'Сопровождала покупку 100% акций Expobank A.D. Belgrade. Источник: ' + _SH_EX],
            ['Юридический консультант продавцов (акционеров Expobank A.D. Belgrade)', 'BDK Advokati',
             'Команду вели партнер Владимир Дашич и юрист Саня Дедович. Источник: ' + _BDK_EX],
            ['Финансовый консультант одной из сторон', 'KPMG (Белград)',
             'Финансовым консультантом сделки было белградское отделение KPMG, клиента источники не называют. '
             'Источник: ' + _KO_EX]]

# (id, поле, старое, новое, цитата, адрес) — поля-факты, с fact_log
ONE_OFF = [
 # $610 млн — рыночная стоимость пакета на конец 2022 года по данным Bloomberg, а не цена продажи
 ('g5fd0e682', 'sum', '$610 млн', 'Не раскрыта', _Q_BL, _VED_BL),
 ('g5fd0e682', 'eco.sum', '$610 млн', 'Не раскрыта', _Q_BL, _VED_BL),
 # 19 мая 2023 года — день публикации; акции проданы «во второй половине 2022 г.», дня нет — год
 ('g5fd0e682', 'date', '2023-05-19', '2022', 'Он продал акции во второй половине 2022 г.', _VED_BL),
 # продавец — российский Экспобанк (структура Игоря Кима), которому перевели сербскую «дочку»; BDK Advokati
 # консультировала «акционеров Expobank A.D. Belgrade» — юрлицо, а не бенефициара
 ('g010ece87', 'seller', 'Игорь Ким', 'Экспобанк', _Q_EX, _KO_EX),
 ('g010ece87', 'seller_id', None, 'g0a130abd', _Q_EX, _KO_EX),
 # клиенты консультантов — по их сообщениям (Schoenherr — владелец Adriatic Bank, BDK — акционеры Expobank)
 ('g010ece87', 'law.adv', _ADV_OLD, _ADV_NEW,
  'Moravčević Vojnović and partners in cooperation with Schoenherr advised the owner of Adriatic Bank A.D. Podgorica on '
  'the acquisition of 100 % of the shares in Expobank A.D. Belgrade.', _SH_EX),
 # продавец назван в источнике прямо: RCI Banque договорился о продаже «РНЛ Лизинг»
 ('gbf0be72c', 'seller', None, 'RCI Banque', _Q_RNL, _KO_RNL),
 ('gbf0be72c', 'seller_id', None, 'ga2a10fa9', _Q_RNL, _KO_RNL),
 # «по цене до €22 млн» — верхняя граница, а не цена (docs/card_money.md, «Диапазон остается диапазоном»)
 ('gbf0be72c', 'sum', '€22 млн', 'До €22 млн', _Q_RNL_SUM, _KO_RNL),
 ('gbf0be72c', 'eco.sum', '€22 млн', 'До €22 млн', _Q_RNL_SUM, _KO_RNL),
]

# снятые значения — чтобы enrich.py не вернул их с той же статьей
_RETRACT = [
 ('g5fd0e682', 'sum', '$610 млн'),
]

# основание даты и прочие служебные поля (не факты): (id, поле, старое, новое)
_SET = [
 # «Холдинг S8 Capital завершил сделку» — пресс-служба покупателя «Ъ» 28.04.2023: день объявления о закрытии
 ('gafda8e29', 'date_basis', None, 'announcement'),
 # RCI Banque «11 октября 2022 года договорился о продаже» (отчетность банка, Ъ 5887461)
 ('gbf0be72c', 'date_basis', None, 'signing'),
 # ЕГРЮЛ (реестр на сайте, /api/companies/ga220a7e4/fns): 12.04.2023 единственным акционером АО «ЕПК» записано АО
 # «Центротраст» — управляющая компания ЗПИФ (реестр ПИФ Банка России, правила № 5206-СД); Ъ 20.03.2023 уже писал о
 # продаже, фонд сформирован 26.12.2022 — какое событие считать датой, источники не говорят, дата не тронута
 ('g1d73eef1', 'law.struct',
  'Комбинированный закрытый паевой инвестиционный фонд промышленных инноваций числится в реестре ЦБ РФ. Фонд '
  'зарегистрирован 28 ноября 2022 года, его формирование завершено 26 декабря.',
  'Комбинированный закрытый паевой инвестиционный фонд промышленных инноваций числится в реестре ЦБ РФ. Фонд '
  'зарегистрирован 28 ноября 2022 года, его формирование завершено 26 декабря.\n\nФондом управляет АО «Центротраст»; '
  'по ЕГРЮЛ, с 12 апреля 2023 года оно записано единственным акционером АО «ЕПК».'),
]

# заметки приемки: (id, путь в accepted_notes, текст)
_NOTES = [
 ('g5fd0e682', 'no_profile.buyer',
  'Покупатель не раскрыт: Bloomberg (пересказ «Ведомостей») — «кто именно купил долю, не уточняется». Искали: '
  'Ведомости, Bloomberg (капча), Mining Weekly (403), поиск по-русски («Блаватник продал долю в Русале») и '
  'по-английски («Blavatnik sold stake Rusal buyer»), раскрытие UC Rusal об акционерах — покупатель нигде не назван.'),
 ('g5fd0e682', 'searched',
  'Ведомости 19.05.2023; Bloomberg 18.05.2023 (капча); Mining Weekly (403); поиск по-русски и по-английски; '
  'Википедия о Леониде Блаватнике — других первоисточников о сделке нет.'),
 ('g560e3f93', 'no_profile.buyer',
  'Покупатель — «местный винодел», имя не раскрыто (Ведомости, Interfax: «The buyer and price have not been '
  'disclosed»). Искали: Forbes (капча), Ведомости, Interfax, Retail.ru, ТАСС, поиск по-английски.'),
]

# описания профилей: (id профиля, поле, старое, новое)
_COMPANY = [
 ('g57a606d0', 'desc',
  'Сербский банк; в 2023 году его продал Игорь Ким компании Adriatic Bank — последний европейский банковский актив '
  'Кима после продажи латвийского и чешского Expobank.',
  'Сербский банк, до 2022 года «дочка» чешского Expobank CZ, затем российского Экспобанка Игоря Кима. В 2023 году '
  'продан владельцу черногорского Adriatic Bank, с сентября 2023 года называется Adriatic Bank A.D. Belgrade.'),
 ('ga0d1d43f', 'desc',
  'В 2023 году купил у Игоря Кима сербский Expobank A.D. Belgrade — последний европейский банковский актив Кима после '
  'продажи латвийского и чешского банков.',
  'Черногорский банк, основан в 2016 году; с 2020 года принадлежит американской Adriatic Capital. В 2023 году его '
  'владелец купил сербский Expobank A.D. Belgrade у российского Экспобанка.'),
 ('g1a56c6ea', 'desc',
  'Заводы свечей зажигания, электроинструментов и котлов отопления; в 2023 году их 100% купил у немецкой Bosch S8 '
  'Capital, сохранив рабочие места.',
  'Заводы свечей зажигания, электроинструментов и котлов отопления в Энгельсе; в 2023 году их 100% купил у немецкой '
  'Bosch холдинг S8 Capital.'),
 ('g550fb0b0', 'desc',
  "Винодельческое хозяйство во Франции: выпускает шампанское под марками Louis XIV, Chateau d'Avize и Chateau d'Avize "
  "Blanc de Blanc. Производственный комплекс — на 2 млн бутылок в год, подвалы для хранения вина — примерно на 5 млн "
  "бутылок; виноградники взяты в долгосрочную аренду. Первую коммерческую партию шампанского выпустили в 2017 году.",
  "Шампанский дом в коммуне Авиз (Шампань, Франция), основан в XIX веке; может выпускать 2 млн бутылок в год. В 2022 "
  "году «Абрау-Дюрсо» продала его местному виноделу."),
]

def _get(obj, field):
    for p in field.split('.'):
        obj = obj.get(p) if isinstance(obj, dict) else None
    return obj


def _set(obj, field, value):
    parts = field.split('.')
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    obj[parts[-1]] = value


def _apply(data):
    import fact_edit_guard
    deals = {d['id']: d for d in data['deals']}
    done = 0
    for cid, field, old, new, quote, url in ONE_OFF:
        card = deals[cid]
        if _get(card, field) == new:
            continue
        assert _get(card, field) == old, (cid, field, _get(card, field))
        _set(card, field, new)
        fact_edit_guard.log(card, field, new, quote, url, _BY)
        done += 1
    for cid, field, old, new in _SET:
        if _get(deals[cid], field) == new:
            continue
        assert _get(deals[cid], field) == old, (cid, field, _get(deals[cid], field))
        _set(deals[cid], field, new)
        done += 1
    for cid, field, value in _RETRACT:
        if not isinstance(deals[cid].get('retracted'), dict):
            deals[cid]['retracted'] = {}
        cur = deals[cid]['retracted'].setdefault(field, [])
        if value not in cur:
            cur.append(value)
            done += 1
    for cid, path, value in _NOTES:
        notes = deals[cid].get('accepted_notes') or {}
        deals[cid]['accepted_notes'] = notes
        if _get(notes, path) == value:
            continue
        assert _get(notes, path) is None, (cid, path, _get(notes, path))
        _set(notes, path, value)
        done += 1
    for comp, field, old, new in _COMPANY:
        c = data['companies'][comp]
        if c.get(field) == new:
            continue
        assert c.get(field) == old, (comp, field, c.get(field))
        c[field] = new
        done += 1
    return done


if __name__ == '__main__':
    import mass_edit_guard  # noqa: E402
    data = json.load(open(DATA, encoding='utf-8'))
    before = copy.deepcopy(data)
    n = _apply(data)
    mass_edit_guard.check(before, data)
    print('Разовая часть m065b: изменений %d (полей-фактов в списке %d) — проверки пройдены.%s'
          % (n, len(ONE_OFF), '' if n else ' Уже применено.'))
    if '--write' in sys.argv and n:
        fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
        before = copy.deepcopy(fresh)
        _apply(fresh)
        mass_edit_guard.check(before, fresh)
        with open(DATA, 'w', encoding='utf-8') as fh:
            json.dump(fresh, fh, ensure_ascii=False, indent=1)
        print('Записано.')
    elif '--write' not in sys.argv:
        print('Сухой прогон. Запись — с ключом --write.')
