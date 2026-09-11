"""從題幹建立可重建的生字候選清單，不修改資料庫。"""
import argparse
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

LEVELS = {f'第{number}級': i for i, number in enumerate('一二三四五六', 1)}


def build(source, database):
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as conn:
        dictionary = {}
        for english, chinese, folder in conn.execute('SELECT english,chinese,folder FROM words ORDER BY id'):
            word = english.strip().lower()
            if folder in LEVELS and re.fullmatch(r"[a-z]{2,}(?:[-'][a-z]+)*", word):
                if word not in dictionary or LEVELS[folder] < dictionary[word]['level']:
                    dictionary[word] = {'word': word, 'meaning': chinese, 'level': LEVELS[folder]}
    entries, audit = {}, Counter()
    for path in sorted(source.rglob('*.md')):
        if '知識點' in path.parts or path.name.startswith('_'):
            continue
        audit['documents'] += 1
        content = path.read_text(encoding='utf-8')
        match = re.search(r'^## 題目內容\s*\n(.*?)(?=^## |^---\s*$|\Z)', content, re.M | re.S)
        if not match or not match[1].strip():
            audit['missing_body'] += 1
            continue
        body = match[1].strip()
        if '原試卷未附簡答' in content:
            audit['answer_unavailable_label'] += 1
        if re.match(r'^\d+[.、]?\s*\(A\)', body):
            audit['options_only_candidate'] += 1
        relative = path.relative_to(source).as_posix()
        exam = path.parent.relative_to(source).as_posix()
        tokens = set(re.findall(r"[a-z]{2,}(?:[-'][a-z]+)*", body.lower()))
        for word in sorted(tokens & dictionary.keys()):
            entry = entries.setdefault(word, {**dictionary[word], 'exams': set(), 'question_count': 0, 'sources': []})
            entry['exams'].add(exam)
            entry['question_count'] += 1
            if len(entry['sources']) < 3 and all(s['exam'] != exam for s in entry['sources']):
                pos = body.lower().find(word)
                start, end = max(0, pos - 100), min(len(body), pos + len(word) + 160)
                entry['sources'].append({'id': relative, 'exam': exam, 'label': path.stem,
                    'excerpt': ('…' if start else '') + body[start:end] + ('…' if end < len(body) else '')})
    items = []
    for entry in entries.values():
        entry['exam_count'] = len(entry.pop('exams'))
        items.append(entry)
    items.sort(key=lambda e: (e['level'], -e['exam_count'], e['word']))
    return {'version': 1, 'audit': dict(audit), 'items': items}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.source, args.database)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'audit': result['audit'], 'candidates': len(result['items'])}, ensure_ascii=False))
