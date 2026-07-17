from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class GradeEnum(str, enum.Enum):
    GRADE_10 = "高一"
    GRADE_11 = "高二"
    GRADE_12 = "高三"


class TaskStatusEnum(str, enum.Enum):
    IN_PROGRESS = "进行中"
    COMPLETED = "已完成"
    EXPIRED = "已过期"


class ChatModeEnum(str, enum.Enum):
    EXPLORE_FIRST = "explore_first"
    BALANCED = "balanced"
    DIRECT_ACTION = "direct_action"


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    grade = Column(Enum(GradeEnum), nullable=False)
    password_hash = Column(String(255), nullable=True)
    chat_mode = Column(String(20), nullable=False, server_default="explore_first")
    unlock_after_turns = Column(Integer, nullable=False, server_default="3")
    onboarding_completed = Column(Boolean, nullable=False, server_default="0")
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    operation_log = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tasks = relationship("Task", back_populates="student", cascade="all, delete-orphan")
    profile = relationship(
        "StudentProfile",
        back_populates="student",
        cascade="all, delete-orphan",
        uselist=False,
    )
    conversation_messages = relationship(
        "ConversationMessage",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    conversations = relationship(
        "Conversation",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    growth_events = relationship(
        "GrowthEvent",
        back_populates="student",
        cascade="all, delete-orphan",
    )


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "estimated_minutes BETWEEN 5 AND 30",
            name="ck_tasks_estimated_minutes",
        ),
        CheckConstraint("growth_points > 0", name="ck_tasks_growth_points"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.IN_PROGRESS, nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=True)
    feedback = Column(Text, nullable=True)
    estimated_minutes = Column(Integer, default=15, server_default="15", nullable=False)
    growth_points = Column(Integer, default=10, server_default="10", nullable=False)
    topic_tags = Column(Text, default="[]", server_default="[]", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    operation_log = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="tasks")
    growth_events = relationship("GrowthEvent", back_populates="task")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    interest_tags = Column(Text, default="[]", server_default="[]", nullable=False)
    ability_tags = Column(Text, default="[]", server_default="[]", nullable=False)
    exploration_stage = Column(
        String(50),
        default="探索中",
        server_default="探索中",
        nullable=False,
    )
    summary = Column(Text, default="", server_default="", nullable=False)
    welcome_message = Column(Text, default="", server_default="", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    student = relationship("Student", back_populates="profile")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant')",
            name="ck_conversation_messages_role",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student = relationship("Student", back_populates="conversation_messages")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    thread_id = Column(String(100), nullable=False, unique=True, index=True)
    title = Column(String(200), nullable=False, default="新对话")
    model_name = Column(String(100), nullable=True)
    thinking_enabled = Column(Boolean, default=False, server_default="0", nullable=False)
    is_plan_mode = Column(Boolean, default=False, server_default="0", nullable=False)
    is_active = Column(Boolean, default=True, server_default="1", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    student = relationship("Student", back_populates="conversations")


class GrowthResource(Base):
    __tablename__ = "growth_resources"
    __table_args__ = (
        CheckConstraint(
            "resource_type IN ('课程', '活动', '竞赛', '实践')",
            name="ck_growth_resources_type",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    resource_type = Column(String(20), nullable=False, index=True)
    description = Column(Text, nullable=False)
    url = Column(Text, nullable=True)
    topic_tags = Column(Text, default="[]", server_default="[]", nullable=False)
    ability_tags = Column(Text, default="[]", server_default="[]", nullable=False)
    suitable_grades = Column(Text, default="[]", server_default="[]", nullable=False)
    exploration_stages = Column(Text, default="[]", server_default="[]", nullable=False)
    is_active = Column(Boolean, default=True, server_default="1", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class GrowthEvent(Base):
    __tablename__ = "growth_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    growth_points = Column(Integer, default=0, server_default="0", nullable=False)
    topic_tags = Column(Text, default="[]", server_default="[]", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student = relationship("Student", back_populates="growth_events")
    task = relationship("Task", back_populates="growth_events")
