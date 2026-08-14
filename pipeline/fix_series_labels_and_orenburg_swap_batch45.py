# -*- coding: utf-8 -*-
"""Сорок пятая партия: систематический промер + 4 находки + 6 описаний.

СИСТЕМАТИЧЕСКИЙ ПРОМЕР (закрывает вопрос с прошлого прогона). Три
прогона подряд (82–84) находили по одной испорченной ссылке `target`
при обычном чтении G2-кандидатов — записана рекомендация промерить
класс целиком. Промер (сигнал: изолированный профиль-`target`, чьё имя
стоит рядом с «Продавец — <имя>» / «<имя> вышел из капитала» / «<имя>
сохранил») дал ТОЛЬКО ОДИН кандидат сверх уже исправленных —
`g57a44f07` («Эйдос Робототехника»), и он неоднозначен: `extra`
одновременно называет ООО «Эйдос Робототехника» и продавцом, и (через
заголовок) предметом сделки, а отдельного профиля АО «Эйдос
Робототехника» (упомянутого в тексте как оперирующее юрлицо) в базе
нет. Без источника не разобрать, кто здесь кто, — трогать не стал
(«досочинить обрубленный факт — не вариант»). Класс не оказался
достаточно частым для отдельного скрипта — измерен и закрыт разовым
прогоном, не автоматизирован.

ЗАТО ПРИ ЧТЕНИИ G2-КАНДИДАТОВ НАШЛИСЬ ЧЕТЫРЕ ДРУГИХ ДЕФЕКТА:

1–2. РАУНД ЗАПИСАН КАК ИМЯ КОМПАНИИ. Профили `g2d8c2e9b` «Series C» и
   `g24a9539d` «Раунд Series A» — название типа раунда, а не компании;
   единственные сделки, где они стоят `target`, называют настоящую
   компанию прямо в заголовке (inDriver, EBAC Online). Переименованы на
   месте (тот же id, та же единственная сделка) — это не смена
   личности, а исправление опечатки парсера: профиль никогда не
   представлял никакой реальной сущности под старым именем.

3. ПОКУПАТЕЛЬ ЗАПИСАН КАК ПРЕДМЕТ. У сделки g99cb85c4 («Приобретение
   «АБС Оренбург» 100% АО «Аэропорт Оренбург»») `target` указывал на
   профиль `g9cd973e3` «АБС Оренбург» — а по тексту именно «АБС
   Оренбург» (СП «Аэропортов регионов» Вексельберга и «Новапорт
   Холдинга» Троценко) ВЫИГРАЛО аукцион и купило актив, `buyer` при
   этом был пуст. Создан профиль «АО «Аэропорт Оренбург»» (предмет —
   аэропорты Оренбурга и Орска, авиакомпания «Оренбуржье»), `target`
   перенесён на него, «АБС Оренбург» перенесён в `buyer`.

4. НЕЯСНОЕ ИМЯ АКТИВА. Профиль `g89a7a2a8` «Арктическое» — название
   месторождения без пояснения, что это лицензия, а не компания;
   переименован в «Лицензия на Арктическое месторождение (Ямал)» по
   тексту той же сделки (она же называет соседнее «Нейтинское» —
   родственный, не переименованный профиль для сравнения формата
   оставлен на будущее).

Плюс 6 описаний обычным G2-кандидатам.

Запуск:
    python3 pipeline/fix_series_labels_and_orenburg_swap_batch45.py            # сухой прогон
    python3 pipeline/fix_series_labels_and_orenburg_swap_batch45.py --write    # записать
"""
import hashlib
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

# --- 1-2: переименование на месте ---
RENAMES = {
    'g2d8c2e9b': ('Series C', 'inDriver'),
    'g24a9539d': ('Раунд Series A', 'EBAC Online'),
    'g89a7a2a8': ('Арктическое', 'Лицензия на Арктическое месторождение (Ямал)'),
}
NEW_ALIASES = {
    'g2d8c2e9b': ['indriver'],
    'g24a9539d': ['ebac online', 'ebac'],
}

