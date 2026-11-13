# -*- coding: utf-8 -*-
"""Вычитка 13 ноября 2026, партия m230 (короткая проверка): стороны по реестру, оценка вместо цены, даты.

Источники открыты заново и сохранены save_source.save(..., day='2026-11-12_m230'); история участников
ЕГРЮЛ — сайт /api/companies/<id>/fns и datanewton.ru/api/v2/history (OWNERS).

ga024ea1e (Pizza Hut / «Ной-М»): «300 млн ₽» — оценка («Сумма сделки неизвестна. Оценочно она могла
  составить 300 млн руб.», Ведомости по Ъ; Ъ: «оценочно за 300 млн руб.» рядом с оценкой Михаила
  Бурмистрова) — не цена, сумма «Не раскрыта», оценка уже в eco.val. Дата 5 июля 2022 года — день
  заметки NRN о сообщении Yum!; Ъ 7 июня пишет, что сделка уже закрылась, дня закрытия нет — дата годом.
g19f07141 (Kingspan): по ЕГРЮЛ 1 апреля 2022 года вышла Kingspan Holdings (Irl) Limited — продавец она, а не
  Kingspan Group plc; из имени покупателя убраны пояснения; Федотченко вошел 19 сентября 2022 года, не в октябре.
gdc38f29c (Emerson / «Метран»): продавцы по распоряжению президента (Interfax 21.02.2023) — Tranmet Holdings
  B.V., Tranmet Holdings Ltd. и Emerson Electric Niderland B.V.; покупатель — ООО «Метран холдинг» без
  владельцев в скобках (они в law.struct).
g99f697c1 («Химки бизнес парк»): по ЕГРЮЛ 3 ноября 2026 года Аркадий Даниелян вышел из ООО «А-финанс» (100%)
  и ООО «КЛС-Химки» (1%), вошло ООО «АГР Холдинг»; «А-финанс» с 10.04.2024 владеет 99% «КЛС-Химки»,
  «КЛС-Химки» — 100% «Химки бизнес парк». Продавец — Даниелян, дата — 3 ноября 2026 года. Оценки
  аналитиков из суммы — в eco.val; описание здания из предмета — в контекст; заголовок без второй части.
g5dffcb32 («Эдисонэнерго»): по ЕГРЮЛ покупатель — ООО «ВТБ Индустриальная недвижимость», а не банк ВТБ;
  продавец — Dvorik Cyprus Ltd без группы в скобках.
g67bced75, g7f1f9992 («Макфа», «СМАК»): изъятие по суду; акционеров АО реестр не показывает, Юревич и
  Белоусов — бенефициары по иску, не продавцы (у «СМАКа» акционером называли и Владилена Фуфарова) —
  продавец снят. «СМАК»: по ЕГРЮЛ Росимущество записано единственным акционером 3 июля 2024 года — 100%.
gbfd7c740 («Империя II»): заголовок без «структур».
gdf6f72b9 («Тракс Восток Рус»): по ЕГРЮЛ 13 января 2023 года 100% общества перешли к ПАО «КАМАЗ» от
  Daimler Kamaz Trucks Holding GmbH — продавец по реестру она; доля 100%, а не 50%.

    python3 pipeline/archive/2026-11/reread_oneoff_m230.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m230', '2026-11-13'
DEL = object()

Q_PH_V = ('Сумма сделки неизвестна. Оценочно она могла составить 300 млн руб.',
          'https://www.vedomosti.ru/business/news/2022/06/07/925416-pizza-hut')
Q_PH_D = ('Владелец мастер-франшизы Pizza Hut в России Amrest сообщил в своей отчетности за первый квартал 2022 года, '
          'что ведет переговоры с владельцем бренда — Yum! Brands о передаче сети пиццерий в РФ местному оператору. '
          'Эта сделка уже закрылась.', 'https://www.kommersant.ru/doc/5392616')
EG_KS = ('ЕГРЮЛ, ООО «РП Гатчина» (бывш. «Кингспан», ИНН 4705033556): 2022-04-01 left Kingspan Holdings (Irl) Limited '
         '(100.0 → None); 2022-04-01 joined «Ф109 Лимитед» (None → 100.0); 2022-09-19 joined Федотченко Игорь '
         'Вячеславович (None → 0.684932)', '')
Q_EM = ('According to the order, Metran Holding is authorized to buy 178 ordinary shares of the Chelyabinsk joint-stock '
        'company from Tranmet Holdings B.V., based in the Netherlands, and part of Emerson Electric Co., and one more of '
        'its ordinary shares, held by Tranmet Holdings Ltd., Great Britain, also part of Emerson Electric Co. The seller '
        'of the shares will be Emerson Electric Niderland B.V. based in the Netherlands.',
        'https://interfax.com/newsroom/top-stories/88173/')
Q_EM_B = ('Russian President Vladimir Putin has authorized Metran Holding LLC in Chelyabinsk to acquire shares of Metran '
          'Industrial Group', 'https://interfax.com/newsroom/top-stories/88173/')
EG_HB = ('ЕГРЮЛ, история участников (datanewton): ООО «А-финанс» (ОГРН 1217700176396) 2026-11-03 вышел Даниелян '
         'Аркадий Ромаевич (100%), вошло ООО «АГР Холдинг» (ОГРН 1237700119348) 100%; ООО «КЛС-Химки» (ОГРН '
         '1225000080360) 2024-04-10 вошло ООО «А-финанс» 99%, 2026-11-03 вышел Даниелян Аркадий Ромаевич (1%), '
         'вошло ООО «АГР Холдинг» 1%; ООО «Химки бизнес парк» — 100% у ООО «КЛС-Химки» с 2023-06-21',
         'https://datanewton.ru/api/v2/history?ogrn=1225000080360&startDate=2000-01-01&attributes=OWNERS')
Q_HB = ('По оценке директора направления рынков капитала IBC Real Estate Николая Горюнова, покупка офисного объекта '
        'могла обойтись компании в 3–3,3 млрд руб.', 'https://www.kommersant.ru/doc/9093249')
Q_HB_T = ('Бенефициаром ООО «Химки бизнес парк» в начале ноября стало ООО «АГР Холдинг», обнаружил “Ъ” в базе СПАРК.',
          'https://www.kommersant.ru/doc/9093249')
Q_VTB = ('в конце сентября 2023 года перешло структуре банка ВТБ — «ВТБ Индустриальная недвижимость»',
         'https://www.kommersant.ru/doc/6312432')
Q_DV = ('Учредителем «Эдисонэнерго» ранее выступала кипрская Dvorik Cyprus Ltd',
        'https://www.kommersant.ru/doc/6312432')
Q_MK = ('Генпрокуратура РФ требовала обратить акции "Макфы" и связанных компаний в доход государства из-за '
        'коррупционного происхождения бизнеса.', 'https://www.interfax.ru/business/961968')
EG_SM = ('ЕГРЮЛ, АО «СМАК» (ИНН 6659003692): 2024-07-03 recorded Росимущество — единственный акционер; '
         '"ВТБ Регистратор" осуществил перевод акций на лицевые счета Росимущества (Интерфакс)',
         'https://www.interfax.ru/business/961968')
Q_EMP = ('Продавец площадки – структура холдинга USM Алишера Усманова и его партнеров и компании Solvers Estate Олега '
         'Малиса', 'https://www.vedomosti.ru/realty/articles/2024/10/15/1068944-sezar-group-kupila-proekti')
EG_TV = ('ЕГРЮЛ, ООО «Тракс Восток Рус» (ИНН 7714790325): 2023-01-13 left Даймлер Камаз Тракс Холдинг ГмбХ '
         '(100.0 → None); 2023-01-13 joined ПАО «КАМАЗ» (None → 100.0). Kamaz has consolidated 100% of shares in its '
         'former joint venture with German automaker Daimler, DK Rus LLC (Interfax)',
         'https://interfax.com/newsroom/top-stories/86912/')

HB_CONTEXT_OLD = ('«Химки бизнес парк» перешел к «КЛС-Химки» в 2023 году, бенефициарами которой тогда стали Григорий '
                  'Саакян и Аркадий Даниелян; передавал ли кто-то из них контроль «АГР Холдингу» сейчас, неизвестно.')
HB_CONTEXT_NEW = ('ООО «Химки бизнес парк» владеет одноименным офисным центром в Химках (Ленинградская улица) площадью '
                  '42 тыс. кв. м. В 2023 году общество перешло к ООО «КЛС-Химки», бенефициарами которого тогда были '
                  'Григорий Саакян и Аркадий Даниелян.')

# (id, поле, было, стало, цитата-адрес или None для прозы)
EDITS = [
    ('ga024ea1e', 'sum', '300 млн ₽ (по оценке)', 'Не раскрыта', Q_PH_V),
    ('ga024ea1e', 'eco.sum', '300 млн ₽ (по оценке)', 'Не раскрыта', Q_PH_V),
    ('ga024ea1e', 'date', '2022-07-05', '2022', Q_PH_D),

    ('g19f07141', 'seller', 'Kingspan Group plc', 'Kingspan Holdings (Irl) Limited', EG_KS),
    ('g19f07141', 'buyer_name', '«Ф109 Лимитед» (местный менеджмент; с декабря 2022 года — Игорь Федотченко)',
     '«Ф109 Лимитед»', EG_KS),
    ('g19f07141', 'law.struct',
     'По истории участников ЕГРЮЛ 1 апреля 2022 года 100% ООО «Кингспан» перешли от Kingspan Holdings (Irl) Limited к '
     'компании «Ф109 Лимитед»; Kingspan назвала покупателя местным менеджментом. В октябре–декабре 2022 года 100% '
     'перешли гендиректору Игорю Федотченко; в феврале 2023 года общество переименовано в ООО «РП Гатчина».',
     'По истории участников ЕГРЮЛ 1 апреля 2022 года 100% ООО «Кингспан» перешли от Kingspan Holdings (Irl) Limited к '
     'компании «Ф109 Лимитед»; Kingspan назвала покупателя местным менеджментом. В сентябре–декабре 2022 года 100% '
     'перешли гендиректору Игорю Федотченко; в феврале 2023 года общество переименовано в ООО «РП Гатчина».', None),

    ('gdc38f29c', 'seller', 'Emerson Electric Co.',
     'Tranmet Holdings B.V., Tranmet Holdings Ltd. и Emerson Electric Niderland B.V.', Q_EM),
    ('gdc38f29c', 'buyer_name', 'ООО «Метран холдинг» (Антон Дружинин и Николай Шестаков)', 'ООО «Метран холдинг»',
     Q_EM_B),
    ('gdc38f29c', 'accepted_notes.no_profile.seller',
     'Emerson Electric Co. — американская компания; продавцы — ее нидерландские и британская структуры (Интерфакс). '
     'История участников ЕГРЮЛ (datanewton, ОГРН 1027402540065): 04.05.2023 единственный акционер — ООО «Метран '
     'холдинг»; российского продавца нет.',
     'Продавцы — Tranmet Holdings B.V., Tranmet Holdings Ltd. и Emerson Electric Niderland B.V., структуры американской '
     'Emerson Electric Co. (распоряжение президента, Интерфакс 21.02.2023); иностранные компании без ИНН. История '
     'участников ЕГРЮЛ (datanewton, ОГРН 1027402540065): 04.05.2023 единственный акционер — ООО «Метран холдинг»; '
     'российского продавца нет.', None),
    ('gdc38f29c', 'accepted_notes.no_profile.buyer',
     'ООО «Метран холдинг» — ИНН в статьях не назван, профиль не заводили; покупатель назван словами с владельцами.',
     'ООО «Метран холдинг» — ИНН в статьях не назван, профиль не заводили; владельцы (Антон Дружинин и Николай '
     'Шестаков, поровну) — в law.struct.', None),

    ('g99f697c1', 'sum', None, 'Не раскрыта', Q_HB),
    ('g99f697c1', 'eco.sum', None, 'Не раскрыта', Q_HB),
    ('g99f697c1', 'eco.val', '—',
     'Цена не раскрыта, оценки аналитиков расходятся. Николай Горюнов, директор направления рынков капитала IBC Real '
     'Estate, называет 3–3,3 млрд ₽. У Антона Калистратова, руководителя департамента оценки и консалтинга CMWP, — '
     '3,3–4,6 млрд ₽. Екатерина Андреева, директор департамента инвестиций и рынков капитала Bright Rich | CORFAC '
     'International, дает 6,5–7 млрд ₽.', None),
    ('g99f697c1', 'asset',
     'ООО «Химки бизнес парк» — бизнес-центр площадью 42 тыс. кв. м на Ленинградской улице в Химках',
     'ООО «Химки бизнес парк»', Q_HB_T),
    ('g99f697c1', 'seller', DEL, 'Аркадий Даниелян', EG_HB),
    ('g99f697c1', 'date', '2026', '2026-11-03', EG_HB),
    ('g99f697c1', 'date_basis', DEL, 'registry', None),
    ('g99f697c1', 'eco.share', '—', '100% доли в ООО «А-финанс» и 1% доли в ООО «КЛС-Химки»', EG_HB),
    ('g99f697c1', 'title', '«АГР Холдинг» купил бизнес-центр «Химки бизнес парк», бывший офис владельца ИКЕА',
     '«АГР Холдинг» купил бизнес-центр «Химки бизнес парк»', Q_HB_T),
    ('g99f697c1', 'law.struct',
     'В начале ноября 2026 года владельцем ООО «Химки бизнес парк» через ООО «КЛС Химки» и ООО «А-финанс» стало ООО '
     '«АГР Холдинг» — переход заметили по данным СПАРК, стороны о сделке не сообщали.',
     'По истории участников ЕГРЮЛ 3 ноября 2026 года Аркадий Даниелян вышел из ООО «А-финанс» (100%) и из ООО '
     '«КЛС-Химки» (1%), их доли получило ООО «АГР Холдинг». «А-финанс» с апреля 2024 года владеет 99% «КЛС-Химки», '
     'а «КЛС-Химки» — 100% ООО «Химки бизнес парк». Стороны о сделке не сообщали.', None),
    ('g99f697c1', 'accepted_notes.no_profile.seller', 'KEEP', DEL, None),

    ('g5dffcb32', 'buyer', 'gcafc31dc', DEL, Q_VTB),
    ('g5dffcb32', 'buyer_name', DEL, 'ООО «ВТБ Индустриальная недвижимость»', Q_VTB),
    ('g5dffcb32', 'seller', 'Dvorik Cyprus Ltd (ADG Group)', 'Dvorik Cyprus Ltd', Q_DV),
    ('g5dffcb32', 'accepted_notes.no_profile.buyer',
     'Прямой покупатель — ООО «ВТБ Индустриальная недвижимость», ИНН в статьях не назван; карточка привязана к '
     'профилю ВТБ (gcafc31dc).',
     'ООО «ВТБ Индустриальная недвижимость» — структура банка ВТБ; ИНН в статьях не назван, профиль не заводили. По '
     'истории участников ЕГРЮЛ общество вошло в ООО «Эдисонэнерго» 28.09.2023 (100%) и вышло 21.12.2023.', None),

    ('g67bced75', 'seller', 'Михаил Юревич и Вадим Белоусов с семьями', DEL, Q_MK),
    ('g7f1f9992', 'seller', 'Михаил Юревич и Вадим Белоусов с семьями', DEL, Q_MK),
    ('g7f1f9992', 'eco.share', 'Акции АО «СМАК» перешли Росимуществу (доля в статьях не названа).',
     '100% акций АО «СМАК»', EG_SM),

    ('gbfd7c740', 'title',
     'Sezar Group купила у структур USM и Solvers Estate проект небоскреба «Империя II» в «Москва-Сити»',
     'Sezar Group купила у USM и Solvers Estate проект небоскреба «Империя II»', Q_EMP),

    ('gdf6f72b9', 'seller', 'Daimler Truck', 'Daimler Kamaz Trucks Holding GmbH', EG_TV),
    ('gdf6f72b9', 'seller_id', 'gb0f6fd37', DEL, EG_TV),
    ('gdf6f72b9', 'eco.share', '50% доли в ООО «Тракс Восток Рус»', '100% доли в ООО «Тракс Восток Рус»', EG_TV),
    ('gdf6f72b9', 'title', '«КАМАЗ» купил у Daimler 50% совместного предприятия «ДК Рус»',
     '«КАМАЗ» купил бывшее совместное с Daimler предприятие «ДК Рус»', EG_TV),
    ('gdf6f72b9', 'law.struct',
     '«КАМАЗ» довел долю с 50% до 100%. Незадолго до перехода, по ЕГРЮЛ, компания сменила название с «ДК Рус» на ООО '
     '«Тракс Восток Рус».',
     'До 13 января 2023 года 100% паритетного СП «КАМАЗа» и Daimler ООО «ДК Рус», по ЕГРЮЛ, принадлежали Daimler Kamaz '
     'Trucks Holding GmbH; 13 января 2023 года единственным участником стал ПАО «КАМАЗ». Незадолго до перехода '
     'компания сменила название с «ДК Рус» на ООО «Тракс Восток Рус».', None),
    ('gdf6f72b9', 'accepted_notes.no_profile.seller', DEL,
     'Daimler Kamaz Trucks Holding GmbH — иностранная компания без ИНН; по истории участников ЕГРЮЛ владела 100% ООО '
     '«Тракс Восток Рус» до 13.01.2023, профиль не заводили.', None),
]
RETRACT = [('ga024ea1e', 'sum', '300 млн ₽ (по оценке)'), ('g19f07141', 'seller', 'Kingspan Group plc'),
           ('gdc38f29c', 'seller', 'Emerson Electric Co.'),
           ('g67bced75', 'seller', 'Михаил Юревич и Вадим Белоусов с семьями'),
           ('g7f1f9992', 'seller', 'Михаил Юревич и Вадим Белоусов с семьями'),
           ('gdf6f72b9', 'seller', 'Daimler Truck')]


def _get(c, path):
    cur = c
    for k in path.split('.'):
        if not isinstance(cur, dict) or k not in cur:
            return DEL
        cur = cur[k]
    return cur


def _set(c, path, v):
    keys = path.split('.')
    cur = c
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    if v is DEL:
        cur.pop(keys[-1], None)
    else:
        cur[keys[-1]] = v


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, field, old, new, ev in EDITS:
        c = by[cid]
        cur = _get(c, field)
        if cur is new or cur == new:
            continue
        if old == 'KEEP':
            pass
        elif old is None:
            assert cur is not DEL and str(cur).startswith('Не раскрыта ('), (cid, field, cur)
        else:
            assert cur == old, (cid, field, cur)
        _set(c, field, new)
        if ev and field in fact_edit_guard.FACT_FIELDS + ('seller_id',):
            fact_edit_guard.log(c, field, None if new is DEL else new, ev[0], ev[1], BY, DAY)
        n += 1
    for cid, field, old in RETRACT:
        lst = by[cid].setdefault('retracted', {}).setdefault(field, [])
        if old not in lst:
            lst.append(old)
            n += 1
    ev = by['g99f697c1']['events'][0]
    if ev['date'] != '2026-11-03':
        assert ev['date'] == '2026'
        ev['date'] = '2026-11-03'
        n += 1
    ctx = by['g99f697c1']['eco']['context']
    if HB_CONTEXT_NEW not in ctx:
        assert HB_CONTEXT_OLD in ctx
        by['g99f697c1']['eco']['context'] = ctx.replace(HB_CONTEXT_OLD, HB_CONTEXT_NEW)
        n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
