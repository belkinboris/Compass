# -*- coding: utf-8 -*-
"""Кампания чтения #122: профили сторон для карточек притока.

ПОЧЕМУ. У 131 карточки притока (`from_ingest: true`) хотя бы одна сторона
(предмет/покупатель/продавец) записана текстом, а не ссылкой на профиль
компании — 90% свежих карточек без кликабельного предмета, 79% без
кликабельного покупателя (замер 11 сентября 2026, см. CLAUDE.md). Приток
пишет стороны текстом и не спрашивает, есть ли у компании профиль; связка
`link_parties.py` чинит только ТОЧНОЕ совпадение с уже существующим
профилем, а новых профилей никогда не заводит — по правилу «ЗАВОДИТЬ
профили механически нельзя», это требует чтения.

КАК СДЕЛАНО. Пять параллельных агентов прочитали все 131 карточку целиком
(не только текст роли — `title`, `asset`, `extra`, `eco`, `law`, плюс
WebFetch по источникам, где нужно) и для каждой из 258 ролей решили:
существующий профиль / новый профиль (с фактами, дословно взятыми из
карточки или источника) / не компания (доля без имени, недвижимость без
юрлица-держателя, физлица, регион, лот из нескольких юрлиц) / неясно.
Отчёты — `pipeline/campaign_122/agent_reports.json`, это сырьё для этого
скрипта и одновременно документация того, что читали и почему решили
так, а не иначе (тот же принцип, что у `pipeline/merge_specs/*.json`).

ЧТО Я ПРОВЕРИЛ ПОВЕРХ АГЕНТОВ, ПРЕЖДЕ ЧЕМ ПИСАТЬ. (1) Механически прогнал
`company_key()` (тот же, что в `test_no_company_twins`) по всем 142
предложенным именам против существующих 1866 профилей — нашлась ровно
одна настоящая коллизия («ТД Эдельвейс» ключом совпадает с уже
существующим «АО «Эдельвейс»» — но это документированная в
`link_parties.NOT_THE_SAME` разная сущность, торговый дом и акционерное
общество разных владельцев; профиль заводится отдельно, тест на
близнецов получил четвёртое исключение). (2) Нашёл один омоним МЕЖДУ
предложениями двух разных агентов: «СтройИнвест» (инвесткомпания в
Екатеринбурге, ресторатор Ферганов) и «Строй инвест» (юрлицо-собственник
ТЦ «Город Косино» в Москве, экс-«Газпромбанк-инвест») — разные компании
с похожим именем, родня уже известного урока про «Каму»; оба профиля
заведены с уточнением в скобках, чтобы ключи не совпадали. (3) Прочитал
все 142 пары имя/описание целиком глазами — проверил, что описания не
выдуманы (только пересказ уже прочитанных фактов), что крупные компании
(Транснефть, МКБ, ГТЛК, Банк России, НСПК), у которых агенты «неожиданно»
не нашли профиля, действительно отсутствуют в базе (проверено прямым
поиском по подстроке отдельно от ключа). (4) Одно предложение — «Недви-
жимые активы» (`g134cf416`, buyer) — сознательно НЕ принято: карточка уже
прошла приёмку 12 сентября 2026 с явным решением не заводить профиль
непубличной SPV без раскрытых бенефициаров; агент с этим не согласился,
но менять уже принятое решение приёмки без человека не буду — текст
остаётся текстом.

Отрасль (`ind`) каждому новому профилю назначена по прочитанным описаниям
и сверена, где было можно, с уже принятой в базе классификацией похожих
компаний (лизинг → «Транспорт и логистика», зарядная инфраструктура →
«Автопром» — по профилю-соседу «ООО «Парус электро»»).

Запуск:
    python3 pipeline/fix_link_ingest_party_profiles_campaign.py
    python3 pipeline/fix_link_ingest_party_profiles_campaign.py --write
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep + 'pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REPORTS = os.path.join(ROOT, 'pipeline', 'campaign_122', 'agent_reports.json')

sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import link_parties  # noqa: E402

ID_FIELD = {'target': 'target', 'buyer': 'buyer', 'seller': 'seller_id'}
TEXT_FIELD = {'target': 'asset', 'buyer': 'buyer_name', 'seller': 'seller'}
GUARD_FIELDS = {'target': ('target', 'asset_id'), 'buyer': ('buyer',), 'seller': ('seller_id',)}

# Дисамбигуация омонима, найденного между партиями 3 и 5 (см. докстринг).
# Ключ — (card_id, role); значение — имя, которое реально записывается в
# базу вместо предложенного агентом.
RENAME = {
    ('g9254527a', 'buyer'): 'СтройИнвест (Екатеринбург)',
    ('gddb34475', 'target'): 'Строй инвест (ТЦ «Город Косино»)',
    # Агент предложил полное официальное имя («Dr. Reddy's Laboratories»),
    # но `review.py` уже нёс запись FIXES для этой же карточки с коротким
    # именем «Dr. Reddy's» (дословно из цитаты источника) — расхождение
    # нашлось прогоном `test_review_table_is_applied_and_not_pending`.
    # Короткая форма не менее верна (это узнаваемый бренд, как «Qiwi plc»
    # уже хранится без разворачивания) и не создаёт коллизии ключа — проще
    # держать одно имя, уже проверенное дословной цитатой, чем заводить
    # второе рядом.
    ('gf70a43e6', 'buyer'): "Dr. Reddy's",
}

# Решения приёмки 12 сентября сильнее вердикта агента — не заводить профиль.
EXCLUDE = {
    ('g134cf416', 'buyer'),
}

# Отрасль для каждого нового профиля — по прочитанным описаниям (см.
# докстринг, пункт (3) и сверка с лизингом/зарядной инфраструктурой).
INDUSTRY = {
    ('gmru-prodo-star-nafta-broiler', 'target'): 'Агро',
    ('gmru-prodo-star-nafta-broiler', 'buyer'): 'Пищепром и напитки',
    ('gmru-prodo-star-nafta-broiler', 'seller'): 'Агро',
    ('gmru-prime-pervy-poliplastik', 'buyer'): 'Управление активами',
    ('gmru-svoj-kredit-evropa-strah', 'target'): 'Страхование',
    ('gmru-svoj-kredit-evropa-strah', 'buyer'): 'Финтех',
    ('gmru-kolomenskoe-peko', 'target'): 'Пищепром и напитки',
    ('gmru-arnest-reckitt', 'target'): 'Потребительские товары',
    ('gmru-arnest-reckitt', 'seller'): 'Потребительские товары',
    ('gmru-mariholodmash-borsky', 'target'): 'Машиностроение',
    ('gmru-mariholodmash-borsky', 'buyer'): 'Машиностроение',
    ('gmru-nordline-totalenergies-arctic', 'target'): 'Нефть и газ',
    ('gmru-nordline-totalenergies-arctic', 'buyer'): 'Нефть и газ',
    ('gmru-nordline-totalenergies-arctic', 'seller'): 'Нефть и газ',
    ('gmru-mtsbank-kdpay', 'target'): 'Финтех',
    ('gmru-roshim-vnt', 'target'): 'Порты и инфраструктура',
    ('gmru-geopromining-zabaikalie', 'target'): 'ГМК и добыча',
    ('gmru-geopromining-zabaikalie', 'buyer'): 'ГМК и добыча',
    ('gmru-geopromining-zabaikalie', 'seller'): 'ГМК и добыча',
    ('gmru-sucden-poetti', 'target'): 'Пищепром и напитки',
    ('gmru-nordgold-chukotka', 'target'): 'ГМК и добыча',
    ('gmru-mirgorodsky-nattys', 'target'): 'Пищепром и напитки',
    ('gmru-rodnye-polya', 'target'): 'Агро',
    ('gmru-rodnye-polya', 'buyer'): 'Агро',
    ('gmru-dobroflot-ikorny', 'target'): 'Ритейл',
    ('gmru-dobroflot-ikorny', 'buyer'): 'Агро',
    ('gmru-vostok-sever-pevek', 'target'): 'Порты и инфраструктура',
    ('gmru-vostok-sever-pevek', 'buyer'): 'Управление активами',
    ('gmru-vim-poklonka', 'buyer'): 'Управление активами',
    ('gmru-sutochno-onetwotrip', 'target'): 'Гостиницы и туризм',
    ('gmru-darkin-vladmorribport', 'target'): 'Порты и инфраструктура',
    ('gmru-darkin-vladmorribport', 'buyer'): 'Порты и инфраструктура',
    ('gmru-strana-development-sreda', 'target'): 'Недвижимость',
    ('gmru-strana-development-sreda', 'buyer'): 'Строительство',
    ('gmru-sollers-jf-mould', 'target'): 'Автопром',
    ('gmru-sollers-jf-mould', 'buyer'): 'Автопром',
    ('gmru-veb-gtlk', 'target'): 'Транспорт и логистика',
    ('gmru-nspk-privatization', 'target'): 'Финтех',
    ('gmru-nspk-privatization', 'seller'): 'Банки',
    ('gbcc32684', 'target'): 'Ритейл',
    ('g13d60ebc', 'target'): 'ИТ и интернет',
    ('g1f302e4f', 'target'): 'Здравоохранение',
    ('gad241bb3', 'target'): 'Фармацевтика',
    ('gad241bb3', 'buyer'): 'Фармацевтика',
    ('gad241bb3', 'seller'): 'Фармацевтика',
    ('gb0759159', 'target'): 'Энергетика',
    ('gacc757b6', 'seller'): 'ИТ и интернет',
    ('g92ef210a', 'target'): 'Машиностроение',
    ('g92ef210a', 'buyer'): 'Машиностроение',
    ('geb221705', 'target'): 'E-commerce',
    ('g6e1bb001', 'target'): 'Порты и инфраструктура',
    ('g24b33459', 'target'): 'Недвижимость',
    ('g24b33459', 'seller'): 'Управление активами',
    ('g4dd7a75c', 'target'): 'Машиностроение',
    ('g4dd7a75c', 'seller'): 'Машиностроение',
    ('g97a481d8', 'target'): 'Финтех',
    ('g97a481d8', 'seller'): 'Холдинги',
    ('g17a6fd62', 'target'): 'Автопром',
    ('g17a6fd62', 'buyer'): 'Автопром',
    ('g17a6fd62', 'seller'): 'ИТ и интернет',
    ('gc44de028', 'target'): 'Недвижимость',
    ('gc44de028', 'buyer'): 'Недвижимость',
    ('gd3769bb9', 'target'): 'Автопром',
    ('g1a626d5b', 'target'): 'ИТ и интернет',
    ('gdfce7e3d', 'target'): 'Недвижимость',
    ('gdfce7e3d', 'seller'): 'Недвижимость',
    ('gc5951fac', 'target'): 'ИТ и интернет',
    ('gfa114edc', 'buyer'): 'ИТ и интернет',
    ('gfa114edc', 'seller'): 'ИТ и интернет',
    ('gf70a43e6', 'buyer'): 'Фармацевтика',
    ('gf70a43e6', 'seller'): 'Фармацевтика',
    ('gbf6f6432', 'target'): 'Производство тары',
    ('gbf6f6432', 'buyer'): 'Финансовые услуги',
    ('g21795ec9', 'target'): 'ИТ и интернет',
    ('g6d73538c', 'buyer'): 'Недвижимость',
    ('g5647e100', 'target'): 'Пищепром и напитки',
    ('g5647e100', 'buyer'): 'Финансовые услуги',
    ('g0431fc51', 'target'): 'Потребительские товары',
    ('g0431fc51', 'buyer'): 'ИТ и интернет',
    ('gac1a0c11', 'target'): 'ИТ и интернет',
    ('g80f18d3d', 'target'): 'Недвижимость',
    ('g9254527a', 'buyer'): 'Недвижимость',
    ('g8827d795', 'buyer'): 'Нефть и газ',
    ('g677f3309', 'target'): 'Ритейл',
    ('g677f3309', 'buyer'): 'Финансовые услуги',
    ('g692dcc6b', 'target'): 'Агро',
    ('g692dcc6b', 'seller'): 'Холдинги',
    ('g998e5eb5', 'target'): 'Банки',
    ('g998e5eb5', 'buyer'): 'Банки',
    ('g8f7479bd', 'seller'): 'Строительство',
    ('gab0f3dde', 'target'): 'Транспорт и логистика',
    ('g94268c8d', 'buyer'): 'Транспорт и логистика',
    ('g7f6d55a9', 'buyer'): 'Нефть и газ',
    ('g7f6d55a9', 'seller'): 'Нефть и газ',
    ('g18a6d375', 'target'): 'Образование',
    ('g15386e04', 'target'): 'Профессиональные услуги',
    ('g0551fc60', 'buyer'): 'Финансовые услуги',
    ('g0551fc60', 'seller'): 'Управление активами',
    ('gda6baa02', 'target'): 'ИТ и интернет',
    ('gda6baa02', 'buyer'): 'ИТ и интернет',
    ('ga525c46b', 'target'): 'Гостиницы и туризм',
    ('ga525c46b', 'buyer'): 'Гостиницы и туризм',
    ('gd1771616', 'buyer'): 'Недвижимость',
    ('gd1771616', 'seller'): 'Недвижимость',
    ('gebead2e8', 'target'): 'ИТ и интернет',
    ('g8b03762d', 'target'): 'ИТ и интернет',
    ('g9076dfc3', 'target'): 'Пищепром и напитки',
    ('g9076dfc3', 'buyer'): 'Пищепром и напитки',
    ('g3f0400db', 'target'): 'ИТ и интернет',
    ('g6bf41023', 'buyer'): 'Рынок ценных бумаг',
    ('gb9a22f5f', 'seller'): 'Пищепром и напитки',
    ('ge283bafc', 'seller'): 'Строительство',
    ('g8d7794d0', 'target'): 'ГМК и добыча',
    ('g8d7794d0', 'buyer'): 'ГМК и добыча',
    ('g8d7794d0', 'seller'): 'ГМК и добыча',
    ('gc7e35605', 'target'): 'Машиностроение',
    ('gc7e35605', 'buyer'): 'Образование',
    ('gad66fcec', 'buyer'): 'Управление активами',
    ('gad66fcec', 'seller'): 'Недвижимость',
    ('g9108dfd0', 'target'): 'Недвижимость',
    ('g9108dfd0', 'seller'): 'Управление активами',
    ('gabdbe320', 'target'): 'Пищепром и напитки',
    ('gabdbe320', 'buyer'): 'Транспорт и логистика',
    ('g60f99ba6', 'buyer'): 'Нефть и газ',
    ('g2c27516d', 'seller'): 'Пищепром и напитки',
    ('gb0f1f736', 'target'): 'Медиа',
    ('gaee6179c', 'target'): 'Недвижимость',
    ('gaee6179c', 'seller'): 'Строительство',
    ('g70c0a9ff', 'target'): 'Медиа',
    ('g70c0a9ff', 'buyer'): 'Медиа',
    ('gd9ccfdd2', 'target'): 'ИТ и интернет',
    ('gddb34475', 'target'): 'Недвижимость',
    ('gddb34475', 'buyer'): 'Недвижимость',
    ('g61b33118', 'target'): 'Агро',
    ('ge0cc0dfe', 'target'): 'Уголь',
    ('g6c5c2e6a', 'target'): 'Пищепром и напитки',
    ('gc52a53dd', 'target'): 'Недвижимость',
    ('gbc7b1e8d', 'buyer'): 'Недвижимость',
    ('gbc7b1e8d', 'seller'): 'Недвижимость',
    ('g3ecb7b86', 'seller'): 'Машиностроение',
    ('g45a72968', 'target'): 'Здравоохранение',
}


def gen_id(name):
    return 'g' + hashlib.sha1(name.encode('utf-8')).hexdigest()[:8]


def main(write):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    comps = data['companies']
    match_keys = data['match_keys']
    by_id = {d['id']: d for d in data['deals']}

    with open(REPORTS, encoding='utf-8') as f:
        records = json.load(f)

    existing_key_index = {}
    for cid, c in comps.items():
        existing_key_index.setdefault(link_parties.company_key(c['name']), []).append(cid)

    created = {}   # (card_id, role) -> new profile id
    id_to_name = {}
    n_new = n_existing = n_skipped = n_excluded = 0

    # Первый проход — создать профили (нужно ДО применения ссылок, потому
    # что запись «existing» на g9108dfd0 ссылается на id, вычисленный от
    # имени профиля, заведённого записью «new» на gad66fcec).
    for r in records:
        card_id, role = r['card_id'], r['role']
        if r['verdict'] != 'new':
            continue
        if (card_id, role) in EXCLUDE:
            n_excluded += 1
            continue
        name = RENAME.get((card_id, role), r['proposed_name'])
        cid = gen_id(name)
        ind = INDUSTRY[(card_id, role)]

        if cid in comps:
            # Тот же новый профиль уже заведён по другой роли/карточке
            # (пример — ЗПИФ «Вим Недвижимость», см. докстринг) — не
            # создавать второй раз, только использовать.
            assert comps[cid]['name'] == name, (card_id, role, name, comps[cid]['name'])
        else:
            key = link_parties.company_key(name)
            colliders = [c for c in existing_key_index.get(key, []) if c != cid]
            allowed_twin = (name, 'АО «Эдельвейс»') if card_id == 'gd1771616' else None
            for other in colliders:
                other_name = comps[other]['name']
                assert allowed_twin == (name, other_name), (
                    'незадокументированная коллизия ключа', name, other, other_name)
            comps[cid] = {'name': name, 'ind': ind, 'desc': r['proposed_desc'],
                          'kpi': ['Профиль', 'Автоматический']}
            mk = r.get('proposed_match_keys') or []
            if mk:
                match_keys[cid] = mk
            existing_key_index.setdefault(key, []).append(cid)
            n_new += 1
        created[(card_id, role)] = cid
        id_to_name[cid] = name

    # Второй проход — проставить ссылки (и для «new», и для «existing»).
    applied = []
    for r in records:
        card_id, role = r['card_id'], r['role']
        if r['verdict'] not in ('new', 'existing'):
            continue
        if (card_id, role) in EXCLUDE:
            continue
        if r['verdict'] == 'existing':
            cid = r['profile_id']
            assert cid in comps, (card_id, role, 'ссылается на несуществующий профиль', cid)
        else:
            cid = created[(card_id, role)]

        card = by_id.get(card_id)
        assert card is not None, ('карточки нет в базе', card_id)
        text_field = TEXT_FIELD[role]
        assert card.get(text_field) == r['text'], (
            card_id, role, 'текст поля уже другой', card.get(text_field), r['text'])
        id_field = ID_FIELD[role]
        assert not card.get(id_field), (card_id, role, 'уже привязано', card.get(id_field))
        for gf in GUARD_FIELDS[role]:
            assert not card.get(gf), (card_id, role, 'guard-поле занято', gf)

        applied.append((card_id, role, id_field, cid, text_field))

    # Конфликт роли: один и тот же профиль не может занять две роли одной
    # карточки — проверяем по итоговому набору применений, а не только
    # против уже стоявших в базе полей (та же граница, что у
    # `test_one_company_holds_one_role_in_a_deal`).
    by_card = {}
    for card_id, role, id_field, cid, text_field in applied:
        by_card.setdefault(card_id, []).append((role, cid))
    for card_id, pairs in by_card.items():
        seen = {}
        for role, cid in pairs:
            assert cid not in seen, (card_id, 'один профиль в двух ролях', seen, role, cid)
            seen[cid] = role

    for card_id, role, id_field, cid, text_field in applied:
        card = by_id[card_id]
        card[id_field] = cid
        if id_field == 'buyer':
            card.pop('buyer_name', None)
        n_existing += 0  # verdict counted above

    n_skipped = sum(1 for r in records if r['verdict'] in ('not_a_company', 'unclear'))

    print('Новых профилей создано: %d' % n_new)
    print('Ссылок проставлено (new+existing): %d' % len(applied))
    print('Исключено (решение приёмки сильнее): %d' % n_excluded)
    print('Пропущено (не компания / неясно): %d' % n_skipped)

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('Сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    main('--write' in sys.argv)
