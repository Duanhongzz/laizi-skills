#!/usr/bin/env python3
"""Read-only corpus search with source locations, runnable from any directory."""
import argparse
import json
import sys
from pathlib import Path

from build_corpus import PROJECT, TRANS_DIR, REFERENCES_DIR, load_corpus, search


def source_location(source):
    if source.startswith('reference:'):
        name, _, line = source[len('reference:'):].rpartition(':')
        if not line.isdigit():
            name, line = source[len('reference:'):], ''
        path = REFERENCES_DIR / name
        return path.relative_to(PROJECT).as_posix() + (':' + line if line else '') if path.is_file() else None
    if source.startswith(('manual-', 'alias-', 'auto-')):
        return None
    candidates = [p for p in TRANS_DIR.glob('*.txt') if p.stem[:60] == source]
    return candidates[0].relative_to(PROJECT).as_posix() if len(candidates) == 1 else None


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query')
    parser.add_argument('--top-k', type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.top_k <= 20:
        parser.error('--top-k must be between 1 and 20')
    results = search(args.query, load_corpus(), top_k=args.top_k)
    payload = []
    for score, item in results:
        source = item.get('source', '')
        payload.append({'score': round(score, 4), 'source': source,
                        'source_file': source_location(source), 'text': item['text']})
    print(json.dumps({'query': args.query, 'results': payload}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
