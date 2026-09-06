# -*- coding: utf-8 -*-
"""Слить партию дублей карточек сделок по файлу спецификаций.

ЧТО ЧИНИТ. Внешний аудит перед бетой (раунд 2, 6 сентября 2026) нашёл второй
дубль после «Открытия» — «Первую образцовую типографию» — и потребовал
проверить дубли по остальной базе. Замер по структурным полям (общий предмет,
одна дата, одна сумма) дал 17 пар-кандидатов; каждую прочитали три
параллельных читателя, 13 пар оказались одной сделкой под двумя id, 4 — разными
сделками одного инвестора или двумя шагами одной консолидации. Решения и
переносимые значения лежат в `pipeline/merge_specs/<дата>.json` — по одной
записи на пару: `keep`, `drop`, `set` (поле → значение), `append_extra`,
`add_src`, `events`, `add_themes`, `ind` и причина.

ПОЧЕМУ ОТДЕЛЬНЫМ ОБЩИМ СКРИПТОМ, А НЕ ТРИНАДЦАТЬЮ ОДНОРАЗОВЫМИ. У слияния
одни и те же обязательные шаги, и один из них в прошлом уже забывали
(правки FIXES к удалённой карточке — см. CLAUDE.md, «Слияние дублей обязано
снять правки к удалённой карточке вместе с ней»); второй — перенос message_id
живого поста канала — впервые понадобился здесь (у двух дублей посты уже
ушли в канал). Скрипт делает всё это сам и в одном порядке:

  1. значение из `set` ложится только в ПУСТОЕ поле оставшейся карточки, и
     каждое его предложение обязано дословно (с точностью до кавычек и
     пробелов) лежать в тексте одной из двух карточек — сочинить его нельзя,
     как и перезаписать заполненное; перенос факта из «Дополнительной
     информации» оставшейся карточки в её же пустое поле — тоже перенос;
  2. `append_extra` дописывается в «Дополнительную информацию» по
     предложениям, и каждое предложение обязано лежать в тексте одной из двух
     карточек; уже стоящие в extra предложения не дублируются;
  3. источники объединяются по адресу (аддитивно, как `src` в review.py);
  4. события переносятся с проверкой вида и даты, а их текст — проверкой, что
     ни одно число и ни одно имя с заглавной не появилось из ниоткуда;
  5. `telegram_posts`: отметка дубля переезжает на оставшуюся карточку
     (message_id уже опубликованного поста — иначе публикация не узнает, что
     сделка в канале, и следующая правка поста его не найдёт);
  6. `merged[drop] = keep` — старый адрес открывает оставшуюся карточку;
     цепочки `merged[x] = drop` перенаправляются на keep;
  7. записи таблицы FIXES на удаляемый id снимаются из всех
     `pipeline/ingest/fixes/*.py` (по AST, с повторным разбором файла), — без
     этого `test_review_table_is_applied_and_not_pending` падает на первом же
     прогоне.

Сухой прогон печатает всё, что будет сделано, и все отказы проверок; при
любом отказе запись не выполняется вовсе (партия целиком или ничего).

Запуск:
    python3 pipeline/merge_duplicate_deals_batch.py --specs pipeline/merge_specs/2026-09-06-audit-round2.json
    python3 pipeline/merge_duplicate_deals_batch.py --specs ... --write
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'
FIXES_DIR = ROOT / 'pipeline' / 'ingest' / 'fixes'
INDEX_HTML = ROOT / 'static' / 'index.html'

PLACEHOLDER = re.compile(
    r'^\s*(—|-|не раскрыт[а-яё]*|публично не сообщалось|не привлекал[а-яё]*|нет данных|неизвестно)?\s*\.?\s*$',
    re.I)
EVENT_KINDS = {'closed', 'negotiations', 'cancelled', 'signed', 'approval', 'other', 'registered', 'announced'}
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
ID_FIELDS = {'buyer', 'seller_id', 'target', 'asset_id'}


def flat(text: str) -> str:
    """Сравнение «дословно с точностью до кавычек, тире и пробелов»: остаются
    только буквы и цифры. Так «ООО "Кама"» и «ООО «Кама»» — один текст."""
    return re.sub(r'[^0-9a-zа-яё]+', '', str(text or '').lower().replace('ё', 'е'))


def strings_of(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in strings_of(v)]
    if isinstance(value, list):
        return [s for v in value for s in strings_of(v)]
    return []


def card_text(card: dict) -> str:
    return ' '.join(strings_of(card))


def get_field(card: dict, path: str):
    node = card
    for part in path.split('.'):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def put_field(card: dict, path: str, value) -> None:
    parts = path.split('.')
    node = card
    for part in parts[:-1]:
        if not isinstance(node.get(part), dict):
            node[part] = {}
        node = node[part]
    node[parts[-1]] = value


def is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return bool(PLACEHOLDER.match(value))
    if isinstance(value, list):
        return not value
    return False


SENTENCE_SPLIT = re.compile(r'(?<=[.!?…])\s+(?=[«"(A-ZА-ЯЁ0-9])')


def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_SPLIT.split(text.strip()) if s.strip()]


NUMBER_RE = re.compile(r'\d+(?:[,.]\d+)?')
CAP_WORD_RE = re.compile(r'(?<![а-яёa-z])[А-ЯЁA-Z][а-яёa-z]{3,}')


def same_word(a: str, b: str) -> bool:
    """Одно слово с точностью до окончания — то же правило, что `_same_word`
    в review.py: общее начало не короче трёх знаков и не короче 60% более
    короткого слова. «Новое»/«новый», «Перспектива»/«Перспективы» — одно
    слово; «Иванов»/«Петров» — нет."""
    a, b = flat(a), flat(b)
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n >= 3 and n >= 0.6 * min(len(a), len(b))


def nothing_invented(note: str, corpus: str) -> list[str]:
    """Что в тексте события появилось из ниоткуда: число, которого нет ни в
    одной из двух карточек, или слово с заглавной, которого там нет ни в
    какой форме. Проверка не заменяет чтение — она ловит выдуманное имя и
    выдуманную цифру, а не пересказ не по делу."""
    corpus_flat = flat(corpus)
    corpus_words = set(re.findall(r'[0-9a-zа-яё]+', corpus.lower().replace('ё', 'е')))
    bad = []
    for num in NUMBER_RE.findall(note):
        if flat(num) not in corpus_flat:
            bad.append(num)
    for word in CAP_WORD_RE.findall(note):
        if flat(word) in corpus_flat:
            continue
        if not any(same_word(word, w) for w in corpus_words):
            bad.append(word)
    return bad


def industries() -> set[str]:
    m = re.search(r'const INDUSTRIES\s*=\s*\[([^\]]*)\]', INDEX_HTML.read_text(encoding='utf-8'))
    return set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()


def src_urls(card: dict) -> set[str]:
    return {s[1] for s in (card.get('src') or []) if isinstance(s, list) and len(s) > 1}


class Merge:
    def __init__(self, data: dict, spec: dict, known_ind: set[str], known_themes: set[str]):
        self.data, self.spec = data, spec
        self.by_id = {d['id']: d for d in data['deals']}
        self.keep_id, self.drop_id = spec['keep'], spec['drop']
        self.known_ind, self.known_themes = known_ind, known_themes
        self.errors: list[str] = []
        self.plan: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(f'{self.drop_id} -> {self.keep_id}: {msg}')

    def check(self) -> None:
        keep, drop = self.by_id.get(self.keep_id), self.by_id.get(self.drop_id)
        if not keep:
            return self.err('нет оставшейся карточки')
        if not drop:
            return self.err('нет удаляемой карточки (уже слита?)')
        if self.drop_id in self.data.get('merged', {}):
            return self.err('удаляемая карточка уже в merged')
        drop_text, keep_text = card_text(drop), card_text(keep)
        both = drop_text + ' ' + keep_text

        for field, value in (self.spec.get('set') or {}).items():
            current = get_field(keep, field)
            if not is_empty(current):
                self.err(f'set {field}: поле оставшейся уже заполнено: {str(current)[:60]!r}')
                continue
            if field in ID_FIELDS:
                if drop.get(field) != value:
                    self.err(f'set {field}: у дубля стоит {drop.get(field)!r}, а не {value!r}')
                elif value not in self.data['companies']:
                    self.err(f'set {field}: профиля {value} нет')
                else:
                    self.plan.append(f'  {field} = {value} ({self.data["companies"][value].get("name")})')
                continue
            if not isinstance(value, str) or not value.strip():
                self.err(f'set {field}: пустое значение')
                continue
            missing = [sent for sent in sentences(value) if flat(sent) not in flat(both)]
            if missing:
                self.err(f'set {field}: предложение не лежит дословно ни в одной карточке: {missing[0][:70]!r}')
                continue
            self.plan.append(f'  {field} <- {value[:70]!r}')

        extra_add = self.spec.get('append_extra')
        if extra_add:
            keep_extra_flat = flat(keep.get('extra') or '')
            take = []
            for sent in sentences(extra_add):
                if flat(sent) not in flat(both):
                    self.err(f'append_extra: предложение не лежит ни в одной карточке: {sent[:80]!r}')
                    continue
                if flat(sent) in keep_extra_flat:
                    self.plan.append(f'  extra: уже есть, пропуск: {sent[:50]!r}')
                    continue
                take.append(sent)
            self.extra_take = take
            if take:
                self.plan.append(f'  extra += {len(take)} предложений')
        else:
            self.extra_take = []

        have = src_urls(keep)
        self.src_take = []
        for item in self.spec.get('add_src') or []:
            if not (isinstance(item, list) and len(item) == 2 and item[1].startswith('http')):
                self.err(f'add_src: не пара [подпись, адрес]: {item!r}')
                continue
            if item[1] in have:
                self.plan.append(f'  src уже есть: {item[1]}')
                continue
            if item[1] not in json.dumps(drop, ensure_ascii=False):
                self.err(f'add_src: адреса нет в дубле: {item[1]}')
                continue
            self.src_take.append(item)
            self.plan.append(f'  src += {item[0]}: {item[1]}')

        self.events_take = []
        have_events = {(e.get('kind'), e.get('date')) for e in (keep.get('events') or [])}
        for ev in self.spec.get('events') or []:
            if ev.get('kind') not in EVENT_KINDS:
                self.err(f'event: неизвестный вид {ev.get("kind")!r}')
                continue
            if not DATE_RE.match(str(ev.get('date') or '')):
                self.err(f'event: дата не в формате ГГГГ-ММ-ДД: {ev.get("date")!r}')
                continue
            invented = nothing_invented((ev.get('title') or '') + ' ' + (ev.get('note') or ''), both)
            if invented:
                self.err(f'event {ev.get("kind")} {ev.get("date")}: в тексте есть то, чего нет в карточках: {invented}')
                continue
            if (ev['kind'], ev['date']) in have_events:
                self.plan.append(f'  event уже есть: {ev["kind"]} {ev["date"]}')
                continue
            src = ev.get('source')
            if src is not None and not (isinstance(src, list) and len(src) == 2):
                self.err(f'event: source не пара: {src!r}')
                continue
            clean = {k: ev[k] for k in ('kind', 'date', 'title', 'note', 'source') if k in ev}
            self.events_take.append(clean)
            self.plan.append(f'  event += {clean["kind"]} {clean["date"]} {clean.get("title", "")[:50]!r}')

        self.themes_take = []
        for theme in self.spec.get('add_themes') or []:
            if theme not in self.known_themes:
                self.err(f'theme неизвестна базе: {theme!r}')
                continue
            if theme in (keep.get('themes') or []):
                continue
            self.themes_take.append(theme)
            self.plan.append(f'  themes += {theme}')

        ind = self.spec.get('ind')
        if ind:
            if ind not in self.known_ind:
                self.err(f'отрасль вне списка INDUSTRIES: {ind!r}')
            elif keep.get('ind') != ind:
                self.plan.append(f'  ind: {keep.get("ind")!r} -> {ind!r}')

        posts = self.data.get('telegram_posts', {})
        if self.drop_id in posts:
            mid_drop, mid_keep = posts[self.drop_id], posts.get(self.keep_id)
            if mid_drop is not None and mid_keep is not None and mid_keep != mid_drop:
                self.err(f'у обеих карточек свои посты в канале: {mid_keep} и {mid_drop}')
            else:
                self.plan.append(f'  telegram_posts: {self.drop_id}={mid_drop} -> {self.keep_id}')
        for key in self.data.get('telegram_milestones', {}):
            if self.drop_id in key:
                self.err(f'у дубля есть веха в telegram_milestones: {key}')

        chained = [k for k, v in self.data.get('merged', {}).items() if v == self.drop_id]
        if chained:
            self.plan.append(f'  merged: {chained} -> {self.keep_id}')

    def apply(self) -> None:
        keep, drop = self.by_id[self.keep_id], self.by_id[self.drop_id]
        for field, value in (self.spec.get('set') or {}).items():
            put_field(keep, field, value)
        if self.extra_take:
            base = (keep.get('extra') or '').rstrip()
            keep['extra'] = (base + ' ' if base else '') + ' '.join(self.extra_take)
        if self.src_take:
            keep.setdefault('src', []).extend(self.src_take)
        if self.events_take:
            keep.setdefault('events', []).extend(self.events_take)
            keep['events'].sort(key=lambda e: e.get('date') or '')
        if self.themes_take:
            keep.setdefault('themes', []).extend(self.themes_take)
        if self.spec.get('ind'):
            keep['ind'] = self.spec['ind']
        posts = self.data.setdefault('telegram_posts', {})
        if self.drop_id in posts:
            mid = posts.pop(self.drop_id)
            if mid is not None or self.keep_id not in posts:
                posts[self.keep_id] = mid
        merged = self.data.setdefault('merged', {})
        for k, v in list(merged.items()):
            if v == self.drop_id:
                merged[k] = self.keep_id
        merged[self.drop_id] = self.keep_id
        self.data['deals'] = [d for d in self.data['deals'] if d['id'] != self.drop_id]


def fixes_entries(path: Path, ids: set[str]) -> list[tuple[int, int]]:
    """Строки (с 1, включительно) записей FIXES с id из списка."""
    tree = ast.parse(path.read_text(encoding='utf-8'))
    spans = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'FIXES' for t in node.targets) \
                and isinstance(node.value, ast.List):
            for el in node.value.elts:
                entry_id = None
                if isinstance(el, ast.Call):
                    for kw in el.keywords:
                        if kw.arg == 'id' and isinstance(kw.value, ast.Constant):
                            entry_id = kw.value.value
                elif isinstance(el, ast.Dict):
                    for k, v in zip(el.keys, el.values):
                        if isinstance(k, ast.Constant) and k.value == 'id' and isinstance(v, ast.Constant):
                            entry_id = v.value
                if entry_id in ids:
                    spans.append((el.lineno, el.end_lineno))
    return spans


def strip_fixes(ids: set[str], write: bool) -> int:
    removed = 0
    for path in sorted(FIXES_DIR.glob('*.py')):
        spans = fixes_entries(path, ids)
        if not spans:
            continue
        lines = path.read_text(encoding='utf-8').split('\n')
        drop_lines: set[int] = set()
        for start, end in spans:
            for n in range(start, end + 1):
                drop_lines.add(n)
            # запятая после закрывающей скобки записи стоит на той же строке — иначе
            # AST отдал бы другой end_lineno; комментарии прямо над записью,
            # называющие снятый id, тоже снимаются, чтобы не описывать пустоту
            n = start - 1
            while n >= 1 and lines[n - 1].strip().startswith('#') and any(i in lines[n - 1] for i in ids):
                drop_lines.add(n)
                n -= 1
        new_text = '\n'.join(l for i, l in enumerate(lines, 1) if i not in drop_lines)
        ast.parse(new_text)  # файл обязан остаться валидным Python
        before = len(fixes_entries(path, ids))
        print(f'FIXES {path.name}: снять {len(spans)} записей')
        removed += len(spans)
        if write:
            path.write_text(new_text, encoding='utf-8')
            assert not fixes_entries(path, ids), path
            assert before == len(spans)
    return removed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--specs', required=True)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    specs = json.load(open(args.specs, encoding='utf-8'))
    data = json.load(open(DATA, encoding='utf-8'))
    known_ind = industries()
    known_themes = {t for d in data['deals'] for t in (d.get('themes') or [])}
    before = len(data['deals'])

    merges, errors = [], []
    for spec in specs:
        m = Merge(data, spec, known_ind, known_themes)
        m.check()
        print(f'\n{spec["drop"]} -> {spec["keep"]}  ({spec.get("reason", "")[:90]}…)')
        for line in m.plan:
            print(line)
        for e in m.errors:
            print('  ОТКАЗ:', e)
        errors.extend(m.errors)
        merges.append(m)

    drop_ids = {s['drop'] for s in specs}
    print()
    fixes_removed = strip_fixes(drop_ids, write=False)
    print(f'\nСлияний: {len(merges)}, сделок {before} -> {before - len(merges)}, записей FIXES снять: {fixes_removed}')
    if errors:
        print(f'\nОТКАЗОВ: {len(errors)} — ничего не записано.')
        return 1
    if not args.write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for m in merges:
        m.apply()
    assert len(data['deals']) == before - len(merges)
    for m in merges:
        assert m.drop_id not in {d['id'] for d in data['deals']}
        assert data['merged'][m.drop_id] == m.keep_id
    strip_fixes(drop_ids, write=True)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
