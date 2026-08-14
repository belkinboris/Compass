# -*- coding: utf-8 -*-
"""Глубокая ревизия 2025 (партия 10), карточки 76–85 из «сотки».

Все 10 карточек — «обыскано под 12 углов, больше ничего не нашлось».

Находки:
  g3b67afa3 (М.Видео / Ужахов): +src Retail.ru.
  ge292671d (Мягкий знак): +src Retail.ru.
  gfe151394 (Чекми / Капитал Life): +src ASN-news.ru.
  cc16fce80 (ЮГК / приватизация): +src Эксперт.
  gf424fa11 (Wildberries / RVB): +src RB.ru.
  c2397cc97 (Инвитро / обратный выкуп): +src Vademecum.
  g59fbdbf8 (Nordgold / лицензии): +src Zolteh.ru.
  g941f2b2b (Корсаковский порт / ГК «Дело»): +src МорВести + Interfax.
  gd73fd825, g2e39c9a4: только deep_researched.
"""

FIXES = [
    # === g3b67afa3: М.Видео / Ужахов ===
    # Retail.ru подтверждает смену контролирующего акционера (Ужахов).
    dict(id='g3b67afa3', field='src', old=None,
         new=['Retail.ru',
              'https://www.retail.ru/news/generalnyy-direktor-m-video-bilan-uzhakhov-'
              'stal-osnovnym-aktsionerom-kompanii-24-iyulya-2024-243191/'],
         quote='генеральный директор «М.Видео» Билан Ужахов стал основным '
               'акционером компании',
         why='профильный ритейл-портал подтверждает имя и статус нового '
             'контролирующего акционера; скачан и сверен'),

    # === ge292671d: Мягкий знак / новый владелец ===
    # Retail.ru подтверждает смену собственника дистрибьютора туалетной бумаги.
    dict(id='ge292671d', field='src', old=None,
         new=['Retail.ru',
              'https://www.retail.ru/news/distributor-tualetnoy-bumagi-myagkiy-znak-'
              'smenil-vladeltsa-9-oktyabrya-2024-245987/'],
         quote='дистрибьютор туалетной бумаги «Мягкий знак» сменил владельца',
         why='независимый ритейл-источник, детали смены собственника; '
             'скачан и сверен'),

    # === gfe151394: Чекми / Капитал Life ===
    # ASN-news (отраслевое страховое издание) описывает сделку по продаже.
    dict(id='gfe151394', field='src', old=None,
         new=['ASN-news', 'https://www.asn-news.ru/news/86955'],
         quote='продала бизнес страховой компании «Капитал Life»',
         why='ASN-news — ведущий портал страховой отрасли России; '
             'подтверждает продажу Чекми страховщику; скачан и сверен'),

    # === cc16fce80: ЮГК / Росимущество ===
    # Expert.ru фиксирует итог аукциона (93,2 млрд руб.), что раскрывает сумму.
    dict(id='cc16fce80', field='src', old=None,
         new=['Эксперт',
              'https://expert.ru/news/rosimuschestvo-prodalo-yugk-za-932-mlrd-rubley'],
         quote='Росимущество продало ЮГК за 93,2 млрд рублей',
         why='Эксперт публикует итоговую цену аукциона, которая отсутствовала '
             'в Telegram-источнике; скачан и сверен'),

    # === gf424fa11: Wildberries / RVB ===
    # RB.ru подтверждает реструктуризацию: WB внёс 15 юрлиц в СП с Russ.
    dict(id='gf424fa11', field='src', old=None,
         new=['RB.ru', 'https://rb.ru/news/wildberries-15-rvb/'],
         quote='Wildberries внесла 15 юрлиц в структуру совместной с Russ компании',
         why='RB.ru раскрывает объём реструктуризации (15 юрлиц) — '
             'детализация, отсутствующая в AK&M; скачан и сверен'),

    # === c2397cc97: Инвитро / обратный выкуп ===
    # Vademecum подтверждает обратный выкуп: 2 млрд руб. на buyback и модернизацию.
    dict(id='c2397cc97', field='src', old=None,
         new=['Vademecum',
              'https://vademec.ru/news/2024/07/12/invitro-napravit-2-mlrd-rubley-na-'
              'obratnyy-vykup-i-modernizatsiyu-medofisov/'],
         quote='«Инвитро» направит 2 млрд рублей на обратный выкуп и модернизацию '
               'медофисов',
         why='Vademecum — ведущее медицинско-фармацевтическое издание; '
             'подтверждает сумму buyback и назначение средств; скачан и сверен'),

    # === g59fbdbf8: Nordgold / лицензии на полиметаллы ===
    # Zolteh.ru (отраслевое горнодобывающее издание) подтверждает структуру, связанную с Nordgold.
    dict(id='g59fbdbf8', field='src', old=None,
         new=['Zolteh.ru',
              'https://zolteh.ru/news/svyazannaya_s_nordgold_struktura_kupila_'
              'kompaniyu_s_litsenziyami_na_polimetally_/'],
         quote='Связанная с «Nordgold» структура купила компанию с лицензиями '
               'на полиметаллы',
         why='Zolteh — профильный портал золото-горнодобывающей отрасли; '
             'подтверждает покупателя и предмет сделки; скачан и сверен'),

    # === g941f2b2b: Корсаковский порт / ГК «Дело» ===
    # МорВести и Interfax подтверждают покупку порта Корсаков структурой Шишкарева.
    dict(id='g941f2b2b', field='src', old=None,
         new=['МорВести', 'https://morvesti.ru/news/1679/109542/'],
         quote='покупку Корсаковского торгового порта компанией Сергея Шишкарева',
         why='профильное морское издание с деталями сделки по Корсакову; '
             'скачано и сверено'),

    dict(id='g941f2b2b', field='src', old=None,
         new=['Interfax', 'https://www.interfax.ru/russia/970352'],
         quote='контрольного пакета порта Корсаков на Сахалине',
         why='Interfax подтверждает сделку и её статус через официальные каналы; '
             'скачан и сверен'),
]
