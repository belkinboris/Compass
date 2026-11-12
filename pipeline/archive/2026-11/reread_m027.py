# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, марафон, партия m027: правки, которые review.py не берет.

ЧТО ЧИНИТ — по карточкам, в OPS (у каждой правки факта — цитата в fact_log).

ЗАПУСК: без ключа — сухой прогон; --write — запись (база перечитывается прямо перед записью,
assert на старое значение, повторный запуск — «уже применено»).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
MISSING = object()
BY = 'reread m027 2026-11-12'

CNEWS_K2 = 'https://www.cnews.ru/news/line/2025-01-16_gk_softline_priobretaet_kontroliruyushchuyu'
COMNEWS_K2 = 'https://www.comnews.ru/content/237202/2025-01-17/2025-w03/1008/softline-priobrel-k2-9b-group'
VED_KP = 'https://www.vedomosti.ru/realty/articles/2024/10/30/1071911-kievskaya-ploschad-vishla-kapitala-samolet'
FONT_ARTIS = 'https://www.fontanka.ru/2024/10/18/74229098/'
RETAIL_FAS = 'https://www.retail.ru/news/fas-soglasovala-seti-rigla-priobretenie-ryada-aptechnykh-setey-v-10-regionakh-20-fevralya-2025-261194/'
PHV_RIGLA = 'https://pharmvestnik.ru/content/news/Rigla-obedinilas-s-krupneishei-aptechnoi-setu-DFO.html'
DN = 'https://datanewton.ru/api/v2/history?ogrn=%s&startDate=2000-01-01&attributes=OWNERS'

