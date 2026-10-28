# -*- coding: utf-8 -*-
"""Консоль, 28 октября 2026: решения по сырью, чьи номера сменились.

Номер сырья считался через hash() и менялся в каждом процессе
(draft.draft_id_for). За день 10 нажатий владельца и партнера сослались на
номера, которых к моменту применения не было ни в одном hold-файле: восемь
«не сделка» (Тайвань, иеговисты — дважды, Volga, даркнет-форум, Бурунди,
Египет, Волгоград) и два «это сделка» — «Аккую» (владелец, 16:05) и
«Артмуза» (партнер, 16:53). Владелец часть из них нажимал повторно в 19:12
уже по новым номерам.

Что делает скрипт (сухой прогон без ключа, запись по --write):
1. Пишет в moderation_state.json память «номер -> заголовок» (`raw_sent_titles`)
   для старых номеров и для сырья, показанного сегодня, — approve.py с этого дня
   находит по ней новость с новым номером.
2. Для новостей, которых в hold уже нет, записывает решение сразу:
   «не сделка» — `decided_raw`/`raw_titles` = drop; «Артмуза» — take (карточка
   gf6a2225a уже заведена притоком); «Аккую» — enrich:g2f22b1dc (та же сделка,
   что карточка «Росатом рассматривает продажу до 49% в проекте АЭС «Аккую»»;
   карточка из первого нажатия владельца сегодня уже была слита в нее).
3. С ключом --consume подтверждает сайту эти 10 решений — ПОСЛЕ push.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote                                            # noqa: E402

STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')
HOLD = os.path.join(ROOT, 'data', 'inbox', 'hold', '2026-10-28.json')

# номер решения -> (ревизия git, где лежал черновик, вердикт)
ORPHANS = {
    'd48553697': ('d6980431', 'drop'), 'd81118251': ('db8e0296', 'drop'),
    'd14776047': ('db8e0296', 'drop'), 'd25306830': ('db8e0296', 'drop'),
    'd35569631': ('db8e0296', 'drop'), 'd14380614': ('db8e0296', 'drop'),
    'd24264752': ('289e9736', 'drop'), 'd69032150': ('289e9736', 'drop'),
    'd87088980': ('289e9736', 'enrich:g2f22b1dc'), 'd77815240': ('289e9736', 'take'),
}


def titles_from_git():
    out = {}
    for did, (rev, _verdict) in ORPHANS.items():
        txt = subprocess.run(['git', 'show', '%s:data/inbox/hold/2026-10-28.json' % rev],
                             capture_output=True, text=True, check=True, cwd=ROOT).stdout
        for d in json.loads(txt).get('drafts') or []:
            if str(d.get('draft_id')) == did:
                out[did] = str(d.get('title') or '')
    missing = set(ORPHANS) - set(out)
    assert not missing, 'не найдены в git: %s' % sorted(missing)
    return out


def main(write=False):
    state = json.load(open(STATE, encoding='utf-8'))
    titles = titles_from_git()
    hold = json.load(open(HOLD, encoding='utf-8')).get('drafts') or []
    present = {promote.raw_key(d.get('title')): str(d['draft_id']) for d in hold}
    sent_titles = state.setdefault('raw_sent_titles', {})
    for did, title in titles.items():
        sent_titles.setdefault(did, title)
    for d in hold:                                         # показанное сегодня — по новым номерам
        if str(d['draft_id']) in set(state.get('sent_raw') or []):
            sent_titles.setdefault(str(d['draft_id']), str(d.get('title') or ''))
    for did, (_rev, verdict) in ORPHANS.items():
        key = promote.raw_key(titles[did])
        if key in present and verdict in ('drop', 'take'):
            print('  %s «%s» — та же новость в hold как %s, применит approve.py' % (did, titles[did][:60], present[key]))
            continue
        print('  %s «%s» -> %s' % (did, titles[did][:60], verdict))
        state.setdefault('decided_raw', {})[did] = verdict if verdict in ('drop', 'take') else 'take'
        state.setdefault('raw_titles', {})[key] = verdict
        if verdict.startswith('enrich:'):
            for k, new_id in present.items():
                if promote.raw_same_news(titles[did], [k]) or 'аккую' in k:
                    state['decided_raw'][new_id] = 'take'
                    state['raw_titles'][k] = verdict
                    print('     + %s «%s» -> %s' % (new_id, k[:50], verdict))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
