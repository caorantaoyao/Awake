from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.services.auth_service import hash_password


def _table_exists(connection, table_name: str) -> bool:
    return connection.execute(
        text(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = :table_name"
        ),
        {"table_name": table_name},
    ).scalar() is not None


def migrate_password_hashes(engine: Engine, legacy_password: str) -> None:
    with engine.begin() as connection:
        if not _table_exists(connection, "students"):
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


def migrate_growth_schema(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        if not _table_exists(connection, "students"):
            return

        if _table_exists(connection, "tasks"):
            task_columns = {
                row[1] for row in connection.execute(text("PRAGMA table_info(tasks)"))
            }
            additions = {
                "estimated_minutes": (
                    "ALTER TABLE tasks ADD COLUMN "
                    "estimated_minutes INTEGER NOT NULL DEFAULT 15"
                ),
                "growth_points": (
                    "ALTER TABLE tasks ADD COLUMN "
                    "growth_points INTEGER NOT NULL DEFAULT 10"
                ),
                "topic_tags": (
                    "ALTER TABLE tasks ADD COLUMN "
                    "topic_tags TEXT NOT NULL DEFAULT '[]'"
                ),
            }
            for column_name, statement in additions.items():
                if column_name not in task_columns:
                    connection.execute(text(statement))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL UNIQUE,
                interest_tags TEXT NOT NULL DEFAULT '[]',
                ability_tags TEXT NOT NULL DEFAULT '[]',
                exploration_stage VARCHAR(50) NOT NULL DEFAULT '探索中',
                summary TEXT NOT NULL DEFAULT '',
                welcome_message TEXT NOT NULL DEFAULT '',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                role VARCHAR(20) NOT NULL
                    CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS growth_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                resource_type VARCHAR(20) NOT NULL
                    CHECK (resource_type IN ('课程', '活动', '竞赛', '实践')),
                description TEXT NOT NULL,
                url TEXT,
                topic_tags TEXT NOT NULL DEFAULT '[]',
                ability_tags TEXT NOT NULL DEFAULT '[]',
                suitable_grades TEXT NOT NULL DEFAULT '[]',
                exploration_stages TEXT NOT NULL DEFAULT '[]',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS growth_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                task_id INTEGER,
                event_type VARCHAR(50) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                growth_points INTEGER NOT NULL DEFAULT 0,
                topic_tags TEXT NOT NULL DEFAULT '[]',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id),
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        """))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_student_profiles_student_id "
            "ON student_profiles (student_id)"
        ))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_conversation_messages_student_id "
            "ON conversation_messages (student_id)"
        ))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_growth_resources_resource_type "
            "ON growth_resources (resource_type)"
        ))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_growth_events_student_id "
            "ON growth_events (student_id)"
        ))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_growth_events_task_id "
            "ON growth_events (task_id)"
        ))


def migrate_student_preferences(engine: Engine) -> None:
    with engine.begin() as connection:
        if not _table_exists(connection, "students"):
            return

        columns = {row[1] for row in connection.execute(text("PRAGMA table_info(students)"))}
        if "chat_mode" not in columns:
            connection.execute(text(
                "ALTER TABLE students ADD COLUMN chat_mode VARCHAR(20) "
                "NOT NULL DEFAULT 'explore_first'"
            ))
        if "unlock_after_turns" not in columns:
            connection.execute(text(
                "ALTER TABLE students ADD COLUMN unlock_after_turns "
                "INTEGER NOT NULL DEFAULT 3"
            ))


def migrate_onboarding(engine: Engine) -> None:
    with engine.begin() as connection:
        if not _table_exists(connection, "students"):
            return

        columns = {row[1] for row in connection.execute(text("PRAGMA table_info(students)"))}
        if "onboarding_completed" not in columns:
            connection.execute(text(
                "ALTER TABLE students ADD COLUMN onboarding_completed "
                "BOOLEAN NOT NULL DEFAULT 0"
            ))


def migrate_profile_welcome_message(engine: Engine) -> None:
    with engine.begin() as connection:
        if not _table_exists(connection, "student_profiles"):
            return
        columns = {row[1] for row in connection.execute(text("PRAGMA table_info(student_profiles)"))}
        if "welcome_message" not in columns:
            connection.execute(text(
                "ALTER TABLE student_profiles ADD COLUMN welcome_message "
                "TEXT NOT NULL DEFAULT ''"
            ))


def migrate_conversations(engine: Engine) -> None:
    with engine.begin() as connection:
        if _table_exists(connection, "conversations"):
            return
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                thread_id VARCHAR(100) NOT NULL UNIQUE,
                title VARCHAR(200) NOT NULL DEFAULT '新对话',
                model_name VARCHAR(100),
                thinking_enabled BOOLEAN NOT NULL DEFAULT 0,
                is_plan_mode BOOLEAN NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
        """))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_conversations_student_id "
            "ON conversations (student_id)"
        ))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_conversations_thread_id "
            "ON conversations (thread_id)"
        ))
