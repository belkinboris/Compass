# -*- coding: utf-8 -*-
"""Сорок вторая партия: разбор коллизии профиля «Кама» + 8 описаний.

НАЙДЕНО. Профиль gcc2d3689 «Кама» нёс три сделки, из которых ДВЕ — про
одну и ту же компанию (ООО «Кама», единственный в России производитель
мелованного картона, ЦБК; куплена структурами Виктора Харитонина у банка
«Траст» в 2023 году), а ТРЕТЬЯ (g6e3bcb70, «Росатом через Рэнеру купил
долю в разработчике электромобиля Атом (АО Кама)») — про совсем другую
компанию: разработчика электромобиля «Атом», основанного главой КамАЗа
Сергеем Когогиным и Рубеном Варданяном. Один и тот же профиль
представлял двух разных юрлиц с совпадающим коротким именем — родня
урока CLAUDE.md про «Акрон Холдинг» («конкретно звучащее имя компании
тоже бывает однофамильцем»).

Заодно у профиля-картонщика и у обеих его сделок стояла неверная отрасль
(«Пищепром и напитки» / «Химия и удобрения») — для целлюлозно-бумажного
комбината это «Лесопром».

ЧТО ДЕЛАЕТ.
1. Создаёт новый профиль для АО «Кама» (проект электромобиля «Атом»),
   переносит на него `target` сделки g6e3bcb70.
2. Правит отрасль профиля-картонщика gcc2d3689 и обеих его сделок на
   «Лесопром».
3. Проставляет описания 8 профилям, где кандидат читался по своим же
   связанным сделкам (Денис Избрехт, структуры Игоря Кима, структуры
   Виктора Харитонина, Augment Investments, «Акрон Холдинг», ООО «Стинн»,
   Умар Кремлев, Артём Чайка) и обоим профилям «Кама».

Запуск:
    python3 pipeline/split_kama_profile_and_describe_batch42.py            # сухой прогон
    python3 pipeline/split_kama_profile_and_describe_batch42.py --write    # записать
"""
import hashlib
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

KAMA_PAPER_ID = 'gcc2d3689'
ATOM_DEAL_ID = 'g6e3bcb70'
NEW_ATOM_SEED = 'АО «Кама» (проект электромобиля «Атом»), Рэнера 2024'
NEW_ATOM_NAME = 'АО «Кама» (проект электромобиля «Атом»)'

DESCRIPTIONS = {
    'g388b0f09': 'Бизнесмен, владелец ГК «Интегра»; в 2023–2026 годах '
                 'купил у Росимущества «Первую образцовую типографию» и '
                 'газодобытчика «Южгазэнерджи», а также маслозавод '
                 '«Исток» в Лисках.',
    'ge370cfae': 'Структуры банкира Игоря Кима, владельца Экспобанка; в '
                 '2022–2025 годах купили российские лизинговые и '
                 'финансовые «дочки» Volkswagen, Volvo, CNH Industrial '
                 'и ALD Automotive.',
    KAMA_PAPER_ID: 'Единственный в России производитель мелованного '
                   'коробочного картона (ЦБК «Кама»); в 2023 году куплен '
                   'структурами Виктора Харитонина у банка «Траст», в '
                   '2024-м перепродан «Свезе».',
    'g6f5d7e99': 'Глава Международной ассоциации бокса (IBA); владеет '
                 'автодилером «Рольф», девелопером AVA Group и '
                 'сертификационными компаниями «Сертификейшен Групп» и '
                 '«Серконс».',
    'gf8c255bb': 'Структуры совладельца «Фармстандарта» Виктора '
                 'Харитонина; ведут переговоры о покупке российского '
                 'бизнеса Reckitt и доли в сети медцентров «Медскан».',
    'g0b9343f2': 'Кипрская структура, связанная с Виктором Харитониным; '
                 'через неё куплен производитель картона «Кама», а '
                 'сделка по покупке комбината Mondi Сыктывкарский не '
                 'состоялась.',
    'g39f180b4': 'Не относится к производителю удобрений «Акрон»; '
                 'машиностроительный холдинг, купивший трансформаторный '
                 'завод в ОАЭ и петербургский завод «Транскат».',
    'g3817a50b': 'Холдинг Григория Садояна, контролирующий крупнейшее '
                 'рекламное агентство Russ и Russ Outdoor; в 2023 году '
                 'купил через Russ Outdoor агентство Gallery (Медиа-1 '
                 'Аутдор).',
    'gbef46925': 'Сын экс-генпрокурора Юрия Чайки; в 2023–2024 годах '
                 'консолидировал 99% девелопера 3S Group (Ульяновск).',
}

NEW_ATOM_DESC = ('Разработчик российского электромобиля «Атом», основан '
                  'главой КамАЗа Сергеем Когогиным и Рубеном Варданяном; '
                  'в 2024 году «Рэнера» (структура Росатома) вошла в '
                  'капитал за 6,2 млрд ₽.')


def new_id(seed, existing):
    cid = 'g' + hashlib.sha1(seed.encode('utf-8')).hexdigest()[:8]
    assert cid not in existing, 'коллизия id: %s' % cid
    return cid


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    deals = data['deals']
    by_id = {d['id']: d for d in deals}

    # --- 1. разбор коллизии «Кама» ---
    kama = comps[KAMA_PAPER_ID]
    assert kama['name'] == 'Кама', 'имя профиля Кама уже изменено'
    assert kama.get('ind') == 'Пищепром и напитки', 'отрасль Кама уже изменена'
    atom_deal = by_id[ATOM_DEAL_ID]
    assert atom_deal['target'] == KAMA_PAPER_ID, 'target сделки Атом уже не Кама'
    assert atom_deal['title'].startswith('Росатом через Рэнеру'), 'сделка Атом не та'

    existing_ids = set(comps.keys())
    existing_names = {c.get('name') for c in comps.values()}
    assert NEW_ATOM_NAME not in existing_names, 'имя нового профиля уже занято'
    aid = new_id(NEW_ATOM_SEED, existing_ids)
    print('НОВЫЙ ПРОФИЛЬ  %-12s %s' % (aid, NEW_ATOM_NAME))

    print('ПЕРЕНОС TARGET  %s: %s -> %s' % (ATOM_DEAL_ID, KAMA_PAPER_ID, aid))

    g0431 = by_id.get('g703d5597')
    g6ef2 = by_id.get('g6ef203a1')
    assert g0431 and g0431.get('ind') == 'Пищепром и напитки'
    assert g6ef2 and g6ef2.get('ind') == 'Химия и удобрения'
    print('ОТРАСЛЬ  g703d5597: Пищепром и напитки -> Лесопром')
    print('ОТРАСЛЬ  g6ef203a1: Химия и удобрения -> Лесопром')
    print('ОТРАСЛЬ  %s: Пищепром и напитки -> Лесопром' % KAMA_PAPER_ID)

    if write:
        comps[aid] = {'name': NEW_ATOM_NAME, 'ind': 'Автопром', 'desc': NEW_ATOM_DESC}
        atom_deal['target'] = aid
        g0431['ind'] = 'Лесопром'
        g6ef2['ind'] = 'Лесопром'
        kama['ind'] = 'Лесопром'

    # --- 2. описания ---
    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  ОПИСАНИЕ %-12s %-40s %s' % (cid, str(c.get('name'))[:40], text[:50]))
        if write:
            c['desc'] = text
        wrote += 1

    print('\nОписаний записано: %d' % wrote)
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

    real = sum(1 for v in comps.values()
               if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
    print('Всего профилей с описанием: %d из %d (%d%%)'
          % (real, len(comps), round(100 * real / len(comps))))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
