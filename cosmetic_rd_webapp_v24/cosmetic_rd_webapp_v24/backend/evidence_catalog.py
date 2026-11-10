"""Versioned, hand-reviewed examples of evidence & regulation, NOT exhaustive legal database.

All data are read from local JSON and never scraped dynamically. No probabilistic
prediction or legal compliance claim is made by the catalogue.
"""
from functools import lru_cache
import json
from pathlib import Path
from typing import Optional

DATA = Path(__file__).resolve().parent / 'data'

@lru_cache(maxsize=2)
def _read(name: str) -> dict:
    with (DATA / name).open('r', encoding='utf-8') as handle:
        return json.load(handle)


def evidence_meta() -> dict:
    data = _read('evidence_catalog.json')
    return {k: v for k, v in data.items() if k != 'records'} | {'record_count': len(data['records'])}


def regulatory_meta() -> dict:
    data = _read('regulatory_catalog.json')
    return {k: v for k, v in data.items() if k != 'records'} | {'record_count': len(data['records'])}


def find_studies(inci: Optional[str] = None, category: Optional[str] = None) -> list[dict]:
    rows = _read('evidence_catalog.json')['records']
    return [dict(row) for row in rows if (not inci or row['inci'].casefold() == inci.strip().casefold())
            and (not category or row['category'] == category)]


def find_limits(inci: Optional[str] = None, market: Optional[str] = None) -> list[dict]:
    rows = _read('regulatory_catalog.json')['records']
    return [dict(row) for row in rows if (not inci or row['inci'].casefold() == inci.strip().casefold())
            and (not market or row['market'] == market.upper())]


def preservation_meta() -> dict:
    data = _read('preservation_systems.json')
    return {k: v for k, v in data.items() if k != 'records'} | {'record_count': len(data['records'])}


def find_preservation_systems(inci: Optional[str] = None) -> list[dict]:
    rows = _read('preservation_systems.json')['records']
    return [dict(row) for row in rows if not inci or any(x.casefold() == inci.casefold() for x in row['composition_pct'])]
