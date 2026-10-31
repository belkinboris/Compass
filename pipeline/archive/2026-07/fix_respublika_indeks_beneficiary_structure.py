# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `g677f3309`
(«Сеть книжных магазинов «Республика» сменила владельцев», август 2026)
уже называла покупателя (ООО «Индекс») и продавцов текстом, но не
называла ни доли продавцов, ни конечных бенефициаров покупателя, ни
профиль деятельности концерна, ни мнение аналитиков о мотивах и рисках
сделки (`eco.rationale` был пуст).

Личный WebFetch подтвердил дословно:
- Vedomosti.ru
  (https://www.vedomosti.ru/media/articles/2026/08/06/1219137-knizhnaya-set-respublika-smenila-vladeltsev):
  «Ранее «Интел-руал» владели граждане Казахстана – Александра Лютикова
  (99%) и Айбек Баймахан (1%)»; «99,99% в нем принадлежало ООО
  «Лайфгрупп», единственным собственником которого является Михаил
  Полежаев, а оставшиеся 0,01% – гендиректору АО Денису Васендину».
- Kommersant.ru (https://www.kommersant.ru/doc/8863560): «Компания в том
  числе занимается банкротством и ликвидацией организаций».
- New-retail.ru
  (https://new-retail.ru/novosti/retail/set_knizhnykh_respublika_prodana_na_fone_padeniya_vyruchki/):
  «Новым владельцем актива стала непрофильная компания — у консалтинговой
  группы нет ни закупочной экспертизы в книжной рознице, ни отстроенной
  логистики» (Егор Афанасьев, АБ «Пропозитум»); «докапитализация,
  реструктуризация долга либо подача заявления о банкротстве» (Роман
  Прудентов, Stonebridge Legal, — три сценария дальнейшего развития).

Сумма сделки ни в одном из проверенных источников (Коммерсантъ,
Ведомости, New Retail) не названа даже оценочно — честная пустота,
не заполняется. Новых событий за месяц (закрытие точек, ребрендинг,
кадровые перестановки) не найдено.

Запуск:
    python3 pipeline/fix_respublika_indeks_beneficiary_structure.py            # сухой прогон
    python3 pipeline/fix_respublika_indeks_beneficiary_structure.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Ранее ООО «Интел-руал» принадлежало гражданам Казахстана Александре '
    'Лютиковой (99%) и Айбеку Баймахану (1%). Покупатель, ООО «Индекс», '
    'принадлежит АО «Концерн производительных сил», в котором 99,99% '
    'контролирует Михаил Полежаев через ООО «Лайфгрупп», а 0,01% — '
    'гендиректор концерна Денис Васендин.'
)

OLD_ECO_CONTEXT = '«Индекс» входит в структуру АО «Концерн производительных сил».'

NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' Концерн в том числе занимается банкротством и ликвидацией '
    'организаций — книжная розница не входит в его профиль.'
)

OLD_ECO_RATIONALE = '—'
NEW_ECO_RATIONALE = (
    'Аналитики указывают, что новый владелец — непрофильная компания без '
    'опыта в книжной рознице: «у консалтинговой группы нет ни закупочной '
    'экспертизы в книжной рознице, ни отстроенной логистики» (Егор '
    'Афанасьев, АБ «Пропозитум»). Юрист Роман Прудентов (Stonebridge '
    'Legal) допускает три сценария развития — докапитализацию, '
    'реструктуризацию долга либо подачу заявления о банкротстве.'
)

NEW_SRC = ['New-retail.ru', 'https://new-retail.ru/novosti/retail/set_knizhnykh_respublika_prodana_na_fone_padeniya_vyruchki/']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g677f3309']

    assert d['law'].get('struct') == OLD_LAW_STRUCT, 'law.struct уже занят: %r' % (d['law'].get('struct'),)
    assert d['eco'].get('context') == OLD_ECO_CONTEXT, 'eco.context изменился: %r' % (d['eco'].get('context'),)
    assert d['eco'].get('rationale') == OLD_ECO_RATIONALE, 'eco.rationale уже занят: %r' % (d['eco'].get('rationale'),)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('g677f3309: law.struct заполнен (доли продавцов, бенефициары '
          'покупателя); eco.context дополнен (профиль концерна — '
          'банкротство/ликвидация); eco.rationale заполнен (мнение '
          'аналитиков о мотивах и рисках); добавлен источник')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['law']['struct'] = NEW_LAW_STRUCT
    d['eco']['context'] = NEW_ECO_CONTEXT
    d['eco']['rationale'] = NEW_ECO_RATIONALE
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
