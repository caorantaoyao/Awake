from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
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


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    grade = Column(Enum(GradeEnum), nullable=False)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    operation_log = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tasks = relationship("Task", back_populates="student", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.IN_PROGRESS, nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    operation_log = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="tasks")
