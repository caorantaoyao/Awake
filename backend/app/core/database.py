from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
from .migrations import (
    migrate_conversations,
    migrate_growth_schema,
    migrate_onboarding,
    migrate_password_hashes,
    migrate_profile_welcome_message,
    migrate_student_preferences,
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    migrate_password_hashes(engine, settings.AUTH_LEGACY_USER_DEFAULT_PASSWORD)
    migrate_growth_schema(engine)
    migrate_student_preferences(engine)
    migrate_conversations(engine)
    migrate_onboarding(engine)
    migrate_profile_welcome_message(engine)
