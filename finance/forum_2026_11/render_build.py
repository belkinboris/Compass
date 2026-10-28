import asyncio, os, sys
from playwright.async_api import async_playwright
OUT=os.path.dirname(os.path.abspath(__file__)); F='/home/user/Compass/static/fonts'
CSS_FONTS='''
@font-face{font-family:'PTS';src:url('file://%(f)s/ptserif-400-cyrillic.woff2') format('woff2');unicode-range:U+0400-04FF,U+2116}
@font-face{font-family:'PTS';src:url('file://%(f)s/ptserif-400-latin.woff2') format('woff2')}
@font-face{font-family:'PTS';src:url('file://%(f)s/PTSerif-Bold.ttf');font-weight:700}
@font-face{font-family:'Man';src:url('file://%(f)s/manrope-cyrillic-400.woff2') format('woff2');font-weight:400;unicode-range:U+0400-04FF,U+2116}
@font-face{font-family:'Man';src:url('file://%(f)s/manrope-cyrillic-500.woff2') format('woff2');font-weight:500;unicode-range:U+0400-04FF,U+2116}
@font-face{font-family:'Man';src:url('file://%(f)s/commissioner-latin.woff2') format('woff2');font-weight:100 900}
'''%{'f':F}
MARK='<svg viewBox="0 0 48 48" width="26" height="26" fill="none" aria-hidden="true"><circle cx="24" cy="24" r="21" stroke="currentColor" stroke-width="2.6"/><g transform="rotate(-38 24 24)"><polygon points="24,5 28.5,24 19.5,24" fill="#C9AE7C"/><polygon points="24,43 28.5,24 19.5,24" fill="currentColor"/></g><circle cx="24" cy="24" r="3.2" fill="#F3F1E9" stroke="currentColor" stroke-width="1.6"/></svg>'
WORD=lambda cls='':'<span class="wordmark %s">%s<span>КО<em>М</em>П<em>А</em>С</span></span>'%(cls,MARK)
QR='<div class="qr"><div class="qrgrid">'+''.join('<i class="%s"></i>'%('on' if (i*7+i//9*3)%5<3 else '') for i in range(81))+'</div><span>QR на живую страницу<br>projectcompass.ru</span></div>'

def tile(n,l,sub=''):
    return '<div class="tile"><b>%s</b><span>%s</span>%s</div>'%(n,l,('<small>%s</small>'%sub if sub else ''))

SESSIONS=[
 dict(n='1',t='9:45',title='Обзор рынка',who='Модератор — Кулешов, ККМП. РСХБ, Яндекс, Старт Капитал, Aspring',
  hand_title='Раздатка · «Рынок M&A в открытых источниках: 2024 → 2025 → 2026»',
  hand='''<table><tr><th></th><th>2024</th><th>2025</th><th>2026 · 10 мес.</th></tr>
<tr><td>сделок в базе, без торгов</td><td>349</td><td>259</td><td>346</td></tr>
<tr><td>сумма раскрыта</td><td>51%</td><td>56%</td><td>50%</td></tr>
<tr><td>медиана раскрытой суммы</td><td>3,5 млрд ₽</td><td>4,0 млрд ₽</td><td><b>2,4 млрд ₽</b></td></tr>
<tr><td>средняя раскрытая сумма</td><td>23,7 млрд ₽</td><td>12,0 млрд ₽</td><td>18,6 млрд ₽</td></tr>
<tr><td>продаж с торгов</td><td>3</td><td>3</td><td><b>78</b></td></tr>
<tr><td>правкомиссия или указ</td><td>29</td><td>9</td><td>27</td></tr>
<tr><td>изъятие, иск Генпрокуратуры</td><td>10</td><td>12</td><td><b>37</b></td></tr>
<tr><td>уход иностранного владельца</td><td>13</td><td>2</td><td>9</td></tr>
<tr><td>«обсуждается» на конец периода</td><td>17</td><td>30</td><td>130</td></tr>
<tr><td>не состоялось</td><td>15</td><td>10</td><td>10</td></tr></table>
<p class="fine">Одна страница, десять строк, каждая против прошлого года — формат годового отчета ABA Deal Points. Мелким шрифтом: приток новостей работает в полную силу с лета 2026, торги считаем с 26 октября; сравнивать можно доли и структуру, не число сделок.</p>''',
  inter_title='Со сцены · «Угадай сумму»',
  inter='Три сделки года с раскрытой ценой. Зал голосует с телефона за диапазон, потом открываем карточку. Росатом и 51% группы «Дело» — 77 млрд ₽. Шереметьево и активы Домодедово — 66 млрд ₽. «Транснефть» и 7,52% Газпромбанка — 40 млрд ₽. Три минуты, и видно, насколько рынок промахивается в оценках.',
  mod_title='Модератору заранее · пять слайдов',
  mod='Рынок по нашему счету. Торги как новый формат. Государство и госбанки как покупатели. Кого называют источники среди консультантов 2025–2026: ALUMNI Partners 9, VERBA LEGAL 9, Nextons 8, White Square 6, Denuo 6, ККМП 5. Карта «кто готовится к сделкам» — 143 признака.',
  tiles=[('10×','медиана меньше среднего','2,4 против 18,6 млрд ₽'),('78','продаж с торгов в 2026','против трех годом ранее'),('86%','сделок без названного консультанта','рынок не называет юристов')]),
 dict(n='2',t='11:15',title='Внутри сделки: инхаус-юристы',who='Яндекс, Севергрупп, Билайн',
  hand_title='Спикерам заранее · «Ваши сделки глазами открытых источников»',
  hand='''<div class="dossier"><div><b>Яндекс</b><span>21 карточка с 2023 года</span><p>15 покупок, 3 продажи, 3 раза сам предмет сделки. Последние: СП с SolidSoft по кибербезопасности, переговоры о продаже Yango в Израиле, объединение корпоративных ИТ-направлений с VK.</p></div>
<div><b>Севергрупп</b><span>9 карточек</span><p>6 покупок («Кордиант» у S8 Capital), 3 продажи («Ароматный мир», «Рив Гош»).</p></div>
<div><b>Билайн</b><span>6 карточек</span><p>MBO 2023 года, покупка 95% CDNVideo, в 2026-м — два лота недвижимости на торгах.</p></div></div>
<p class="fine">Одна страница на компанию: что мы увидели, что нет, где источники расходятся. В руки модератору и спикерам с просьбой поправить — подарок и проверка базы одновременно.</p>''',
  inter_title='Раздатка · «От MoU до закрытия: что видно снаружи»',
  inter='Воронка статусов по годам и список долгостроев: 32 сделки «обсуждаются» с 2022–2024 годов без единого подтверждения — Philip Morris, «Мультимедиа Холдинг», МГКЛ. Инхаус-юристы знают, почему сделки виснут; мы показываем, как это выглядит для рынка.',
  mod_title='Интерактив · «Сколько живет сделка»',
  mod='Распределение «первая новость → закрытие» по месяцам, отдельно для сделок с правкомиссией и без. Показываем, только если успеем разметить даты и проверить выборку. Цифру без списка сделок за ней не выносим.',
  tiles=[('130','сделок «обсуждается» на конец октября 2026',''),('32','долгостроя с 2022–2024 годов','без единого подтверждения'),('10','сделок не состоялось в 2026','причины размечаем руками')]),
 dict(n='3',t='12:45',title='Продажа выделенного бизнеса',who='Модераторы — Рудяк, Никольская',
  hand_title='Раздатка · «Как в России продают непрофильное: 20 примеров 2022–2026»',
  hand='''<table class="list"><tr><th>кто продает</th><th>что выделил</th><th>кому · за сколько</th></tr>
<tr><td>ВТБ</td><td>агрохолдинг «Лабинский»</td><td>50 млрд ₽</td></tr>
<tr><td>ВТБ</td><td>пансионат «Камелия», отели Hyatt Regency и Holiday Inn</td><td>структурам частных инвесторов</td></tr>
<tr><td>Норникель</td><td>золотой проект Быстринско-Ширинское</td><td>покупатель не назван</td></tr>
<tr><td>UniCredit</td><td>часть российских активов банка</td><td>инвестору из ОАЭ</td></tr>
<tr><td>Henkel</td><td>российский бизнес</td><td>консорциуму инвесторов</td></tr>
<tr><td>РЖД</td><td>Moscow Towers, 49% ФГК, 25% плюс 1 акция «ПНК»</td><td>через торги</td></tr></table>
<p class="fine">Полная таблица — 22 карточки: кто продает → что выделил → кому → за сколько → как структурировано (продажа долей, торги, передача в управление).</p>''',
  inter_title='Кейс для модераторов · банк распродает непрофильное',
  inter='У ВТБ в базе 22 карточки, из них 13 — продажи: отели, агро, «Открытие». Самый длинный ряд выделений у одного продавца за три года. У Сбера 30 карточек: 19 покупок и 10 продаж. Пара на одном развороте, со ссылками на карточки.',
  mod_title='Интерактив · «Что раскрывают при выделении»',
  mod='Доля сделок, где названы цена, структура (поэтапный вход, рассрочка, опцион обратного выкупа) и согласования — из текстов карточек. Честно подписано: это «что рынок рассказывает», а не «что в договорах». Закрытые условия — зона исследования юрфирм, и мы говорим это вслух.',
  tiles=[('22','карточки выделения непрофильного',''),('13 из 22','карточек ВТБ — продажи',''),('10 из 30','карточек Сбера — продажи','')]),
 dict(n='4',t='15:00',title='Оценка компаний',who='Модератор — Гаджиев, Orion. Сбер, ВТБ',
  hand_title='Раздатка · «Цена сделки: раскрыто, посчитано, в открытых исследованиях»',
  hand='''<div class="layers"><div><i>1</i><b>Что раскрыто</b><p>Тепловая карта «отрасль × год» с долей сделок с названной суммой: где молчат (ИТ, здравоохранение), где не могут (торги, госимущество, IPO). У нас 56% раскрытых за 2025 без торгов, у Mergers.ru — 51%: порядок совпадает.</p></div>
<div><i>2</i><b>Что посчитано</b><p>Медианы по сделкам базы рядом с внешними ориентирами: цены реальных сделок Б1 и Advance Capital за 2024 год — агро 5,2 EBITDA, ритейл 5,0, логистика 5,4, ТМТ 6,1, тяжелая промышленность 3,8; биржа по АТОН и Kept; мировой ориентир Дамодарана как потолок. Источник у каждого числа.</p></div>
<div><i>3</i><b>Живая демонстрация</b><p>Карточка без раскрытой цены, кнопка «Посчитать»: отчетность ФНС покупаемой компании × медиана базы и × отраслевой мультипликатор, диапазон, похожие сделки, ссылка на источник у каждого метода.</p></div></div>''',
  inter_title='Модератору из Orion',
  inter='Со сцены будут говорить о дисконтах за ключевую ставку и уход иностранцев. У нас есть цифра из Б1: сделки выхода иностранцев шли по 2,3 EBITDA против 5,4 у внутренних, и 61 карточка таких выходов, по которым это можно проверить.',
  mod_title='Что нужно до сессии',
  mod='Три кейса для демонстрации «Посчитать» с подтвержденной отчетностью. Тепловая карта раскрытия по отраслям. Таблица мультипликаторов в трех колонках: база, сделки Б1, биржа.',
  tiles=[('56%','сделок 2025 с названной суммой','без торгов'),('5,2×','EBITDA — агро, сделки 2024','Б1 и Advance Capital'),('2,3×','EBITDA — выход иностранцев','против 5,4 у внутренних')]),
 dict(n='5',t='16:30',title='Трансграничные M&A',who='Модератор — Бутенко, Stonebridge',
  hand_title='Разворот · «Три пути иностранного актива»',
  hand='''<div class="paths"><div><b>Путь 1 · продажа</b><p>61 карточка ухода иностранного владельца: 13 в 2022, 24 в 2023, 13 в 2024, 2 в 2025, 9 в 2026. Правкомиссия и указы — 121 карточка, пик 2023 года, новый подъем в 2026-м.</p></div>
<div><b>Путь 2 · временное управление</b><p>19 карточек: Danone, Carlsberg, Ariston (передан Газпрому), Akzo Nobel, CanPack, Fortum. Хронология указов и что с активом дальше: продан, возвращен, заморожен.</p></div>
<div><b>Путь 3 · изъятие и торги</b><p>74 карточки по искам Генпрокуратуры, 37 из них в 2026 году. Дальше торги: ЮГК — 93 млрд ₽, Домодедово — 66 млрд ₽ на аукционе на понижение, Raven Russia — 47 млрд ₽, «Агропромкредит» — 1,43 млрд ₽, цена снижена вдвое от первой.</p></div></div>
<p class="fine">Хроника фактов со ссылками, без оценок.</p>''',
  inter_title='Интерактив · «Второй круг»',
  inter='Лента перепродаж активов, купленных у иностранцев: актив → первый покупатель 2022–2023 → второй покупатель 2025–2026 → через сколько месяцев. Desport/АРМ → «Сити Капитал», Frigoglass → «Фригохолд», Danone → Health & Nutrition → «Логика молока». Единственная в стране такая таблица.',
  mod_title='Модератору из Stonebridge',
  mod='Он ведет именно такие сделки — лента перепродаж и хронология временного управления будут интереснее всего ему. Нужна ручная разметка 70 карточек, три-четыре часа.',
  tiles=[('61','карточка ухода иностранцев','2022–2026'),('19','карточек временного управления',''),('37','изъятий в 2026 году','из 74 за четыре года')]),
]

def page_session(s, phone=False):
    tiles=''.join(tile(*t) for t in s['tiles'])
    return f'''<section class="page sess">
<header class="band"><div class="num">{s['n']}</div><div><div class="kicker">Сессия {s['n']} · {s['t']}</div><h2>{s['title']}</h2><p class="who">{s['who']}</p></div>{WORD('light')}</header>
<div class="cols"><div class="main"><h3>{s['hand_title']}</h3>{s['hand']}</div>
<aside><div class="card"><h4>{s['inter_title']}</h4><p>{s['inter']}</p></div><div class="card"><h4>{s['mod_title']}</h4><p>{s['mod']}</p></div></aside></div>
<div class="tiles">{tiles}</div>
</section>'''

def html(phone=False):
    cover=f'''<section class="page cover">{WORD('light big')}
<div class="ctext"><div class="kicker">M&amp;A Форум · 12 ноября 2026 · Москва</div><h1>Что Компас готовит<br>к каждой сессии</h1>
<p class="lead">Раздатки, интерактивы, досье спикерам. Все числа — из базы Компаса на 28 октября 2026: 1 531 сделка с 2022 года, за каждой цифрой — список карточек со ссылкой на источник.</p></div>
<div class="tiles light">{tile('1 531','сделка в базе','с 2022 года')}{tile('78','продаж с торгов в 2026','против трех годом ранее')}{tile('61','уход иностранного владельца','2022–2026')}{tile('86%','сделок без названного консультанта','')}</div>
<div class="foot"><span>projectcompass.ru</span><span>материалы к форуму · черновик для основателей</span></div></section>'''
    mech=f'''<section class="page mech"><div class="cols"><div class="main"><div class="kicker">Сквозная механика</div><h2>Они спросили — мы посчитали</h2>
<p>Все обзоры рынка — одного из двух видов: агрегаты без списка сделок или опросы. У нас каждая цифра раскладывается на список сделок со ссылкой на источник. Поэтому каждый материал форума заканчивается одним и тем же: QR на живую страницу сайта, где любой столбик открывается до карточки.</p>
<div class="rules"><div><b>Не меряемся числом сделок</b><p>с AK&amp;M и Kept: разный охват и пороги. Сравниваем доли и структуру.</p></div><div><b>Не даем оценок изъятиям</b><p>только хроника фактов со ссылками.</p></div><div><b>Не называем рейтингом</b><p>список консультантов — «кого называют источники».</p></div><div><b>Не показываем цифру</b><p>за которой нет списка сделок.</p></div></div></div>
<aside class="qrside">{QR}<p class="fine">Страница «Аналитика к форуму»: те же графики, кликабельные до карточек. Показать с телефона в кулуарах.</p></aside></div></section>'''
    sess=''.join(page_session(s,phone) for s in SESSIONS)
    card=f'''<section class="page extra"><div class="cols"><div class="main"><div class="kicker">Для всех, независимо от сессии</div><h2>Карточка форума</h2>
<div class="a5"><div class="a5front">{WORD()}<div class="kicker">2024 → 2025 → 2026</div><ul><li>медиана сделки <b>2,4 млрд ₽</b> против средней 18,6</li><li>торгов <b>78</b> против трех</li><li>изъятий <b>37</b> за десять месяцев</li><li>«обсуждается» <b>130</b> сделок</li></ul>{QR}</div>
<div class="a5back"><div class="kicker">Спросите Компас</div><p>«Какие сделки были у <em>компании спикера</em> с 2022 года?» — ассистент отвечает со ссылками, пока спикер говорит.</p>{QR}</div></div></div>
<aside><div class="card"><h4>Пять постов за неделю до форума</h4><p>Медиана против среднего. Торги. Три пути иностранного актива. Кого называют источники среди консультантов. Карта признаков будущих сделок. Последний пост — «увидимся 12 ноября».</p></div>
<div class="card"><h4>До печати, по порядку</h4><ol><li>Разметка типа покупателя — 3 часа</li><li>Даты «новость → закрытие» — 1 час и проверка</li><li>Цепочки перепродаж — 3–4 часа</li><li>Три кейса для «Посчитать» — 1 час</li><li>Досье трех спикеров — 1 час</li><li>Страница на сайте и пересчет цифр в день печати</li></ol></div></aside></div></section>'''
    body=cover+mech+sess+card
    pw='390px' if phone else '297mm'; ph='auto' if phone else '210mm'
    css=CSS_FONTS+'''
:root{--ivory:#F3F1E9;--paper:#F5F5F1;--ink:#15191D;--mut:#66707A;--line:#E2E5DF;--deep:#0F2B21;--acc:#1D5A44;--bronze:#A3814E;--bl:#C9AE7C}
*{box-sizing:border-box}html,body{margin:0;padding:0}body{font-family:'Man',sans-serif;color:var(--ink);background:#fff;font-size:12.5px;line-height:1.5}
h1,h2,h3,.tile b,.num,.wordmark{font-family:'PTS',serif;font-weight:400}
.page{width:'''+pw+''';min-height:'''+ph+''';page-break-after:always;position:relative;overflow:hidden;padding:'''+('28px 18px' if phone else '34px 42px')+''';background:var(--paper)}
.page:last-child{page-break-after:auto}
.kicker{font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--bronze);font-weight:500}
.wordmark{display:inline-flex;align-items:center;gap:8px;font-size:20px;color:var(--ink)}.wordmark em{font-style:normal;color:var(--bronze)}.wordmark.light{color:var(--ivory)}.wordmark.big{font-size:26px}
.cover{background:var(--deep);color:var(--ivory);display:flex;flex-direction:column}.cover .ctext{margin-top:auto}.cover .tiles{margin-top:28px}.cover .foot{margin-top:auto;padding-top:24px;display:flex;justify-content:space-between;color:#C9D9D0;font-size:11px;letter-spacing:.08em;text-transform:uppercase}
.cover h1{font-size:'''+('36px' if phone else '56px')+''';line-height:1.05;margin:14px 0 18px}.cover .lead{max-width:640px;font-size:'''+('14px' if phone else '16px')+''';color:#C9D9D0}
.cover .kicker{color:var(--bl)}
.tiles{display:grid;grid-template-columns:repeat('''+('2' if phone else 'auto-fit')+''',minmax(0,1fr));gap:10px;margin-top:22px}
.tile{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px}.tile b{display:block;font-size:'''+('26px' if phone else '32px')+''';line-height:1;color:var(--deep)}.tile span{display:block;margin-top:6px;font-size:12px;color:var(--ink)}.tile small{display:block;color:var(--mut);font-size:11px;margin-top:2px}
'''+('.tiles .tile:last-child:nth-child(odd){grid-column:1/-1}' if phone else '')+'''
.tiles.light .tile{background:rgba(255,255,255,.07);border-color:rgba(255,255,255,.18)}.tiles.light .tile b{color:var(--bl)}.tiles.light .tile span{color:var(--ivory)}.tiles.light .tile small{color:#C9D9D0}
.band{display:grid;grid-template-columns:auto 1fr auto;gap:18px;align-items:center;background:var(--deep);color:var(--ivory);margin:'''+('-28px -18px 18px' if phone else '-34px -42px 22px')+''';padding:'''+('18px' if phone else '22px 42px')+'''}
.band .num{font-size:'''+('44px' if phone else '64px')+''';color:var(--bl);line-height:1}.band h2{margin:4px 0 2px;font-size:'''+('22px' if phone else '30px')+'''}.band .who{margin:0;color:#C9D9D0;font-size:12px}.band .kicker{color:var(--bl)}
.band .wordmark{'''+('display:none' if phone else '')+'''}
.sess,.mech,.extra{display:flex;flex-direction:column}.sess .cols,.mech .cols,.extra .cols{flex:1}.sess .tiles{margin-top:auto;padding-top:18px}
.main{display:flex;flex-direction:column}.main>.paths,.main>.layers,.main>.dossier{flex:1}.paths,.layers{display:flex;flex-direction:column}.paths div,.layers div{flex:1;align-content:start}.paths div p,.layers div p{align-self:start}.dossier{align-content:stretch}
aside{display:flex;flex-direction:column}aside .card{flex:1;margin-bottom:12px}aside .card:last-child{margin-bottom:0}
.cols{display:grid;grid-template-columns:'''+('1fr' if phone else '1.55fr 1fr')+''';gap:'''+('16px' if phone else '28px')+'''}
.main h3{font-size:'''+('17px' if phone else '20px')+''';margin:0 0 10px;color:var(--deep)}
table{width:100%;border-collapse:collapse;font-size:'''+('11px' if phone else '12px')+''';background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line-soft,#ECEEE8)}th{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--mut);font-weight:500;background:var(--ivory)}td:not(:first-child),th:not(:first-child){text-align:right;font-variant-numeric:tabular-nums}table.list td:not(:first-child),table.list th:not(:first-child){text-align:left}tr:last-child td{border-bottom:0}td b{color:var(--acc)}table:not(.list) td:not(:first-child){white-space:nowrap}

.fine{font-size:11px;color:var(--mut);margin:10px 0 0}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:12px}.card h4{margin:0 0 6px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--acc);font-weight:600}.card p{margin:0}.card ol{margin:0;padding-left:18px}.card li{margin:2px 0}
.dossier{display:grid;grid-template-columns:repeat('''+('1' if phone else '3')+''',1fr);gap:10px}.dossier div{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px}.dossier b{font-family:'PTS',serif;font-size:18px;display:block}.dossier span{display:block;color:var(--bronze);font-size:11px;margin:2px 0 6px}.dossier p{margin:0;font-size:12px}
.layers div,.paths div{display:grid;grid-template-columns:auto 1fr;gap:0 12px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-bottom:8px}.layers i{font-style:normal;font-family:'PTS',serif;font-size:26px;color:var(--bl);grid-row:span 2}.layers b,.paths b{font-size:13px;color:var(--deep)}.layers p,.paths p{margin:2px 0 0;font-size:12px;grid-column:2}.paths div{grid-template-columns:1fr}.paths p{grid-column:1}
.mech h2,.extra h2{font-size:'''+('26px' if phone else '36px')+''';margin:6px 0 12px;color:var(--deep)}.mech .main>p{font-size:'''+('14px' if phone else '15px')+''';max-width:620px}
.rules{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:18px}.rules div{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px}.rules b{color:var(--deep)}.rules p{margin:2px 0 0;color:var(--mut);font-size:12px}
.qrside{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.qr{display:inline-flex;flex-direction:column;align-items:center;gap:8px}.qrgrid{display:grid;grid-template-columns:repeat(9,1fr);width:92px;height:92px;border:6px solid #fff;background:#fff;outline:1px solid var(--line)}.qrgrid i{display:block}.qrgrid i.on{background:var(--deep)}.qr span{font-size:11px;color:var(--mut)}
.a5{display:grid;grid-template-columns:'''+('1fr' if phone else '1fr 1fr')+''';gap:14px;margin-top:12px}.a5front,.a5back{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px;min-height:'''+('auto' if phone else '300px')+''';display:flex;flex-direction:column;gap:10px}.a5back{background:var(--deep);color:var(--ivory)}.a5back .kicker{color:var(--bl)}.a5back .qr span{color:#C9D9D0}.a5 ul{margin:0;padding-left:16px;font-size:13px}.a5 li{margin:3px 0}.a5 b{color:var(--acc)}.a5back em{color:var(--bl);font-style:normal}
'''
    return '<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>'+css+'</style></head><body>'+body+'</body></html>'

async def render():
    async with async_playwright() as p:
        br=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        for phone in (False,True):
            name='forum_phone' if phone else 'forum_desktop'
            open(os.path.join(OUT,name+'.html'),'w').write(html(phone))
            pg=await br.new_page(viewport={'width':390 if phone else 1123,'height':900})
            await pg.goto('file://'+os.path.join(OUT,name+'.html')); await pg.wait_for_timeout(600)
            if phone:
                h=await pg.evaluate('document.body.scrollHeight')
                await pg.pdf(path=os.path.join(OUT,name+'.pdf'),width='390px',height=str(h+2)+'px',print_background=True,page_ranges='1')
                await pg.screenshot(path=os.path.join(OUT,name+'.png'),full_page=True)
            else:
                await pg.pdf(path=os.path.join(OUT,name+'.pdf'),width='297mm',height='210mm',print_background=True)
                for i in range(await pg.evaluate("document.querySelectorAll('.page').length")):
                    el=(await pg.query_selector_all('.page'))[i]; await el.screenshot(path=os.path.join(OUT,'desk_%d.png'%(i+1)))
            # переполнения страниц
            over=await pg.evaluate("[...document.querySelectorAll('.page')].map((p,i)=>[i+1,p.scrollHeight,p.clientHeight,p.scrollWidth,p.clientWidth]).filter(x=>x[1]>x[2]+1||x[3]>x[4]+1)")
            print(name,'overflow:',over)
            await pg.close()
        await br.close()
asyncio.run(render())
