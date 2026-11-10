"""Apply 001/002 to a DEDICATED disposable PostgreSQL *_test database only.

Fail closed if URL missing, ambiguous, or not an explicit test DB. This is not
an upgrade tool for production; do not use on databases holding real R&D data.
"""
from __future__ import annotations
import os
from pathlib import Path
from sqlalchemy.engine.url import make_url

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = [ROOT / 'migrations/001_v451_init.sql', ROOT / 'migrations/002_v452_traceability.sql']


def validate_url(raw: str) -> str:
    if not raw:
        raise ValueError('TEST_POSTGRES_URL is required; refusing to guess a target database')
    parsed = make_url(raw)
    if not parsed.drivername.startswith('postgresql') or not (parsed.database or '').endswith('_test'):
        raise ValueError('Only a dedicated PostgreSQL database ending in _test is permitted')
    if not parsed.host:
        raise ValueError('PostgreSQL hostname must be explicit')
    return raw.replace('postgresql+psycopg://', 'postgresql://', 1)


def main() -> int:
    dsn = validate_url(os.environ.get('TEST_POSTGRES_URL', ''))
    import psycopg
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.rnd_v451_studies'), to_regclass('public.rnd_v452_candidates'), to_regclass('public.rnd_v452_batch_provenance')")
            a, b, c = (v is not None for v in cur.fetchone())
            if b != c:
                raise RuntimeError('Partial 002 schema detected: stop for manual review')
            if b and not a:
                raise RuntimeError('002 schema without 001: stop for manual review')
            pending = ([] if b else [MIGRATIONS[1]]) if a else MIGRATIONS
            for source in pending:
                sql = source.read_text(encoding='utf-8')
                cur.execute(sql, prepare=False)
                print(f'APPLIED {source.name} to test database')
            if not pending:
                print('SKIP migrations: test database already has 001 and 002')
            cur.execute("SELECT to_regclass('public.rnd_v451_studies'), to_regclass('public.rnd_v452_candidates'), to_regclass('public.rnd_v452_batch_provenance')")
            if any(value is None for value in cur.fetchone()):
                raise RuntimeError('Expected tables absent after migrations')
    print('PASS: dedicated PostgreSQL _test schema ready')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
