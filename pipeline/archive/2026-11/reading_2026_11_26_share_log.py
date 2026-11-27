"""Вычитка 26.11.2026: языковые правки eco.share (proofread) — подтверждение словами
источника в fact_log для fact_edit_guard; g9c218ea2 — вернуть «доли» (вычитка его сняла).
Цитаты — дословно из текстов статей на диске (data/inbox/raw)."""
import json, sys
sys.path.insert(0, 'pipeline')
import fact_edit_guard as g
P = 'static/data/deals_promoted.json'
BY = 'вычитка 26.11.2026'
G9C_OLD = '65% в ООО «СТГТ» и доля в ООО «Воронежский трансформатор»'
G9C_NEW = '65% доли в ООО «СТГТ» и доля в ООО «Воронежский трансформатор»'
ROWS = {
 'g8302ab18': ('По его словам, при выходе на рынок ожидается «довольно стандартный free-float» — в районе 20%.',
               'https://www.kommersant.ru/doc/9024385'),
 'g62577a1d': ('Московский производитель плавленых сыров «Карат» завершил сделку по покупке Павловского молочного завода, который выпускает молочную продукцию под брендом «Эго», а также сыры Cremeitali. Об этом РБК сообщили в пресс-службе «Карата». Сумму сделки там не раскрывают.',
               'https://news.mail.ru/society/72713374/'),
 'gf31c1d53': ('предприятие приобрело недвижимость и производственное оборудование ювелирного завода «ПАРС», расположенного в поселке Красное-на-Волге Костромской области.',
               'https://dela.ru/news/301689/'),
 'g11e381eb': ('На четырех производственных площадках, ставших предметом сделки, трудятся 724 человека.',
               'https://www.interfax.ru/business/860502'),
 'g58ebb771': ('Согласно сообщению компании, бизнес в РФ будет продан основателю всей группы Игорю Боровикову за символический $1.',
               'https://www.interfax.ru/russia/866876'),
 'g9c218ea2': ('Компания « Интер РАО » выкупила 65%-ную долю Siemens Energy в совместном с «Силовыми машинами» предприятии – ленинградском «Сименс Технологии газовых турбин» (СТГТ) … структура компании – голландская RAO Intertech B.V. – 11 октября стала собственником воронежского завода Siemens Energy – ООО «Воронежский трансформатор»',
               'https://www.vedomosti.ru/business/news/2022/10/14/945601-inter-rao-priobrela-doli-siemens'),
 'g9b852635': ('Группа «Эталон» выставила на продажу два участка в Нагатинской пойме общей площадью 2,2 га. … Речь идет о двух участках в Даниловском районе, часть территории относится к проекту комплексного развития территорий (КРТ).',
               'https://mperspektiva.ru/topics/etalon-vystavil-na-prodazhu-16-aktivov-v-shesti-regionakh-rossii/'),
 'g25aaf2c0': ('Здание находится по адресу Пятницкая, 15. Общая площадь здания — свыше 1 тыс. кв. м. Как следует из отчета об оценке, здание является выявленным объектом культурного наследия',
               'https://realty.rbc.ru/news/6aad0fe739f83eb70d0c9aec'),
}
d = json.load(open(P, encoding='utf-8'))
for c in d['deals']:
    if c['id'] not in ROWS: continue
    eco = c.setdefault('eco', {})
    if c['id'] == 'g9c218ea2':
        assert eco.get('share') == G9C_OLD, eco.get('share')
        eco['share'] = G9C_NEW
    q, u = ROWS[c['id']]
    if not any(r.get('field') == 'eco.share' and r.get('new') == eco['share'] for r in c.get('fact_log') or []):
        g.log(c, 'eco.share', eco['share'], q, u, BY); print('log', c['id'])
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('written')
