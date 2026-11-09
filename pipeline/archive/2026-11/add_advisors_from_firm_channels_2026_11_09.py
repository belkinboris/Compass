"""9 ноября 2026, владелец: «Как мы эту сделку упустили?» (t.me/kkmpconnect/700).
Сверка архивов Telegram-каналов юрфирм (ККМП, ALUMNI, LEVEL, BIRCH, White Square,
ЛКП) с базой: у сделок ниже фирма сама пишет, что консультировала, а в карточке
консультант не указан («не раскрывались»). Дописывает фирму в law.adv со ссылкой
на пост; заглушку «Не раскрывались» снимает. Без --write — сухой прогон."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
ADD = {
    'ge32bd008': ('Юридический консультант покупателя («Интеррос»)', 'ККМП', 'Покупка у Societe Generale Росбанка и страховых компаний «Сосьете Женераль Страхование». Источник: https://t.me/kkmpconnect/105'),
    'c9a31a355': ('Юридический консультант «Норникеля»', 'ККМП', 'Перевод холдинговой компании Быстринского ГОКа в российскую юрисдикцию (АО «ХК Быстра»). Источник: https://t.me/kkmpconnect/1350'),
    'g5ccd2edb': ('Юридический консультант продавцов (Алексей и Ирина Макаровы)', 'LEVEL Legal Services', 'Продажа 100% долей ООО «УК Атол». Источник: https://t.me/LevelLegalServices/555'),
    'gf23149cf': ('Юридический консультант покупателя (VK)', 'ALUMNI Partners', 'Приобретение у структур Альфа-банка 100% акций ЗАО «Зингер». Источник: https://t.me/alumnipartnerslawfirm/694'),
    'g668c46db': ('Юридический консультант покупателя (ВымпелКом)', 'ALUMNI Partners', 'Приобретение 51% ООО «Колибри» (Callibri). Источник: https://t.me/alumnipartnerslawfirm/893'),
    'g3d34ac8e': ('Юридический консультант продавца (Raven Russia)', 'ALUMNI Partners', 'Продажа БЦ «Примиум» ЗПИФ «РД 2». Источник: https://t.me/alumnipartnerslawfirm/1341'),
    'gdb854428': ('Юридический консультант продавца (ЗПИФ «Азимут-капитал»)', 'ALUMNI Partners', 'Продажа 100% ООО «СДМ ТК-2». Источник: https://t.me/alumnipartnerslawfirm/1559'),
    'g61b33118': ('Юридический консультант покупателя (АПК «Михайловский», «Черкизово»)', 'ALUMNI Partners', 'Приобретение 100% долей ООО «Руском». Источник: https://t.me/alumnipartnerslawfirm/1694'),
    'g0e7acc4d': ('Юридический консультант покупателя («Завод ТЕХНО», ТЕХНОНИКОЛЬ)', 'ALUMNI Partners', 'Приобретение 100% долей ООО «ТД ЛТМ». Источник: https://t.me/alumnipartnerslawfirm/2225'),
    'citibank': ('Консультант покупателя по регуляторным согласованиям («Ренессанс Капитал»)', 'ALUMNI Partners', 'Получение согласований Банка России и Президента РФ. Источник: https://t.me/alumnipartnerslawfirm/2444'),
}


def is_placeholder(a):
    return isinstance(a, list) and len(a) > 1 and str(a[1]).strip().lower() in ('не раскрывались', 'не раскрыты', '—', '')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    by = {d['id']: d for d in data['deals']}
    for cid, entry in ADD.items():
        d = by[cid]
        law = d.setdefault('law', {})
        adv = [a for a in (law.get('adv') or []) if not is_placeholder(a)]
        assert not any(entry[1].split()[0].lower() in json.dumps(a, ensure_ascii=False).lower() for a in adv), (cid, 'фирма уже есть')
        law['adv'] = adv + [list(entry)]
        print('  %s: + %s — %s' % (cid, entry[1], d['title'][:60]))
    if write:
        fresh = json.load(open(DATA, encoding='utf-8'))
        assert len(fresh['deals']) == len(data['deals'])
        json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
