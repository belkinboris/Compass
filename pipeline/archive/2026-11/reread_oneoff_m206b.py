# -*- coding: utf-8 -*-
"""Вычитка, марафон 12–13 ноября 2026, партия m206 (часть 2): то, что таблица правок не умеет.

- g405236c9 (НТК/«Данилово»): продавец — девелопер NK Group (с ним НТК ведет переговоры), а
  «Всеинструменты.ру» — арендатор, под которого строят склад; 8–9 млрд ₽ — оценки консультантов CMWP и
  Ricci, не цена: сумма «Не раскрыта» (docs/card_money.md, решение 13 ноября 2026); описание профиля НТК.
- gb8717464 («Союзмультфильм»): 1,2–1,3 млрд ₽ — оценка Бурмистрова; цену назвал продавец-государство:
  Минфин — 1,118 млрд ₽ поступлений от сделки (sum_basis disclosed). Продавец — Росимущество
  (собственник 100% акций), а не текст «Российская Федерация».
- g1c47b363 («Таврос»/«Тосненский»): ≈300 млн ₽ — оценка Шумова всех 100% долей, не цена 33%:
  «Не раскрыта»; описание профиля комбината без «купила» (находка post).
- gc567457f (Котласский химзавод): дня 20 декабря нет в источниках («в декабре 2024 года») — дата годом.
- g7ccf80f9 («Авито»/Internest): Денис Романовский — гендиректор Roden Media, комментатор, не продавец;
  продавец снят. Покупатель остается текстом «КЕХ Екоммерц»: ссылку на профиль «Авито» снял прежний
  аудит (запись таблицы правок 2026-10), юрлицо то же. 2,5 млрд ₽ — оценка Бурмистрова: «Не раскрыта». Описание профиля Internest.

Без ключа — сухой прогон; --write пишет, перечитав базу прямо перед записью. Повторный запуск
ничего не ломает («уже применено»).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка m206, 13.11.2026'
NONE = 'Не раскрыта'
KOM_NTK = 'https://www.kommersant.ru/doc/8119329'
MINFIN = 'https://finance.mail.ru/article/sberbank-kupil-paket-akciy-soyuzmultfilma-68111598/'
NEWSRU = 'https://news.ru/culture/soyumultfilm-privatizirovali-chto-eto-znachit-kto-kupil-dolyu'
KOM_TOS = 'https://www.kommersant.ru/doc/7433499'
KOM_KHZ = 'https://www.kommersant.ru/doc/7432009'
IFX_AV = 'https://www.interfax.ru/business/998257'
SOSTAV_AV = 'https://www.sostav.ru/publication/avito-kupil-reklamnye-servisy-adriver-i-soloway-72080.html'


def absorb(card, field, value):
    import review
    fp = review.fix_fingerprint(value)
    lst = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
    if fp not in lst:
        lst.append(fp)


def retract(card, field, value):
    r = card.setdefault('retracted', {}).setdefault(field, [])
    if value not in r:
        r.append(value)


def set_sum(card, old, new, quote, url, out):
    if card.get('sum') == new and card['eco'].get('sum') == new:
        return
    assert card.get('sum') == old and card['eco'].get('sum') == old, (card.get('sum'), card['eco'].get('sum'))
    card['sum'] = new
    card['eco']['sum'] = new
    retract(card, 'sum', old)
    fact_edit_guard.log(card, 'sum', new, quote, url, BY)
    fact_edit_guard.log(card, 'eco.sum', new, quote, url, BY)
    out.append('%s sum -> %s' % (card['id'], new))


def set_desc(comps, cid, start, desc, out):
    p = comps[cid]
    if p.get('desc') != desc:
        assert (p.get('desc') or '').startswith(start), p.get('desc')
        p['desc'] = desc
        out.append('%s desc' % cid)


def apply(data):
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    out = []

    c = deals['g405236c9']
    set_sum(c, '8–9 млрд ₽', NONE,
            'Руководитель департамента складской и индустриальной недвижимости CMWP Егор Дорофеев оценивает сумму '
            'сделки по покупке склада в Данилово в 9 млрд руб., директор в департаменте складской недвижимости Ricci '
            'Алексей Слепов — в 8–8,5 млрд руб. с учетом потенциальной скидки за значительный объем.',
            'https://www.kommersant.ru/doc/8119274', out)
    if c.get('seller') != 'NK Group':
        assert c.get('seller_id') == 'g5075b0e6' and c.get('seller') == 'Всеинструменты.ру', (c.get('seller_id'), c.get('seller'))
        c['seller_id'] = None
        c['seller'] = 'NK Group'
        retract(c, 'seller', 'Всеинструменты.ру')
        q = ('НТК договаривается с NK Group о покупке складского комплекса «Данилово» площадью около 100 тыс. кв. м '
             'в одноименной деревне Домодедовского района Подмосковья')
        fact_edit_guard.log(c, 'seller', 'NK Group', q, 'https://www.kommersant.ru/doc/8119274', BY)
        fact_edit_guard.log(c, 'seller_id', None, q, 'https://www.kommersant.ru/doc/8119274', BY)
        out.append('g405236c9 seller -> NK Group')
    set_desc(comps, 'ga1c619c8', 'Компания, созданная в 2014 году',
             'Инвестор в коммерческую недвижимость, создан в 2014 году; до декабря 2023 года им владел Валерий '
             'Субботин, сейчас учредитель — АО «Энерго решения». В 2025 году вел переговоры с NK Group о покупке '
             'складского комплекса «Данилово».', out)

    c = deals['gb8717464']
    q = ('Увеличение поступлений от приватизации в федеральный бюджет было обеспечено в основном за счет поступления '
         'средств от данной сделки и составило 1,118 млрд рублей')
    set_sum(c, '1,2–1,3 млрд ₽ (по оценке)', '1,118 млрд ₽', q, MINFIN, out)
    if c.get('sum_basis') != 'disclosed':
        assert c.get('sum_basis') is None, c.get('sum_basis')
        c['sum_basis'] = 'disclosed'
        fact_edit_guard.log(c, 'sum_basis', 'disclosed', q, MINFIN, BY)
        out.append('gb8717464 sum_basis -> disclosed')
    if c.get('seller_id') != 'g9fd82fee':
        assert c.get('seller') == 'Российская Федерация' and c.get('seller_id') is None, (c.get('seller'), c.get('seller_id'))
        assert comps['g9fd82fee']['name'] == 'Росимущество'
        c['seller_id'] = 'g9fd82fee'
        c['seller'] = None
        fact_edit_guard.log(c, 'seller_id', 'g9fd82fee',
                            'В 2021 году киностудия в рамках подготовки к приватизации была акционирована, '
                            'собственником 100% акций выступало Росимущество.', NEWSRU, BY)
        fact_edit_guard.log(c, 'seller', None,
                            'В 2021 году киностудия в рамках подготовки к приватизации была акционирована, '
                            'собственником 100% акций выступало Росимущество.', NEWSRU, BY)
        out.append('gb8717464 seller_id -> Росимущество')

    c = deals['g1c47b363']
    set_sum(c, '≈300 млн ₽ (по оценке)', NONE,
            'Инвестбанкир Илья Шумов оценивает 100% долей МПК «Тосненский» примерно в 300 млн руб.', KOM_TOS, out)
    set_desc(comps, 'ge02c264d', 'Мясоперерабатывающий комплекс в Ленобласти',
             'Мясоперерабатывающий комбинат в городе Тельман Ленинградской области: убой свиней и скота, оптовые '
             'поставки мяса.', out)

    old = ('Прежде предприятие контролировалось Олегом Селиховым (37%), Екатериной Ясновой (36%) и Виктором Крыловым '
           '(27%; ему также принадлежит мясоперерабатывающий завод «Иней» в Санкт-Петербурге); судя по данным СПАРК, все '
           'они полностью вышли из бизнеса МПК «Тосненский».')
    new = ('До сделки комбинатом владели Олег Селихов (37%), Екатерина Яснова (36%) и Виктор Крылов (27%), которому '
           'принадлежит еще и петербургский мясокомбинат «Иней»; по данным СПАРК, из МПК они вышли полностью.')
    ctx = c['eco']['context']
    if not ctx.startswith(new):
        assert ctx.startswith(old), ctx[:200]
        c['eco']['context'] = new + ctx[len(old):]
        out.append('g1c47b363 eco.context: первое предложение пересказано')

    c = deals['gc567457f']
    if c.get('date') != '2024':
        assert c.get('date') == '2024-12-20', c.get('date')
        c['date'] = '2024'
        for e in c.get('events') or []:
            if e.get('date') == '2024-12-20':
                e['date'] = '2024'
        fact_edit_guard.log(c, 'date', '2024',
                            'В декабре 2024 года МКОО «Огмент Инвестментс Лимитед» господина Харитонина получила '
                            'около 99,9% в ООО «КХЗ-Менеджмент»', KOM_KHZ, BY)
        out.append('gc567457f date -> 2024')

    # Цель сделки была рейтингом Forbes покупателя — это не мотив; рейтинг перенесен в контекст таблицей правок.
    if c['eco'].get('rationale') != '—':
        assert c['eco']['rationale'].startswith('Харитонин — 24-й в рейтинге'), c['eco']['rationale']
        import review
        for f in review.FIXES:
            if f['id'] == 'gc567457f' and f['field'] == 'eco.rationale':
                absorb(c, 'eco.rationale', f['new'])
        c['eco']['rationale'] = '—'
        out.append('gc567457f eco.rationale -> —')

    c = deals['g7ccf80f9']
    set_sum(c, '2,5 млрд ₽ (по оценке)', NONE,
            'Стоимость сделки официально не раскрывается. Глава «INFOLine Аналитики» Михаил Бурмистров оценивает ее '
            'в диапазоне 2−2,5 млрд руб.', SOSTAV_AV, out)
    if c.get('seller') is not None:
        assert c.get('seller') == 'Денис Романовский', c.get('seller')
        absorb(c, 'seller', 'Денис Романовский')
        retract(c, 'seller', 'Денис Романовский')
        c['seller'] = None
        fact_edit_guard.log(c, 'seller', None,
                            'В свою очередь основатель и генеральный директор Roden Media Денис Романовский отметил',
                            IFX_AV, BY)
        out.append('g7ccf80f9 seller -> None')
    notes = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    why = ('продавец не назван: ни сообщение «Авито», ни Интерфакс, ни Sostav, ни ADPASS и Oborot не называют прежних '
           'владельцев ООО «Интернест-Холдинг»; поиск по Roden Media и Интернест-Холдингу владельцев не дал, ЕГРЮЛ из '
           'контейнера не открылся. Денис Романовский (Roden Media) в сообщении — комментатор, не продавец')
    if notes.get('seller') != why:
        notes['seller'] = why
        out.append('g7ccf80f9 accepted_notes.no_profile.seller')
    set_desc(comps, 'g2527f1ab', 'Рекламная группа: сервис управления рекламой AdRiver',
             'Рекламная группа: сервис аудита и управления рекламой AdRiver и рекламная платформа Soloway; '
             'головная компания — ООО «Интернест-Холдинг». В 2024 году группу купил «Авито».', out)
    return out


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    out = apply(data)
    print('\n'.join(out) or 'уже применено')
    if '--write' in argv and out:
        data = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
        apply(data)
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
