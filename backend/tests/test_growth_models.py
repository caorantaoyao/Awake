import importlib

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.models import models


def _model(name):
    model = getattr(models, name, None)
    assert model is not None, f"{name} model is missing"
    return model


def test_growth_models_persist_required_defaults_and_student_profile_is_unique(db_session):
    StudentProfile = _model("StudentProfile")
    ConversationMessage = _model("ConversationMessage")
    GrowthResource = _model("GrowthResource")
    GrowthEvent = _model("GrowthEvent")

    student = models.Student(
        name="成长测试学生",
        email="growth-model@example.com",
        grade=models.GradeEnum.GRADE_10,
        password_hash="test-hash",
    )
    db_session.add(student)
    db_session.flush()

    profile = StudentProfile(student_id=student.id)
    message = ConversationMessage(
        student_id=student.id,
        role="user",
        content="我最近开始关注机器人。",
    )
    resource = GrowthResource(
        title="机器人入门实践",
        resource_type="实践",
        description="用一个小项目了解机器人。",
    )
    event = GrowthEvent(
        student_id=student.id,
        event_type="profile_updated",
        title="画像已更新",
    )
    task = models.Task(
        student_id=student.id,
        description="用 15 分钟了解机器人传感器",
    )
    db_session.add_all([profile, message, resource, event, task])
    db_session.commit()

    assert profile.interest_tags == "[]"
    assert profile.ability_tags == "[]"
    assert profile.exploration_stage == "探索中"
    assert profile.summary == ""
    assert message.role == "user"
    assert resource.topic_tags == "[]"
    assert resource.suitable_grades == "[]"
    assert resource.exploration_stages == "[]"
    assert resource.is_active is True
    assert event.growth_points == 0
    assert event.topic_tags == "[]"
    assert task.estimated_minutes == 15
    assert task.growth_points == 10
    assert task.topic_tags == "[]"

    db_session.add(StudentProfile(student_id=student.id))
    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.parametrize(
    ("estimated_minutes", "growth_points"),
    [(4, 10), (31, 10), (15, 0)],
)
def test_task_rejects_invalid_growth_values(
    db_session,
    estimated_minutes,
    growth_points,
):
    student = models.Student(
        name="约束测试学生",
        email=f"constraint-{estimated_minutes}-{growth_points}@example.com",
        grade=models.GradeEnum.GRADE_11,
        password_hash="test-hash",
    )
    db_session.add(student)
    db_session.flush()
    db_session.add(models.Task(
        student_id=student.id,
        description="约束测试任务",
        estimated_minutes=estimated_minutes,
        growth_points=growth_points,
    ))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_growth_migration_upgrades_legacy_sqlite_idempotently_without_data_loss(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy-growth.db'}")
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                grade VARCHAR(16) NOT NULL,
                password_hash VARCHAR(255),
                registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                operation_log DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        connection.execute(text("""
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                status VARCHAR(16) NOT NULL DEFAULT '进行中',
                deadline DATETIME,
                feedback TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                operation_log DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
        """))
        connection.execute(text("""
            INSERT INTO students (name, email, grade, password_hash)
            VALUES ('旧库学生', 'legacy-growth@example.com', '高一', 'existing-hash')
        """))
        connection.execute(text("""
            INSERT INTO tasks (student_id, description)
            VALUES (1, '旧库任务')
        """))

    migrations = importlib.import_module("app.core.migrations")
    migrate_growth_schema = getattr(migrations, "migrate_growth_schema", None)
    assert migrate_growth_schema is not None, "growth schema migration is missing"

    migrate_growth_schema(engine)
    migrate_growth_schema(engine)

    inspector = inspect(engine)
    assert {
        "student_profiles",
        "conversation_messages",
        "growth_resources",
        "growth_events",
    }.issubset(inspector.get_table_names())
    assert {
        "estimated_minutes",
        "growth_points",
        "topic_tags",
    }.issubset({column["name"] for column in inspector.get_columns("tasks")})

    with engine.begin() as connection:
        legacy_student = connection.execute(text("""
            SELECT name, email, password_hash FROM students WHERE id = 1
        """)).one()
        legacy_task = connection.execute(text("""
            SELECT description, estimated_minutes, growth_points, topic_tags
            FROM tasks WHERE id = 1
        """)).one()

    assert legacy_student == (
        "旧库学生",
        "legacy-growth@example.com",
        "existing-hash",
    )
    assert legacy_task == ("旧库任务", 15, 10, "[]")
