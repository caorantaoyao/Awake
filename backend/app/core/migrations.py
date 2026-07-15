from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.services.auth_service import hash_password


def migrate_password_hashes(engine: Engine, legacy_password: str) -> None:
    with engine.begin() as connection:
        students_table = connection.execute(text(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'students'"
        )).scalar()
        if not students_table:
            return

        columns = [row[1] for row in connection.execute(text("PRAGMA table_info(students)"))]
        if "password_hash" not in columns:
            connection.execute(text("ALTER TABLE students ADD COLUMN password_hash VARCHAR(255)"))

        legacy_rows = connection.execute(text("""
            SELECT id FROM students
            WHERE password_hash IS NULL OR password_hash = ''
        """)).mappings().all()
        for row in legacy_rows:
            connection.execute(
                text("UPDATE students SET password_hash = :password_hash WHERE id = :id"),
                {"password_hash": hash_password(legacy_password), "id": row["id"]}
            )
