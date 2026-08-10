# -*- coding: utf-8 -*-
"""Два близнеца компаний плюс пять описаний — G2, партия 18.

БЛИЗНЕЦЫ.

* «Нетология-групп» (`ga09e7dfc`, именительный, сделка «Сбер приобрёл
  Нетологию и Фоксфорд у Мордашова») / «Нетологии-групп» (`g74c40349`,
  родительный, сделка «IndaSpace привлёк 6 млн рублей... от основателя
  «Нетологии-групп» Максима Спиридонова») — тот же падежный рисунок, что
  во всех прошлых волнах: у ОБОИХ была своя сделка.

* «ООО «Домиленд»» (`g0e121b1b`) / «Платформа Домиленд» (`gb7833cdd`) —
  НЕ падежный вариант, а разное имя ОДНОЙ компании в двух сделках
  подряд: `g150f6855` («Самолёт» купил 76% IT-компании «Клиентский
  сервис» (ООО «Домиленд»), ранее принадлежавшей структурам ВТБ) и
  `g64141daa` («Яндекс купил оставшуюся долю в Домиленд» — та же сделка
  прямо говорит: «В январе Самолёт выкупил 75,7% компании Клиентский
  сервис (владельца Домиленда), Яндекс выкупил оставшуюся долю у
  Самолёта»). Это не совпадение имени (урок CLAUDE.md про «Каму» и
  «Акрон Холдинг») — вторая сделка ЯВНО описывает первую как
  предыдущий шаг той же истории владения, с тем же гендиректором
  (Дарья Воронова). Выживает `g0e121b1b` — юридическое имя ближе к
  тому, что называет вторая (более специфичная) сделка.

ОПИСАНИЯ. Кандидаты — узнаваемые имена среди профилей без описания;
для каждого прочитан текст его собственной сделки в базе перед
написанием текста (урок CLAUDE.md про «Акрон Холдинг»).

Запуск:
    python3 pipeline/merge_twins_and_describe_batch18.py            # сухой прогон
    python3 pipeline/merge_twins_and_describe_batch18.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

# (dup_id, survivor_id, [deal_ids], ожидаемое имя дубля, ожидаемое имя выжившего)
CLUSTERS = [
    ('g74c40349', 'ga09e7dfc', ['g92c6a8ce'], 'Нетологии-групп', 'Нетология-групп'),
    ('gb7833cdd', 'g0e121b1b', ['g64141daa'], 'Платформа Домиленд', 'ООО «Домиленд»'),
]

DESCRIPTIONS = {
    'ga09e7dfc': 'Российская edtech-платформа, объединяет школу '
                 'дополнительного профессионального образования '
                 '«Нетология» и онлайн-школу для школьников «Фоксфорд»; '
                 'в 2021 году куплена Сбером у структуры «Северстали».',
    'g0e121b1b': 'Российская IT-платформа для управления жилой '
                 'недвижимостью (сервис «Домиленд»); в 2024–2025 годах '
                 'перешла от структур ВТБ к «Самолёту», а затем к '
                 'Яндексу.',
    'g41bf9d28': 'Российская независимая нефтегазовая компания '
                 'Эдуарда Худайнатова.',
    'g22f45541': 'Российская дочерняя структура американского банка '
                 'Goldman Sachs; в 2025 году продана фонду Balchug '
                 'Capital.',
    'gf4733fef': 'Российский производитель автомобилей люксового '
                 'класса под брендом Aurus, дочерняя структура ФГУП '
                 '«НАМИ».',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    companies = data['companies']
    deals = data['deals']

    for dup_id, survivor_id, deal_ids, dup_name, survivor_name in CLUSTERS:
        assert companies[dup_id]['name'] == dup_name, 'дубль %s уже не тот' % dup_id
        assert companies[survivor_id]['name'] == survivor_name, 'выживший %s уже не тот' % survivor_id

        full_text_refs = sorted(d['id'] for d in deals if dup_id in json.dumps(d, ensure_ascii=False))
        assert full_text_refs == sorted(deal_ids), (
            'дубль %s встречается не только в учтённых сделках: %r' % (dup_id, full_text_refs))

        print('СЛИВАЕМ  %s -> %s (%s)' % (dup_id, survivor_id, survivor_name))
        print('ПЕРЕНАПРАВЛЯЕМ  сделки', deal_ids)

        if not write:
            continue

        for d in deals:
            if d.get('id') in deal_ids:
                if d.get('target') == dup_id:
                    d['target'] = survivor_id
                if d.get('buyer') == dup_id:
                    d['buyer'] = survivor_id
                if d.get('seller_id') == dup_id:
                    d['seller_id'] = survivor_id
                if d.get('asset_id') == dup_id:
                    d['asset_id'] = survivor_id

        survivor_aliases = set(data['match_keys'].get(survivor_id, []))
        survivor_aliases.update(data['match_keys'].pop(dup_id, []))
        data['match_keys'][survivor_id] = sorted(survivor_aliases)

        data.setdefault('merged_companies', {})[dup_id] = survivor_id
        del companies[dup_id]

    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = companies.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 260, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  %-12s %-34s %s' % (cid, str(c.get('name'))[:34], text[:56]))
        if write:
            c['desc'] = text
        wrote += 1

    print('\nОписаний записано: %d' % wrote)
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