OPS = [
 # ga857f692 (Softline / К2-9b Group): дата — день записи в ЕГРЮЛ (51% у нового участника, Яненко 100% → 49%),
 # а не 02.10.2024 — день заметки Softline о допэмиссии, которая про эту сделку не пишет (источник снят).
 {'op': 'set', 'id': 'ga857f692', 'field': 'date', 'old': '2024-10-02', 'new': '2025-01-15',
  'q': ('ЕГРЮЛ, ООО «К2-9Б ГРУПП» (ИНН 3662288650), история участников: 2025-01-15 share_changed: Яненко Михаил '
        'Романович (100.0 → 49.0); 2025-01-15 joined: Загоруйко Валерия Витальевна (None → 51.0). CNews 16.01.2025: '
        'ГК Softline ... объявляет о приобретении контролирующей доли в группе компаний К2-9b Group', CNEWS_K2)},
 {'op': 'set', 'id': 'ga857f692', 'field': 'src',
  'old': [['Softline.ru', 'https://softline.ru/about/news/pao-softlayn-obyavlyaet-o-zavershenii-razmeshcheniya-dopolnitelnogo-vypuska-aktsiy-initsiirovannogo-s-celyu-finansirovaniya-m-a-strategii-gruppy'],
          ['ComNews', COMNEWS_K2], ['CNews', CNEWS_K2],
          ['CNews Safe', 'https://safe.cnews.ru/news/line/2025-03-19_inferit_oblako_gk_softline']],
  'new': [['CNews', CNEWS_K2], ['ComNews', COMNEWS_K2],
          ['CNews Safe', 'https://safe.cnews.ru/news/line/2025-03-19_inferit_oblako_gk_softline']]},
 {'op': 'replace', 'id': 'ga857f692', 'field': 'eco.context',
  'old': 'тестированию защищенности веб-ресурсов от DDoS-атак.',
  'new': 'тестированию защищенности веб-ресурсов от DDoS-атак.\n\nПо ЕГРЮЛ, 15 января 2025 года 51% долей '
         'ООО «К2-9б Групп» перешли к Валерии Загоруйко, у основателя Михаила Яненко осталось 49%; '
         'связь нового участника с «Софтлайном» открытые источники не раскрывают.'},
 {'op': 'company', 'cid': 'g7b600ccf', 'field': 'desc',
  'old': 'Компания в сфере системной интеграции и кибербезопасности; в 2024 году 51% с опцией на полную консолидацию к 2027–2028 годам купил Софтлайн за 400 млн ₽ (первый этап).',
  'new': 'Воронежский системный интегратор в сфере информационной безопасности; в январе 2025 года 51% купил Softline, у которого есть право довести долю до 100% в 2027–2028 годах.'},
 {'op': 'set', 'id': 'ga857f692', 'field': 'date_basis', 'old': MISSING, 'new': 'registry'},
 # g4a751f95 («Севергрупп» / «Кордиант»): заметка «Движка» о перезапуске завода Gislaved в 2025 году — не про эту
 # сделку (фраза о ней снята из контекста вместе с покупкой «А.Раймонд РУС» — другой сделкой).
 {'op': 'set', 'id': 'g4a751f95', 'field': 'src',
  'old': [['Коммерсантъ', 'https://www.kommersant.ru/doc/7198627'], ['Коммерсантъ', 'https://www.kommersant.ru/doc/7327316'],
          ['Восход', 'https://www.voskhod.legal/team'],
          ['Движок', 'https://dvizhok.su/business/zavod-gislaved-v-ulyanovske-perezapusk-proizvodstva-i-planyi-na-2025-god'],
          ['Коммерсантъ', 'https://www.kommersant.ru/doc/7233644'],
          ['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/10/02/1066066-severgrupp-kupila-kordiant'],
          ['Коммерсантъ', 'https://www.kommersant.ru/doc/7198179']],
  'new': [['Коммерсантъ', 'https://www.kommersant.ru/doc/7198627'],
          ['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/10/02/1066066-severgrupp-kupila-kordiant'],
          ['Коммерсантъ', 'https://www.kommersant.ru/doc/7198179'], ['Коммерсантъ', 'https://www.kommersant.ru/doc/7327316'],
          ['Восход', 'https://www.voskhod.legal/team'], ['Коммерсантъ', 'https://www.kommersant.ru/doc/7233644']]},
 # gc9bc132c («Киевская площадь» / «Самолет»): 25,6 млрд ₽ — биржевая стоимость 10% акций при ВХОДЕ в 2021 году,
 # а не цена выхода (Ведомости: подробности сделки не раскрыты). Дата 01.10.2024 ни в одном источнике не стоит:
 # Ведомости 30.10.2024 — «сделка произошла еще несколько месяцев назад» → дата годом. Профиль «Азалия
 # (Киевская площадь)» сопоставлен с ООО «СЗ «Азалия» — продавцом акций «Самолета» это юрлицо ни один
 # источник не называет; ссылка снимается, продавец — текстом. Ъ 8608660 и Business Gazeta — отчетность и
 # техдефолт «Самолета» 2025–2026 годов, о выходе «Киевской площади» не пишут — сняты.
 {'op': 'set', 'id': 'gc9bc132c', 'field': 'sum', 'old': '25,6 млрд ₽ (по оценке)', 'new': 'Не раскрыта',
  'q': ('По их словам, сделка произошла еще несколько месяцев назад. Ее подробности они не раскрыли. … На момент '
        'сделки 10% акций девелопера на Московской бирже стоили около 25,6 млрд руб.', VED_KP)},
 {'op': 'set', 'id': 'gc9bc132c', 'field': 'eco.sum', 'old': '25,6 млрд ₽ (по оценке)', 'new': 'Не раскрыта',
  'q': ('По их словам, сделка произошла еще несколько месяцев назад. Ее подробности они не раскрыли.', VED_KP)},
 {'op': 'retract', 'id': 'gc9bc132c', 'field': 'sum', 'new': ['25,6 млрд ₽ (по оценке)']},
 {'op': 'set', 'id': 'gc9bc132c', 'field': 'date', 'old': '2024-10-01', 'new': '2024',
  'q': ('30 октября 2024 … По их словам, сделка произошла еще несколько месяцев назад.', VED_KP)},
 {'op': 'set', 'id': 'gc9bc132c', 'field': 'seller_id', 'old': 'g11514f2e', 'new': MISSING,
  'q': ('ГК «Киевская площадь» и ее совладелец Год Нисанов вышли из состава акционеров группы «Самолет»', VED_KP)},
 {'op': 'set', 'id': 'gc9bc132c', 'field': 'seller', 'old': '«Киевская площадь»', 'new': 'ГК «Киевская площадь» и Год Нисанов',
  'q': ('ГК «Киевская площадь» и ее совладелец Год Нисанов вышли из состава акционеров группы «Самолет»', VED_KP)},
 {'op': 'note', 'id': 'gc9bc132c', 'path': 'no_profile.buyer',
  'new': 'Покупатель акций не раскрыт: Ведомости (30.10.2024) и РИА Недвижимость пишут только о выходе «Киевской площади» '
         'и Года Нисанова из акционеров; у ПАО реестр акционеров не открыт, пакет каждой структуры был меньше 5% и не '
         'раскрывался. Искали: Ведомости, РИА Недвижимость, Ъ и Business Gazeta о «Самолете», веб-поиск по «Азалии» и «Киевской площади».'},
 {'op': 'note', 'id': 'gc9bc132c', 'path': 'no_profile.seller',
  'new': 'Продавцы — структуры группы «Киевская площадь» и Год Нисанов (Ведомости); какие юрлица держали акции, '
         'источники не называют, у каждого было меньше 5%. Профиль «Азалия (Киевская площадь)» — ООО «СЗ «Азалия», '
         'его участие в этой сделке не подтверждено, ссылка снята.'},
 {'op': 'set', 'id': 'gc9bc132c', 'field': 'src',
  'old': [['Ведомости', VED_KP], ['РИА Недвижимость', 'https://realty.ria.ru/20241030/samolet-1980984296.html'],
          ['Коммерсантъ', 'https://www.kommersant.ru/doc/8608660'], ['Business Gazeta', 'https://m.business-gazeta.ru/news/701575']],
  'new': [['Ведомости', VED_KP], ['РИА Недвижимость', 'https://realty.ria.ru/20241030/samolet-1980984296.html']]},
 # g3b356148 («Продовольственная инициатива» / «Артис–Детское питание»): акции продавцов-банкротов проданы на торгах
 # (тип — «Продажа с торгов», правка review.py), заголовок — конструкцией торгов и с долей по Фонтанке (2 × 49,09%);
 # прежняя запись заголовка лежит в written_titles_g3_2026_11_01.py — ее отпечаток уходит в proofread_absorbed.
 # Сумма — «порядка 204 млн рублей» (204,4 — наш расчет из двух стартовых цен). Дата 01.10.2024 ни в одном
 # источнике не стоит: на 18.10.2024 «договоры купли-продажи уже заключены» → дата годом.
 {'op': 'set', 'id': 'g3b356148', 'field': 'title',
  'old': 'ООО «Продовольственная инициатива» купило 98,2% АО «Артис–Детское питание»',
  'new': 'ООО «Продовольственная инициатива» купило на торгах 98,18% АО «Артис–Детское питание»',
  'absorb': 'ООО «Продовольственная инициатива» купило 98,2% АО «Артис–Детское питание»',
  'q': ('Компания выкупила доли прежних владельцев Михаила Ляско и Евгения Чернышева, которые держали по 49,09 % бизнеса … '
        'По итогам торгов покупателем стала компания «Продовольственная инициатива»', FONT_ARTIS)},
 {'op': 'set', 'id': 'g3b356148', 'field': 'sum', 'old': '204,4 млн ₽', 'new': '≈204 млн ₽',
  'q': ('сумма сделки составила порядка 204 млн рублей', FONT_ARTIS)},
 {'op': 'set', 'id': 'g3b356148', 'field': 'eco.sum', 'old': '204,4 млн ₽', 'new': '≈204 млн ₽',
  'q': ('сумма сделки составила порядка 204 млн рублей', FONT_ARTIS)},
 {'op': 'set', 'id': 'g3b356148', 'field': 'date', 'old': '2024-10-01', 'new': '2024',
  'q': ('18 октября 2024 … По итогам торгов покупателем стала компания «Продовольственная инициатива», договоры купли-продажи уже заключены', FONT_ARTIS)},
 {'op': 'company', 'cid': 'g168b6da5', 'field': 'desc',
  'old': 'Компания основателя Антона Капралова; в 2024 году купила на банкротных торгах 98,2% «Артис–Детское питание» за 204,4 млн ₽, а сама затем перешла к Андрею Алексееву.',
  'new': 'Петербургская оптовая компания Андрея Алексеева, бывшего директора по персоналу «Артис–Детское питание»; в 2024 году купила на банкротных торгах 98,18% его акций примерно за 204 млн ₽.'},
 {'op': 'company', 'cid': 'g2678d3df', 'field': 'desc',
  'old': 'Реализовано на банкротных торгах по иску «Банка Санкт-Петербург»; в 2024 году 98,2% акций купила «Продовольственная инициатива» за 204,4 млн ₽.',
  'new': 'Петербургская компания школьного и больничного питания, работает с 1995 года; в 2024 году 98,18% акций купила на банкротных торгах «Продовольственная инициатива».'},
 {'op': 'company', 'cid': 'g7b600ccf', 'field': 'legal_short', 'old': MISSING, 'new': 'ООО «К2-9Б Групп»'},
 # gfa47c307 («Ригла» / «Аптека Миницен» и «Новая аптека»): 01.10.2024 — ни в одном источнике. 6 декабря 2024 года
 # договор подписан и направлен на регистрацию (Фармвестник со слов «Риглы»), а ФАС согласовала покупку компаний сети с
 # предписаниями только 20.02.2025 (Retail.ru) — переход прав не раньше этого; Vademecum со слов источников называл
 # 06.12.2024 днем закрытия — версия записана в «Как устроена сделка». Дата — годом закрытия. Консультант Unicorn —
 # из Фармвестника. Предписания ФАС перенесены из «Условий» в «Согласования».
 {'op': 'set', 'id': 'gfa47c307', 'field': 'date', 'old': '2024-10-01', 'new': '2025',
  'q': ('ФАС России согласовала ходатайства о приобретении организацией 16 хозяйствующих субъектов (ООО «Аверс Аптека '
        'Миницен», … ООО «Суперфарма» …) (20 февраля 2025) … АС «Ригла» 6 декабря подписала договор … На текущий момент '
        'договор направлен на государственную регистрацию', RETAIL_FAS)},
 {'op': 'set', 'id': 'gfa47c307', 'field': 'eco.finadv', 'old': 'Публично не сообщалось',
  'new': 'Unicorn — финансовый консультант одной из сторон',
  'q': ('Консультантом сделки выступила компания Unicorn.', PHV_RIGLA)},
 {'op': 'set', 'id': 'gfa47c307', 'field': 'law.terms',
  'old': 'ФАС следит, чтобы ее предписания выполнялись. Если этого не произойдет, ведомство может пойти в суд и добиваться признания сделок недействительными.',
  'new': '—'},
 {'op': 'set', 'id': 'gfa47c307', 'field': 'src',
  'old': [['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/10/02/1066160-rigla-pokupaet-setei'],
          ['Vademecum', 'https://vademec.ru/news/2024/12/06/rigla-zavershila-sdelku-po-pokupke-dalnevostochnoy-apteki-minitsen/'],
          ['Konkurent.ru', 'https://konkurent.ru/article/73339'],
          ['Vademecum', 'https://vademec.ru/news/2026/06/08/roznichnyy-segment-gk-protek-pereimenovan-v-rigla-zdravsiti/']],
  'new': [['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/10/02/1066160-rigla-pokupaet-setei'],
          ['Фармвестник', PHV_RIGLA],
          ['Vademecum', 'https://vademec.ru/news/2024/12/06/rigla-zavershila-sdelku-po-pokupke-dalnevostochnoy-apteki-minitsen/'],
          ['Retail.ru', RETAIL_FAS],
          ['Konkurent.ru', 'https://konkurent.ru/article/73339'],
          ['Vademecum', 'https://vademec.ru/news/2026/06/08/roznichnyy-segment-gk-protek-pereimenovan-v-rigla-zdravsiti/']]},
 # g514c4225 (3 STREAMS / VMMGame): механика по ЕГРЮЛ ООО «Куб» в день карточки — в «Как устроена сделка»; описания
 # профилей — без неподтвержденного (Shinsale, «Кривенко и партнеры», «увеличив долю с 6% до 18%» как вложение фонда).
 {'op': 'set', 'id': 'g514c4225', 'field': 'law.struct', 'old': '—',
  'new': 'По ЕГРЮЛ, 27 сентября 2024 года доля АО «ТИЛТЕХ» в ООО «Куб» выросла с 6% до 18%, а доля Виктора Удавихина '
         'снизилась с 31,33% до 19,33%. Какую долю получил фонд за 45 млн ₽, стороны не раскрывали.'},
 {'op': 'company', 'cid': 'gfaa7f73a', 'field': 'desc',
  'old': 'Инвестиционный фонд группы «Тилтех» (совладельцы — Андрей Кривенко и партнеры), вкладывается в потребительские бренды — мебель VMMGame, Shinsale.',
  'new': 'Инвестиционный фонд группы «ТилТех» (партнеры группы — «Агама», «Химрар» и «ВкусВилл»), основан в 2023 году; вкладывается в потребительские бренды, в том числе VMMGame.'},
 {'op': 'company', 'cid': 'g9ea22c56', 'field': 'desc',
  'old': 'Производитель мебели; в 2024 году фонд 3 STREAMS (владельцы — Андрей Кривенко и партнеры) вложил в него 45 млн ₽, увеличив долю с 6% до 18%.',
  'new': 'Производитель игровых кресел и столов для геймеров (ООО «Куб», Дедовск); в 2024 году фонд 3 STREAMS вложил в компанию 45 млн ₽.'},
 {'op': 'company', 'cid': 'g9ea22c56', 'field': 'legal_short', 'old': MISSING, 'new': 'ООО «Куб»'},
 # g81a766ac («Русагро» / «Агро-Белогорье», 25% по суду): сумма — голым числом (review.py «тыс.» не разбирает);
 # источники о консолидации 100% (своя карточка g97d9fa60), доверительном управлении 2025, аресте Мошковича
 # и отчетности 2025 года — не про эту сделку, сняты вместе с этими фразами контекста и «Согласований».
 {'op': 'set', 'id': 'g81a766ac', 'field': 'sum', 'old': '2,5 тыс. ₽ (номинальная цена по решению суда)', 'new': '2,5 тыс. ₽',
  'q': ('В апреле 2024 года арбитражный суд Белгородской области постановил перевести 25% доли Владимира Зотова в '
        '«Агро-Белогорье» в адрес «Русагро» за 2,5 тыс. руб.', 'https://www.kommersant.ru/doc/7196506')},
 {'op': 'set', 'id': 'g81a766ac', 'field': 'eco.sum', 'old': '2,5 тыс. ₽ (номинальная цена по решению суда)', 'new': '2,5 тыс. ₽',
  'q': ('постановил перевести 25% доли Владимира Зотова в «Агро-Белогорье» в адрес «Русагро» за 2,5 тыс. руб.',
        'https://www.kommersant.ru/doc/7196506')},
 {'op': 'set', 'id': 'g81a766ac', 'field': 'src',
  'old': [['Коммерсантъ', 'https://www.kommersant.ru/doc/7196506'], ['Интерфакс', 'https://www.interfax.ru/business/991408'],
          ['AgroInvestor', 'https://www.agroinvestor.ru/transaction/news/43314-rusagro-poluchila-100-kontrol-nad-agro-belogorem/'],
          ['Интерфакс', 'https://www.interfax.ru/russia/1028523'], ['Право.ру', 'https://pravo.ru/news/258960/'],
          ['AgroInvestor', 'https://www.agroinvestor.ru/companies/news/46043/'],
          ['Meatinfo.ru', 'https://meatinfo.ru/news/chistaya-pribil-mpz-agro-belogore-v-496326']],
  'new': [['Коммерсантъ', 'https://www.kommersant.ru/doc/7196506'], ['Интерфакс', 'https://www.interfax.ru/business/991408']]},
 # gd58fa76a (АФК «Система» / «Транс Капитал»): год ошибочен — ЕГРЮЛ 26 сентября 2023 года (Интерфакс 27.09.2023, RB.ru 28.09.2023).
 {'op': 'set', 'id': 'gd58fa76a', 'field': 'date', 'old': '2024-09-26', 'new': '2023-09-26',
  'q': ('20:18, 27 сентября 2023 … Согласно ЕГРЮЛ, структура ПАО АФК "Система" - ООО "Система Телеком Активы" - с 26 сентября не '
        'является владельцем 90% ООО УК "Система Смарттех". Новым владельцем указанной доли стало АО "Транс Капитал".',
        'https://www.interfax.ru/business/923027')},
 {'op': 'set', 'id': 'gd58fa76a', 'field': 'date_basis', 'old': MISSING, 'new': 'registry'},
 {'op': 'company', 'cid': 'gc49f4801', 'field': 'desc',
  'old': 'В 2024 году купило 90% венчурного фонда Sistema SmartTech у структуры АФК «Система», не будучи аффилировано с корпорацией.',
  'new': 'Инвестиционная компания, создана в 2022 году; принадлежит ЗПИФ «Современные инновации». В 2023 году купила 90% УК «Система Смарттех» у структуры АФК «Система».'},
 # g8b2e2afd (Вознесенский / «Карат»): год ошибочен — ЕГРЮЛ 21.09.2023 (Ведомости 03.10.2023). Продавец в реестре —
 # «Гледен капитал» (входит в Gleden Invest Александра Клячина), а не сам Клячин: в схеме — юрлицо, Клячин — в прозе.
 {'op': 'set', 'id': 'g8b2e2afd', 'field': 'date', 'old': '2024-09-21', 'new': '2023-09-21',
  'q': ('По данным ЕГРЮЛ, 21 сентября 2023 г. 99,9% в ООО «Карат инвестиции», которому принадлежит АО «Карат», перешли в '
        'собственность предпринимателя Александра Вознесенского.', 'https://www.vedomosti.ru/business/articles/2023/10/03/998388-u-proizvoditelya-plavlenih-sirov-druzhba-i-yantar-smenilsya-sobstvennik')},
 {'op': 'set', 'id': 'g8b2e2afd', 'field': 'date_basis', 'old': MISSING, 'new': 'registry'},
 {'op': 'set', 'id': 'g8b2e2afd', 'field': 'seller_id', 'old': 'gb9c8945c', 'new': MISSING,
  'q': ('Ранее эта доля принадлежала фирме «Гледен капитал», которая входит в Gleden Invest Клячина.', 'https://www.vedomosti.ru/business/articles/2023/10/03/998388-u-proizvoditelya-plavlenih-sirov-druzhba-i-yantar-smenilsya-sobstvennik')},
 {'op': 'set', 'id': 'g8b2e2afd', 'field': 'seller', 'old': MISSING, 'new': '«Гледен капитал»',
  'q': ('Ранее эта доля принадлежала фирме «Гледен капитал», которая входит в Gleden Invest Клячина.', 'https://www.vedomosti.ru/business/articles/2023/10/03/998388-u-proizvoditelya-plavlenih-sirov-druzhba-i-yantar-smenilsya-sobstvennik')},
 {'op': 'note', 'id': 'g8b2e2afd', 'path': 'no_profile.seller',
  'new': 'Продавец по ЕГРЮЛ (Ведомости, 03.10.2023) — фирма «Гледен капитал» из Gleden Invest Александра Клячина; '
         'ИНН и правовую форму издание не называет, профиль не заводили.'},
 {'op': 'company', 'cid': 'gda4fa496', 'field': 'desc',
  'old': 'Петербургский бизнесмен; в 2024 году купил у Александра Клячина (Gleden Invest) завод «Карат».',
  'new': 'Предприниматель; в сентябре 2023 года получил 99,9% ООО «Карат инвестиции», владельца завода «Карат», от структуры Gleden Invest Александра Клячина.'},
 {'op': 'company', 'cid': 'gb9c8945c', 'field': 'desc',
  'old': 'Бизнесмен, владелец Gleden Invest; в 2024 году продал завод «Карат» Александру Вознесенскому, в 2025-м обсуждал выкуп у Росимущества бывших активов KR Properties.',
  'new': 'Бизнесмен, владелец Gleden Invest; в 2023 году его структура продала завод «Карат» Александру Вознесенскому, в 2025-м обсуждал выкуп у Росимущества бывших активов KR Properties.'},
 # Правовые формы сторон (ЕГРЮЛ через party_legal_names.py; сеть в репетиции сбрасывалась — ставим явно).
 {'op': 'company', 'cid': 'g7313d9af', 'field': 'legal_short', 'old': MISSING, 'new': 'ООО «Ригла»'},
 {'op': 'company', 'cid': 'gb52f53eb', 'field': 'legal_short', 'old': MISSING, 'new': 'АО «Кордиант»'},
 {'op': 'company', 'cid': 'g168b6da5', 'field': 'legal_short', 'old': MISSING, 'new': 'ООО «Продовольственная инициатива»'},
 {'op': 'company', 'cid': 'g2678d3df', 'field': 'legal_short', 'old': MISSING, 'new': 'АО «Артис–Детское питание»'},
 {'op': 'company', 'cid': 'g1581ce50', 'field': 'legal_short', 'old': MISSING, 'new': 'ООО «ГК «Агро-Белогорье»'},
 # g3af64b90 (Газпромбанк / ЭОС, не состоялась): 20.09.2024 — день статьи РБК о переговорах; карточка о срыве сделки,
 # отказ стал известен в мае 2025 года (Эксперт 06.05.2025 со ссылкой на РБК, день события не назван) → дата годом.
 # В «Согласованиях» стоял рассказ о срыве — согласования там нет (перенесено в «Дополнительно»).
 {'op': 'set', 'id': 'g3af64b90', 'field': 'date', 'old': '2024-09-20', 'new': '2025',
  'q': ('Новости 06 мая 2025 … Немецкая EOS Group, владеющая крупной коллекторской компанией в России, отказалась '
        'продавать «дочку» Газпромбанку. Иностранные акционеры ЭОС «вышли из сделки»', 'https://expert.ru/news/nemetskaya-kollektorskaya-kompaniya-otkazalas-ot-sdelki-s-gazprombankom/')},
 {'op': 'set', 'id': 'g3af64b90', 'field': 'law.appr',
  'old': 'Сделка не состоялась: немецкая EOS Group отказалась продавать российскую «дочку» Газпромбанку. Иностранные акционеры ЭОС вышли из сделки, а переговоры, начавшиеся осенью прошлого года, прекращены; компания подтвердила, что не ведет переговоров о продаже своего бизнеса в России.',
  'new': '—'},
 {'op': 'company', 'cid': 'gf286b3ae', 'field': 'desc',
  'old': 'Коллекторская компания, российское подразделение немецкой EOS Group; Сделка не состоялась: немецкая EOS Group отказалась продавать российскую «дочку» Газпромбанку.',
  'new': 'Коллекторское агентство, российская дочерняя компания немецкой EOS Group: покупает у банков проблемные долги и взыскивает их.'},
 {'op': 'company', 'cid': 'gf286b3ae', 'field': 'ind', 'old': 'Банки', 'new': 'Финансовые услуги'},
 # gf7dede20 (Russ / «Эфир Транзит»): покупка «Барсрекарта» в октябре 2025 года — другая сделка, снята из контекста;
 # «нынешнего года» — относительное время, заменено годом (БИЗНЕС Online: на 1 января 2024 года участники — Глеб
 # Григорьев и Луиза Сафарова, 13 сентября 100% у Андрея Кокорина).
 {'op': 'replace', 'id': 'gf7dede20', 'field': 'eco.context',
  'old': ' Russ продолжил консолидацию рынка: в конце октября группа, входящая в ООО РВБ, купила еще одного оператора рекламы в метро Казани — компанию «Барсрекарт» с лайтбоксами двух форматов, рекламный инвентарь которой Russ планирует интегрировать в свою сеть.',
  'new': ''},
 {'op': 'replace', 'id': 'gf7dede20', 'field': 'eco.context',
  'old': 'До сентября нынешнего года у казанского «Эфир Транзита» было 2 учредителя: Глеб Григорьев и Луиза Сафарова, по 50% у каждого.',
  'new': 'В начале 2024 года у казанского «Эфир Транзита» было два участника с долями по 50% — Глеб Григорьев и Луиза Сафарова; 13 сентября 2024 года все 100% перешли к Андрею Кокорину, директору московских АО «Медиа плюс груп» и ООО «МП Диджитал».'},
]


