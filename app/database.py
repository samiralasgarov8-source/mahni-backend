"""
SECTION 7: Verilənlər bazası bağlantısı (SQLAlchemy).
DATABASE_URL sqlite ilə başlayırsa lokal fayl istifadə olunur (quraşdırma lazım deyil).
Render-də Postgres veriləcəksə, DATABASE_URL env-i dəyişmək kifayətdir — kod dəyişmir.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: hər request üçün ayrıca DB sessiyası açır, sonda bağlayır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Tətbiq başlayanda bütün cədvəlləri (əgər yoxdursa) yaradır."""
    from . import models  # noqa: F401  (modellər import olunmalıdır ki, Base.metadata onları tanısın)
    Base.metadata.create_all(bind=engine)
