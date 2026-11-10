"""Fail-closed guards for the V4.5.2 R2 external acceptance pipeline."""
from pathlib import Path
import pytest
from scripts.apply_test_migrations_v452 import validate_url

ROOT = Path(__file__).resolve().parent

@pytest.mark.parametrize('url', [
    '',
    'sqlite:///formula_ci_test',
    'postgresql://user:pass@localhost/production',
    'postgresql://user:pass@localhost/formula_rd',
    'postgresql://user:pass@/formula_ci_test',
])
def test_migration_refuses_non_dedicated_targets(url):
    with pytest.raises(ValueError):
        validate_url(url)


def test_migration_accepts_only_explicit_test_database():
    assert validate_url('postgresql+psycopg://u:p@localhost:5432/formula_ci_test') == \
        'postgresql://u:p@localhost:5432/formula_ci_test'


def test_browser_exercised_pages_and_api_rewrite_are_grounded():
    smoke=(ROOT/'scripts/browser_smoke_v452.py').read_text(encoding='utf-8')
    assert all(x in smoke for x in ("'/optimizer'", "'/experiments'", "'/backend/health/v4.5'"))
    next_config=(ROOT/'frontend/next.config.ts').read_text(encoding='utf-8')
    assert "source: '/backend/:path*'" in next_config


def test_default_development_servers_are_local_only():
    shell=(ROOT/'scripts/run_backend.sh').read_text(encoding='utf-8')
    compose=(ROOT/'compose.yaml').read_text(encoding='utf-8')
    assert '--host 127.0.0.1' in shell
    assert '127.0.0.1:3000:3000' in compose
