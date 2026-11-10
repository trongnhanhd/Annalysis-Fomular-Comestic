"""Choose dev SQLite or a PostgreSQL repository explicitly.

Production has no automatic migration. Apply migrations/001_v451_init.sql first.
"""
from __future__ import annotations
import os
from experimental_repository_v45 import Repository


def open_repository():
    url = os.environ.get('V45_DATABASE_URL', '').strip()
    if not url:
        return Repository()
    if not url.startswith(('postgresql://', 'postgresql+psycopg://')):
        raise RuntimeError('V45_DATABASE_URL chỉ hỗ trợ PostgreSQL; SQLite dev sử dụng V45_DB_PATH')
    from experimental_repository_postgres_v451 import PostgresRepository
    return PostgresRepository(url)


def storage_name():
    return 'postgresql' if os.environ.get('V45_DATABASE_URL') else 'sqlite_demo'
