from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import List
import logging

from app.core.database import get_db
from app.models.models import Student, Task, TaskStatusEnum, GradeEnum
from app.schemas.schemas import (
    StudentRegisterRequest,
    StudentLoginRequest,
    StudentResponse,
    TaskCreateRequest,
    TaskCompleteRequest,
    TaskResponse,
    StudentWithTasksResponse,
    ApiResponse,
    ChatRequest,
    ChatResponse,
    ExtractTaskRequest,
    DeerFlowStatusResponse,
    SkillListResponse,
    SkillItem,
    SkillToggleRequest,
    SkillToggleResponse,
    ModelListResponse,
)
from app.services.auth_service import create_access_token, decode_access_token, hash_password, verify_password
from app.services.email_service import email_service
from app.services.feishu_service import feishu_service
from app.services.deerflow_service import deerflow_service
from app.services.deerflow_control import deerflow_control_service

logger = logging.getLogger(__name__)

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已失效"
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已失效"
        )

    student_id = payload.get("student_id")
    student = db.query(Student).filter(Student.id == student_id).first() if student_id else None
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已失效"
        )

    return student


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
            grade=GradeEnum(request.grade.value),
            password_hash=hash_password(request.password)
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


@router.post("/api/login", response_model=ApiResponse)
def login_student(
    request: StudentLoginRequest,
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.email == request.email).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该邮箱尚未注册，请先完成注册"
        )
    if not student.password_hash or not verify_password(request.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误，请重新输入"
        )

    access_token = create_access_token(student.id, student.email)
    logger.info(f"用户登录成功: {student.name} ({student.email})")

    return ApiResponse(
        success=True,
        message="登录成功",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "student": StudentResponse.model_validate(student).model_dump()
        }
    )


@router.get("/api/auth/me", response_model=StudentResponse)
def get_me(current_student: Student = Depends(get_current_student)):
    return current_student


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


@router.get("/api/deerflow/status", response_model=DeerFlowStatusResponse)
async def get_deerflow_status():
    try:
        return await deerflow_control_service.get_status()
    except Exception as e:
        logger.error(f"DeerFlow status 代理异常: {e}")
        return DeerFlowStatusResponse(
            online=False,
            assistant_id=deerflow_control_service.assistant_id,
            model=None,
            error="DeerFlow 控制代理异常"
        )


@router.get("/api/deerflow/skills", response_model=SkillListResponse)
async def get_deerflow_skills():
    try:
        return await deerflow_control_service.list_skills()
    except Exception as e:
        logger.error(f"DeerFlow skills 代理异常: {e}")
        return SkillListResponse(
            online=False,
            skills=[],
            error="DeerFlow 控制代理异常"
        )


@router.put("/api/deerflow/skills/{name}", response_model=SkillToggleResponse)
async def set_deerflow_skill_enabled(name: str, request: SkillToggleRequest):
    try:
        return await deerflow_control_service.set_skill_enabled(name, request.enabled)
    except Exception as e:
        logger.error(f"DeerFlow skill 开关代理异常: {e}")
        return SkillToggleResponse(
            online=False,
            skill=SkillItem(name=name, enabled=None),
            error="DeerFlow 控制代理异常"
        )


@router.get("/api/deerflow/models", response_model=ModelListResponse)
async def get_deerflow_models():
    try:
        return await deerflow_control_service.list_models()
    except Exception as e:
        logger.error(f"DeerFlow models 代理异常: {e}")
        return ModelListResponse(
            online=False,
            models=[],
            error="DeerFlow 控制代理异常"
        )


@router.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
