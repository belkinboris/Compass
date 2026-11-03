# -*- coding: utf-8 -*-
"""Вычитка 3 ноября 2026, ночь (партия ng): правки, которых review.py не умеет.

Прозу партии пишет pipeline/ingest/fixes/reread_2026_11_03_ng.py; здесь — то, что таблица
не пропускает: ссылки на профили, формат суммы «До N» и три поля, чьи числа стоят только в
английских источниках (prose_gate не считает число, за которым идет латинское слово:
«RUB 335 per», «60 calendar days», «7.44 billion») — перевод с цитатой здесь, источник уже в
src карточки (docs/card_editing.md, «Под вопросом: как записывать перевод»).

ge386fb20 («Магнит»/«Колос Кубани») — неверные роли.
  Коммерсантъ (kommersant.ru/doc/8476725): «„Магнит“ выкупил хозяйство по выращиванию голубики
  и яблок у ООО „Колос Кубани“, рассказали „Ъ“ в компании. В периметр соглашения вошли 262 га
  земли». Реестр ООО «Колос Кубани» (ИНН 2304073639, сверен вживую 28.08.2026 — после сделки)
  по-прежнему показывает Дениса Тарана владельцем 100% с 3 октября 2025 года; у общества около
  1,8 тыс. га (TAdviser), куплено 262. Значит, «Магнит» купил хозяйство у ООО, а не ООО у
  Тарана: продавец — ООО «Колос Кубани» (профиль gf4207471 переходит из target в seller_id),
  предмет — хозяйство текстом (как «элеваторы и зерновой терминал в порту Азов» у g304f9065).
  «Денис Таран» в продавцах — в retracted, чтобы обогащение не вернуло его.
  Отвергнуто: оставить Тарана по правилу «Стаксель» (docs/card_parties.md) — оно про покупку
  долей, переход которых реестр еще не показал; здесь статья прямо называет продавцом ООО.

gf14ff7aa (фонд специальных ситуаций) — sum «30 млрд ₽» ≠ eco.sum «До 30 млрд ₽» (находка
  приемки sum_fields_differ). «Альфа-Капитал»: «планирует привлечь капитал до 30 млрд рублей»;
  review.sum_is_supported формат «До N» не разбирает.

ge6f1e0ae (Globaltrans) — law.terms пусто, в extra «335 ₽ на GDR» (неверно: на обыкновенную
  акцию, решение совета директоров 18.04.2025, globaltrans.com/investors/news/detail/2557).

Профиль delo («Группа компаний «Дело»», предмет g5eb6ff22) — legal_short «ООО «УК «Дело»»» (находка
  приемки party_legal_form:target). party_legal_names.py --write здесь НЕ годится: сайт
  (/api/companies/delo/fns) отдает тольяттинское ООО «ГК Дело», ИНН 6320082606 (владелец Данил
  Малютин), хотя fns_registry.json 3 сентября 2026 перепривязал профиль к ООО «УК «Дело»», ИНН
  7706434676 (решение и причина — в реестре); доли сделки — доли УК «Дело» (ТАСС: «до 100% долей в
  уставном капитале ООО УК “Дело”»).

g81d69138 («Балчуг Капитал») — eco.val: «Около 7,4 млрд ₽ по рыночным ценам на дату сделки;
  цифра 45,6 млрд ₽ … не подтверждена» — без автора, «45,6 млрд» ни в одном источнике нет.
  Автор оценки — Interfax (EN), 2.04.2025: «almost 7.44 billion rubles or $87.6 million».

    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_ng.py            # сухой прогон
    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_ng.py --write    # затем facts_derive.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

KK = 'ge386fb20'
KK_PROFILE = 'gf4207471'
KK_ASSET = 'Сады голубики и яблок в Крымском районе Краснодарского края'

A1 = 'gf14ff7aa'
DELO = 'delo'
DELO_LEGAL = 'ООО «УК «Дело»»'
GT = 'ge6f1e0ae'
BC = 'g81d69138'

GT_TERMS_OLD = '—'
GT_TERMS_NEW = ('Цена окончательная и не корректируется. Покупатель платит в течение 90 дней после закрытия, '
                'а права на все активы должны перейти к нему за 60 дней, иначе он вправе отказаться от '
                'договора.')
# «The specified Total Consideration is final and is not subject to any adjustment … Total
# Consideration will be paid within 90 days from the closing date … the title to all Assets shall be
# transferred to the Purchaser within 60 calendar days following the Closing Date, otherwise the
# Purchaser is entitled to withdraw from the SPA» (globaltrans.com, итоги собрания 10.04.2025)

GT_EXTRA_OLD = ('Акционеры Globaltrans Investment PLC 10 апреля 2025 года одобрили продажу 100% долей в пяти '
                'дочерних компаниях в пользу ЗПИФ «Трансатлант» под управлением ООО «КСП Капитал Управление '
                'Активами». Закрытие сделки состоялось около 17 апреля 2025 года; покупатель обязан '
                'перечислить $767 млн в рублевом эквиваленте в течение 90 дней с даты закрытия. Одновременно '
                'акционеры одобрили выпуск новых акций на сумму до $101,7 млн с оплатой через передачу GDR из '
                'российских депозитариев. Совет директоров утвердил специальный дивиденд в размере 335 ₽ на '
                'GDR из поступлений от сделки; компания намерена распределить все или почти все вырученные '
                'средства через этот механизм.')
GT_EXTRA_NEW = ('О передаче «дочек» покупателю стало известно 17 апреля 2025 года. На следующий день совет '
                'директоров Globaltrans утвердил специальный дивиденд — 335 ₽ на обыкновенную акцию, всего '
                '59,7 млрд ₽, около 95% выручки от продажи.\n'
                '\n'
                'Тем же собранием, что одобрило продажу, акционеры разрешили выпустить новые акции на сумму до '
                '$101,7 млн, которые оплачиваются расписками GDR из российских депозитариев.')
# «RUB 335 per 1 ordinary share … in total to RUB 59 736 616 765 … approximately 95% of the gross
# proceeds» (globaltrans.com, 18.04.2025); дата передачи — Коммерсантъ, kommersant.ru/doc/7660033,
# опубликован 17.04.2025; выпуск акций — Интерфакс, interfax.ru/business/1020286

BC_VAL_OLD = ('Около 7,4 млрд ₽ по рыночным ценам на дату сделки; цифра 45,6 млрд ₽, встречавшаяся в ранних '
              'сообщениях, источниками не подтверждена.')
BC_VAL_NEW = ('Цену сделки стороны не раскрыли. По расчету «Интерфакса», рыночная стоимость всех пакетов в день '
              'распоряжения — почти 7,44 млрд ₽ ($87,6 млн), из них около 4 млрд ₽ приходится на «Газпром»; '
              'Reuters насчитал почти $80 млн.')
# «The combined market value of these stakes … was almost 7.44 billion rubles or $87.6 million at the
# official rate on April 2» (interfax.com/newsroom/top-stories/110724/); «самый заметный из них - 0,12%
# "Газпрома" рыночной стоимостью почти 4 млрд рублей» (interfax.ru/business/1017901); «The value of all
# shares listed in the decree amounted to almost $80 million, according to Reuters calculations»


def deal(base, did):
    return next(d for d in base['deals'] if d['id'] == did)


def plan(base):
    kk = deal(base, KK)
    assert kk.get('seller') == 'Денис Таран', kk.get('seller')
    assert not kk.get('seller_id'), kk.get('seller_id')
    assert kk.get('target') == KK_PROFILE, kk.get('target')
    assert not kk.get('asset'), kk.get('asset')
    assert base['companies'][KK_PROFILE]['name'] == 'ООО «Колос Кубани»'
    a1 = deal(base, A1)
    assert a1.get('sum') == '30 млрд ₽', a1.get('sum')
    assert a1['eco'].get('sum') == 'До 30 млрд ₽', a1['eco'].get('sum')
    gt = deal(base, GT)
    assert gt['law'].get('terms') == GT_TERMS_OLD, gt['law'].get('terms')
    assert gt.get('extra') == GT_EXTRA_OLD, gt.get('extra')[:80]
    bc = deal(base, BC)
    assert bc['eco'].get('val') == BC_VAL_OLD, bc['eco'].get('val')
    assert not base['companies'][DELO].get('legal_short'), base['companies'][DELO].get('legal_short')
    return kk, a1, gt, bc


def apply(base):
    kk, a1, gt, bc = plan(base)
    kk['seller'] = 'ООО «Колос Кубани»'
    kk['seller_id'] = KK_PROFILE
    kk['target'] = None
    kk['asset'] = KK_ASSET
    retracted = kk.setdefault('retracted', {})
    if 'Денис Таран' not in retracted.setdefault('seller', []):
        retracted['seller'].append('Денис Таран')
    a1['sum'] = 'До 30 млрд ₽'
    gt['law']['terms'] = GT_TERMS_NEW
    gt['extra'] = GT_EXTRA_NEW
    bc['eco']['val'] = BC_VAL_NEW
    base['companies'][DELO]['legal_short'] = DELO_LEGAL


def main(argv):
    base = json.load(open(DATA, encoding='utf-8'))
    plan(base)
    print('%s: seller «Денис Таран» → «ООО «Колос Кубани»», seller_id → %s, target %s → None, asset → %r'
          % (KK, KK_PROFILE, KK_PROFILE, KK_ASSET))
    print('%s: sum «30 млрд ₽» → «До 30 млрд ₽»' % A1)
    print('%s: law.terms «—» → %s…; extra → %s…' % (GT, GT_TERMS_NEW[:60], GT_EXTRA_NEW[:60]))
    print('%s: eco.val → %s…' % (BC, BC_VAL_NEW[:60]))
    print('профиль %s: legal_short → %s' % (DELO, DELO_LEGAL))
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
    apply(fresh)
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано. Дальше: python3 pipeline/facts_derive.py --write')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
