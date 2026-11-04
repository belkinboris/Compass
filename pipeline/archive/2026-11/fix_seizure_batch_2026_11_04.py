"""Правки новых карточек изъятий после проверок test_data (4 ноября 2026): даты, «Согласования» с органом,
кавычки и тире, форма предмета, лишнее издание в тексте, реестр лота. Запуск: [--write]."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
R = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
d = json.load(open(P, encoding='utf-8')); by = {x['id']: x for x in d['deals']}
reg = json.load(open(R, encoding='utf-8'))

# 1. месяц без дня — только год (допустимые виды даты: ГГГГ-ММ-ДД, ГГГГ, unknown)
for i in ('ce56cdefd', 'gd8d09f21', 'g2076ee30', 'g0931ed04', 'g1c0e9175', 'g8ef5f397', 'g8b071b30', 'g969c85c1'):
    by[i]['date'] = by[i]['date'][:4]

# 2. «Согласования» называют орган
CARPRICE = 'Решение принял Тверской районный суд Москвы. Московский городской суд 26 мая 2026 года оставил решение почти без изменений; жалобы третьих лиц, чье имущество тоже изъяли, рассматривать отказался.'
for i in ('gb92f7119', 'g3a168646', 'gece7ec74', 'gf3c6c82e', 'gf47051a2'):
    by[i]['law']['appr'] = CARPRICE
def prefix(i, text):
    a = by[i]['law']['appr']
    by[i]['law']['appr'] = text + ' ' + a
prefix('ce56cdefd', 'Решение вынес Никулинский районный суд Москвы.')
prefix('g8b071b30', 'Решение вынес Никулинский районный суд Москвы.')
prefix('g146df6ac', 'Решение принял Ленинский районный суд Курска.')
prefix('g2076ee30', 'Решение принял суд по иску Генпрокуратуры.')
prefix('g24fe6d49', 'Решение принял Ленинский районный суд Курска.')
prefix('g290a0a0e', 'Решение вынес Ленинский районный суд Екатеринбурга.')
for i in ('g4f9a1741', 'g6f98005b'):
    by[i]['law']['appr'] = 'Компании перешли государству по иску Генпрокуратуры, который рассматривал Никулинский районный суд Москвы; ' + by[i]['law']['appr'][0].lower() + by[i]['law']['appr'][1:]
prefix('g77aa1026', 'Решение принял Московский районный суд Санкт-Петербурга.')
prefix('g8ef5f397', 'Решение принял Хамовнический суд Москвы.')
prefix('gd2ee3313', 'Решение принял Замоскворецкий суд Москвы.')
prefix('gd8d09f21', 'Решение принял Лабинский городской суд Краснодарского края.')
prefix('gee8893dd', 'Решение принял Ленинский районный суд Екатеринбурга.')

# 3. кавычки и тире
by['c374fc2ca']['eco']['share'] = by['c374fc2ca']['eco']['share'].replace('ООО «Пивоваренная компания «Балтика»:', 'ООО «Пивоваренная компания «Балтика»»:')
by['g146df6ac']['eco']['share'] = by['g146df6ac']['eco']['share'].replace('ООО «КЦ «Мерлетто».', 'ООО «КЦ «Мерлетто»».')
for i, fields in (('gba396687', ('share',)), ('g146df6ac', ('target_fin', 'context'))):
    for f in fields:
        by[i]['eco'][f] = by[i]['eco'][f].replace(' - ', ' — ')

# 4. форма предмета: где размер доли не назван, предмет в контекст, поле — «—»
def share_to_context(i):
    eco = by[i]['eco']; old = eco['share']
    if old not in (eco.get('context') or ''):
        eco['context'] = old.rstrip('.') + '. ' + (eco.get('context') or '')
    eco['share'] = '—'
for i in ('g290a0a0e', 'gd8d09f21', 'gd2ee3313', 'gf0258897', 'gba396687'):
    share_to_context(i)
by['g77aa1026']['eco']['share'] = ('100% акций АО «Рольф» (ими владели Delance Limited и ООО «Рольф Моторс»), а также 100% долей '
                                   'в ООО «Рольф Моторс», ООО «Рольф Эстейт Санкт-Петербург» и ООО «Рольф Тех».')
old = by['c4e275305']['eco']['share']
by['c4e275305']['eco']['context'] = old.rstrip('.') + '. ' + by['c4e275305']['eco']['context']
by['c4e275305']['eco']['share'] = '100% доли в ООО «ПКМТП» (прежние владельцы — Александр Иванчей, Камчатское морское пароходство и «Новкам»).'

# 5. нежелательное издание в тексте карточки Batilogistic
c = by['gf93ab76b']
c['eco']['context'] = c['eco']['context'].replace(' Moscow Times сообщает, что эти общества названы в указе наряду с FM Logistic.', ' В указе они названы наряду с FM Logistic.')
c['accepted_notes']['searched'] = c['accepted_notes']['searched'].replace('Moscow Times (справка об активах), ', '')

# 6. профиль-лот «Южгазэнерджи + Кейтеринг-Юг» не имеет единого ИНН
for r in reg:
    if r['company_id'] == 'g097e34b2-target':
        r.update(decision='lot', inn=None, reason='Профиль — лот из двух юрлиц («Южгазэнерджи» и «Кейтеринг-Юг», проданы одним лотом): единого ИНН у лота нет. '
                 'ИНН ООО «Южгазэнерджи» — 0105046700 (saby.ru), 4 ноября 2026.')
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(reg, open(R, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')
else:
    print('сухой прогон ok')