def _walk(obj, parts):
    for p in parts:
        obj = obj.get(p, MISSING) if isinstance(obj, dict) else MISSING
    return obj


def _set(obj, field, value):
    parts = field.split('.')
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    if value is MISSING:
        obj.pop(parts[-1], None)
    else:
        obj[parts[-1]] = value


def _apply(data, log):
    from fact_edit_guard import log as fact_log
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    for op in OPS:
        kind = op['op']
        if kind == 'registry':
            continue
        if kind == 'company':
            prof = comps[op['cid']]
            cur = prof.get(op['field'], MISSING)
            if cur == op['new']:
                log.append('уже применено: профиль %s %s' % (op['cid'], op['field']))
                continue
            assert cur == op['old'], (op['cid'], op['field'], cur)
            prof[op['field']] = op['new']
            log.append('профиль %s %s' % (op['cid'], op['field']))
            continue
        card = deals[op['id']]
        if kind == 'set':
            cur = _walk(card, op['field'].split('.'))
            if cur == op['new']:
                log.append('уже применено: %s %s' % (op['id'], op['field']))
                continue
            assert cur == op['old'], (op['id'], op['field'], cur)
            _set(card, op['field'], op['new'])
            if 'absorb' in op:
                from pipeline.ingest.review import fix_fingerprint
                lst = card.setdefault('proofread_absorbed', {}).setdefault(op['field'], [])
                if fix_fingerprint(op['absorb']) not in lst:
                    lst.append(fix_fingerprint(op['absorb']))
            if 'q' in op:
                fact_log(card, op['field'], None if op['new'] is MISSING else op['new'], op['q'][0], op['q'][1], BY)
            log.append('%s %s' % (op['id'], op['field']))
        elif kind == 'replace':
            cur = _walk(card, op['field'].split('.'))
            if (op['new'] and op['new'] in cur) or (not op['new'] and op['old'] not in cur):
                log.append('уже применено: %s %s (фраза)' % (op['id'], op['field']))
                continue
            assert cur.count(op['old']) == 1, (op['id'], op['field'])
            _set(card, op['field'], cur.replace(op['old'], op['new']))
            log.append('%s %s (фраза)' % (op['id'], op['field']))
        elif kind == 'retract':
            lst = card.setdefault('retracted', {}).setdefault(op['field'], [])
            for v in op['new']:
                if v not in lst:
                    lst.append(v)
            log.append('%s retracted.%s' % (op['id'], op['field']))
        elif kind == 'note':
            notes = card.setdefault('accepted_notes', {})
            cur = _walk(notes, op['path'].split('.'))
            if cur == op['new']:
                log.append('уже применено: %s accepted_notes.%s' % (op['id'], op['path']))
                continue
            assert cur is MISSING, (op['id'], op['path'], cur)
            _set(notes, op['path'], op['new'])
            log.append('%s accepted_notes.%s' % (op['id'], op['path']))
        else:
            raise AssertionError(kind)


def _registry(write, log):
    import fns_registry
    from fns_notes_to_registry import edit_registry_entry
    for op in OPS:
        if op['op'] != 'registry':
            continue
        cur = fns_registry.by_company_id().get(op['cid']) or {}  # noqa
        if cur.get('inn') == op['new']['inn']:
            log.append('уже применено: реестр %s' % op['cid'])
            continue
        assert cur.get('inn') == op['old_inn'], (op['cid'], cur)
        if write:
            assert edit_registry_entry(op['cid'], op['new'])
        log.append('реестр %s: ИНН %s → %s' % (op['cid'], op['old_inn'], op['new']['inn']))


def main(write=False):
    from pipeline import mass_edit_guard
    log = []
    data = json.load(open(DATA, encoding='utf-8'))
    _apply(data, log)
    _registry(False, log)
    print('\n'.join(log))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
    _apply(fresh, [])
    mass_edit_guard.check(json.load(open(DATA, encoding='utf-8')), fresh, os.environ.get('MASS_OK'))
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    _registry(True, [])
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
