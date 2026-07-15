from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import List
import logging

from app.core.database import get_db
from app.models.models import Student, Task, TaskStatusEnum, GradeEnum
from app.schemas.schemas import (
    StudentRegisterRequest,
    StudentResponse,
    TaskCreateRequest,
    TaskCompleteRequest,
    TaskResponse,
    StudentWithTasksResponse,
    ApiResponse,
    ChatRequest,
    ChatResponse,
    ExtractTaskRequest
)
from app.services.email_service import email_service
from app.services.feishu_service import feishu_service
from app.services.deerflow_service import deerflow_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def register_student(
    request: StudentRegisterRequest,
    db: Session = Depends(get_db)
):
    existing = db.query(Student).filter(Student.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已注册"
        )

    try:
        student = Student(
            name=request.name,
            email=request.email,
            grade=GradeEnum(request.grade.value)
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        email_service.send_welcome_email(request.email, request.name)
        await feishu_service.notify_new_student({
            "name": student.name,
            "email": student.email,
            "grade": student.grade.value
        })

        logger.info(f"新用户注册成功: {student.name} ({student.email})")

        return ApiResponse(
            success=True,
            message="注册成功！欢迎邮件已发送至您的邮箱，请查收并开始与小海对话。",
            data={
                "student": StudentResponse.model_validate(student).model_dump()
            }
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已注册"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/api/tasks", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: TaskCreateRequest,
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.email == request.student_email).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )

    try:
        task = Task(
            student_id=student.id,
            description=request.description,
            deadline=request.deadline
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        await feishu_service.notify_task_created(
            {"id": task.id, "description": task.description},
            {"name": student.name, "email": student.email}
        )

        logger.info(f"任务创建成功: 学生 {student.name}, 任务ID {task.id}")

        return ApiResponse(
            success=True,
            message="任务创建成功",
            data={
                "task": TaskResponse.model_validate(task).model_dump()
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"任务创建失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="任务创建失败"
        )


@router.post("/api/task-complete", response_model=ApiResponse)
async def complete_task(
    request: TaskCompleteRequest,
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == request.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    if task.status == TaskStatusEnum.COMPLETED:
        return ApiResponse(
            success=True,
            message="任务已完成，无需重复打卡",
            data={
                "task": TaskResponse.model_validate(task).model_dump()
            }
        )

    try:
        task.status = TaskStatusEnum.COMPLETED
        task.completed_at = datetime.now()
        task.feedback = request.feedback
        db.commit()
        db.refresh(task)

        student = db.query(Student).filter(Student.id == task.student_id).first()
        await feishu_service.notify_task_complete(
            {"id": task.id, "description": task.description, "feedback": task.feedback},
            {"name": student.name, "email": student.email} if student else {}
        )

        logger.info(f"任务打卡成功: 任务ID {task.id}")

        return ApiResponse(
            success=True,
            message="打卡成功！太棒了，继续加油！",
            data={
                "task": TaskResponse.model_validate(task).model_dump()
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"打卡失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="打卡失败，请稍后重试"
        )


@router.get("/api/students/{email}", response_model=StudentWithTasksResponse)
def get_student(email: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == email).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )
    return StudentWithTasksResponse.model_validate(student)


@router.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    return TaskResponse.model_validate(task)


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    msg_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
    result = await deerflow_service.chat(msg_dicts, request.student_name)

    user_turns = sum(1 for m in request.messages if m.role == "user")
    can_extract_task = user_turns >= 3

    return ChatResponse(
        success=True,
        reply=result["reply"],
        mode=result["mode"],
        can_extract_task=can_extract_task
    )


@router.post("/api/chat/extract-task", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def extract_task(request: ExtractTaskRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == request.student_email).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )

    try:
        msg_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
        description = await deerflow_service.extract_task(msg_dicts, student.name)

        task = Task(student_id=student.id, description=description)
        db.add(task)
        db.commit()
        db.refresh(task)

        await feishu_service.notify_task_created(
            {"id": task.id, "description": task.description},
            {"name": student.name, "email": student.email}
        )

        logger.info(f"对话提炼任务成功: 学生 {student.name}, 任务ID {task.id}")

        return ApiResponse(
            success=True,
            message="任务已生成",
            data={
                "task": TaskResponse.model_validate(task).model_dump()
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"对话提炼任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="任务生成失败，请稍后重试"
        )


@router.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