# --- 3: свап buyer/target для Оренбургского аэропорта ---
ORENBURG_DEAL_ID = 'g99cb85c4'
ABS_ID = 'g9cd973e3'
AIRPORT_SEED = 'АО «Аэропорт Оренбург», аэропорты Оренбурга и Орска, Оренбуржье'
AIRPORT_NAME = 'АО «Аэропорт Оренбург»'
AIRPORT_DESC = ('Владеет аэропортами Оренбурга и Орска и авиакомпанией '
                 '«Оренбуржье»; в 2021 году куплен СП «Аэропортов '
                 'регионов» и «Новапорт Холдинга» за 3,193 млрд ₽.')

DESCRIPTIONS = {
    'g2d8c2e9b': 'Платформа для заказа такси и поездок; в 2021 году '
                 'привлекла $150 млн (раунд Series C) и стала '
                 'единорогом с оценкой $1,23 млрд.',
    'g24a9539d': 'Бразильская EdTech-платформа; в 2021 году привлекла '
                 'раунд Series A на $11 млн во главе с Baring Vostok.',
    'g89a7a2a8': 'Лицензия НОВАТЭКа на нефтегазовое месторождение на '
                 'Ямале; куплена на аукционе в 2021 году за 10,877 '
                 'млрд ₽.',
    'gc9bafa49': 'Автодилерский холдинг; в 2025 году купил у '
                 '«Ингосстраха» 99,99% акций «Ингосстрах Банка» за '
                 '18,1 млрд ₽.',
    'gbd8b9d63': 'Бизнесмен и миноритарный акционер ВТБ; в 2026 году '
                 'нарастил долю в банке с 4,82% до 5,33% в ходе SPO.',
    'gca80a12c': 'Казахстанское ТОО; в 2021 году выиграло аукцион ЦБ '
                 'РФ на 100% санированного Азиатско-Тихоокеанского '
                 'банка за около 14 млрд ₽.',
}


def new_id(seed, existing):
    cid = 'g' + hashlib.sha1(seed.encode('utf-8')).hexdigest()[:8]
    assert cid not in existing, 'коллизия id: %s' % cid
    return cid


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    mk = data['match_keys']
    by_id = {d['id']: d for d in data['deals']}

    # --- переименования на месте ---
    for cid, (old, new) in RENAMES.items():
        assert comps[cid]['name'] == old, 'профиль %s уже переименован' % cid
        existing_names = {c.get('name') for c in comps.values()}
        assert new not in existing_names, 'имя %r уже занято' % new
        print('ПЕРЕИМЕНОВАНИЕ  %-12s %r -> %r' % (cid, old, new))
        if write:
            comps[cid]['name'] = new
            if cid in NEW_ALIASES:
                mk[cid] = NEW_ALIASES[cid]

    # --- свап buyer/target для Оренбургского аэропорта ---
    deal = by_id[ORENBURG_DEAL_ID]
    assert deal['target'] == ABS_ID, 'target сделки уже не АБС Оренбург'
    assert deal.get('buyer') is None, 'buyer сделки уже заполнен'
    assert comps[ABS_ID]['name'] == 'АБС Оренбург'

    existing_ids = set(comps.keys())
    existing_names = {c.get('name') for c in comps.values()}
    assert AIRPORT_NAME not in existing_names, 'имя нового профиля уже занято'
    aid = new_id(AIRPORT_SEED, existing_ids)
    print('НОВЫЙ ПРОФИЛЬ  %-12s %s' % (aid, AIRPORT_NAME))
    print('ПЕРЕНОС TARGET  %s: %s -> %s' % (ORENBURG_DEAL_ID, ABS_ID, aid))
    print('ПЕРЕНОС BUYER   %s: None -> %s (АБС Оренбург)' % (ORENBURG_DEAL_ID, ABS_ID))

    if write:
        comps[aid] = {'name': AIRPORT_NAME, 'ind': 'Транспорт и логистика', 'desc': AIRPORT_DESC}
        deal['target'] = aid
        deal['buyer'] = ABS_ID

    # --- описания ---
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
