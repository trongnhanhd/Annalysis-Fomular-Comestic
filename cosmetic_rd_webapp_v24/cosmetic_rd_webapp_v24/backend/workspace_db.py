"""Persistence layer. PostgreSQL in Docker; optional SQLite for offline local testing.

Research drafts never flow into the reviewed scientific catalog or LP constraints.
"""
from __future__ import annotations
import os
import uuid
from datetime import datetime, timezone
from typing import Generator
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session
from sqlalchemy.pool import StaticPool


def utcnow():
    return datetime.now(timezone.utc)

DB_URL = os.getenv('DATABASE_URL', 'sqlite:///./cosmetic_rd_local.db')
kwargs = {'pool_pre_ping': True}
if DB_URL.startswith('sqlite'):
    kwargs['connect_args'] = {'check_same_thread': False}
    if DB_URL in ('sqlite://', 'sqlite:///:memory:'):
        kwargs['poolclass'] = StaticPool
engine = create_engine(DB_URL, **kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

JSON_FIELD = JSON().with_variant(JSONB, 'postgresql')

class Product(Base):
    __tablename__ = 'products'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(220), nullable=False)
    brand: Mapped[str] = mapped_column(String(160), default='')
    market: Mapped[str] = mapped_column(String(12), default='VN')
    product_type: Mapped[str] = mapped_column(String(60), default='leave_on')
    inci: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    analyses: Mapped[list['AnalysisRun']] = relationship(back_populates='product', cascade='all, delete-orphan')
    formulas: Mapped[list['FormulaVersion']] = relationship(back_populates='product', cascade='all, delete-orphan')

class AnalysisRun(Base):
    __tablename__ = 'analysis_runs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(ForeignKey('products.id'), index=True)
    input_snapshot: Mapped[dict] = mapped_column(JSON_FIELD, nullable=False)
    result_snapshot: Mapped[dict] = mapped_column(JSON_FIELD, nullable=False)
    result_status: Mapped[str] = mapped_column(String(35), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    product: Mapped[Product] = relationship(back_populates='analyses')

class ResearchRecord(Base):
    __tablename__ = 'research_records'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inci: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(350), nullable=False)
    study_type: Mapped[str] = mapped_column(String(65), default='unspecified')
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    doi: Mapped[str] = mapped_column(String(200), default='')
    min_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_type: Mapped[str] = mapped_column(String(60), default='unspecified')
    matrix: Mapped[str] = mapped_column(String(250), default='')
    notes: Mapped[str] = mapped_column(Text, default='')
    review_status: Mapped[str] = mapped_column(String(35), default='draft')
    reviewed_by: Mapped[str] = mapped_column(String(150), default='')
    review_note: Mapped[str] = mapped_column(Text, default='')
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class FormulaVersion(Base):
    __tablename__ = 'formula_versions'
    __table_args__ = (UniqueConstraint('product_id', 'version', name='uq_formula_product_version'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(ForeignKey('products.id'), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    ingredients: Mapped[list] = mapped_column(JSON_FIELD, nullable=False)
    name: Mapped[str] = mapped_column(String(200), default='Công thức giả thuyết')
    notes: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(String(40), default='hypothesis')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    product: Mapped[Product] = relationship(back_populates='formulas')

def initialize_database():
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
