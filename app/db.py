"""Database connection for local SQLite and managed Neon PostgreSQL.

Production-like test environments must explicitly require PostgreSQL, so the
service refuses to start instead of silently creating ephemeral SQLite files.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

def database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///./feridas_dev.db").strip()
    require_postgres = os.getenv("FERIDAS_REQUIRE_POSTGRES", "false").lower() == "true"
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    if require_postgres and not url.startswith("postgresql+psycopg://"):
        raise RuntimeError("PostgreSQL obrigatório: configure DATABASE_URL do Neon no Render")
    if not url:
        raise RuntimeError("DATABASE_URL não configurada")
    return url

DATABASE_URL = database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as session:
        yield session
