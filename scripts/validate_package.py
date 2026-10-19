#!/usr/bin/env python3
"""Validate the portable skill package and its checksums without network access."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/laizi-perspective'
MANIFEST = ROOT / 'package-manifest.json'
IGNORED = {'.git', '__pycache__', '.venv', 'venv', 'node_modules'}


def files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file()
                  and not any(part in IGNORED for part in p.relative_to(ROOT).parts)
                  and p != MANIFEST)


def snapshot():
    return {p.relative_to(ROOT).as_posix(): {
        'bytes': p.stat().st_size,
        'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
    } for p in files()}


def validate():
    text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    assert text.startswith('---\n'), 'missing YAML frontmatter'
    assert 'name: laizi-perspective\n' in text, 'wrong skill name'
    assert re.search(r'^description: .+', text, re.M), 'missing skill description'
    corpus = json.loads((SKILL / 'laizi_corpus.json').read_text(encoding='utf-8'))
    assert isinstance(corpus, list) and corpus, 'corpus must be a nonempty list'
    for i, entry in enumerate(corpus):
        assert isinstance(entry.get('text'), str) and entry['text'].strip(), f'empty text at {i}'
        assert isinstance(entry.get('source'), str) and entry['source'], f'empty source at {i}'
        assert isinstance(entry.get('quality'), (int, float)), f'invalid quality at {i}'
    forbidden_ext = {'.pem', '.key', '.db', '.sqlite', '.sqlite3', '.mp3', '.wav',
                     '.m4a', '.mp4', '.safetensors', '.pyc'}
    secrets = re.compile(r'\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})')
    private_key = re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
    email = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
    phone = re.compile(r'(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)')
    processing_metadata = re.compile(r'^\s*(?:Duration|Transcription time|Realtime ratio)\s*:', re.M | re.I)
    for p in files():
        assert p.suffix.lower() not in forbidden_ext, f'unexpected binary or credential: {p.name}'
        assert p.name != '.env' and 'cookie' not in p.name.lower(), f'unexpected private config: {p.name}'
        data = p.read_text(encoding='utf-8')
        assert not secrets.search(data), f'possible token in {p.name}'
        assert not private_key.search(data), f'possible private key in {p.name}'
        assert not email.search(data), f'email address in {p.name}'
        assert not phone.search(data), f'phone-number candidate in {p.name}'
        assert not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|/(?:Users|home|mnt)/[^\s]+', data), f'absolute machine path in {p.name}'
        if p.suffix == '.md':
            for target in re.findall(r'\]\(([^)]+)\)', data):
                if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                    continue
                local = target.split('#')[0].split(' "')[0]
                target_path = p.parent / local
                assert target_path.resolve() == MANIFEST or target_path.exists(), f'broken link in {p.name}: {local}'
    provenance = json.loads((ROOT / 'source-provenance.json').read_text(encoding='utf-8'))
    assert provenance.get('format') == 'skill-release-v1', 'unexpected provenance format'
    assert set(entry['destination'] for entry in provenance['files']) == {
        p.relative_to(SKILL).as_posix() for p in SKILL.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts
    }, 'release inventory has missing or extra files'
    for entry in provenance['files']:
        assert set(entry) == {'destination', 'packaged_sha256'}, 'legacy source metadata found'
        dest = SKILL / entry['destination']
        assert dest.is_file(), f'missing source asset: {entry["destination"]}'
        actual_hash = hashlib.sha256(dest.read_bytes()).hexdigest()
        assert actual_hash == entry['packaged_sha256'], f'stale source hash: {entry["destination"]}'
    if (ROOT / '.git').exists():
        probe = subprocess.run(['git', 'log', '--all', '--format=%ae%n%ce'], cwd=ROOT,
                               capture_output=True, text=True)
        if probe.returncode == 0:
            for address in probe.stdout.splitlines():
                assert address.endswith('@users.noreply.github.com') or address == 'noreply' + '@' + 'github.com', 'non-anonymous commit email'
    return {'corpus_entries': len(corpus),
            'transcript_files': len(list((SKILL / 'references/sources/transcripts').glob('*.txt'))),
            'files': len(files()) + 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update-manifest', action='store_true')
    args = parser.parse_args()
    if args.update_manifest:
        provenance_path = ROOT / 'source-provenance.json'
        provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
        provenance['files'] = [{'destination': p.relative_to(SKILL).as_posix(),
                                'packaged_sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                               for p in sorted(SKILL.rglob('*'))
                               if p.is_file() and '__pycache__' not in p.parts]
        provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n',
                                   encoding='utf-8', newline='\n')
    counts = validate()
    current = snapshot()
    if args.update_manifest:
        MANIFEST.write_text(json.dumps({'counts': counts, 'files': current}, ensure_ascii=False, indent=2)
                            + '\n', encoding='utf-8', newline='\n')
    else:
        expected = json.loads(MANIFEST.read_text(encoding='utf-8'))
        assert expected['files'] == current, 'file set or checksum changed; review and update manifest'
        assert expected['counts'] == counts, 'package counts changed'
    print(json.dumps({'status': 'PASS', **counts}, ensure_ascii=False))


if __name__ == '__main__':
    main()
