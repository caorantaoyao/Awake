from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from typing import List
import logging

from app.core.database import get_db
from app.models.models import (
    ConversationMessage,
    GradeEnum,
    GrowthEvent,
    Student,
    StudentProfile,
    Task,
    TaskStatusEnum,
)
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
    ConversationHistoryResponse,
    ExtractTaskRequest,
    GrowthEventListResponse,
    GrowthResourceListResponse,
    GrowthSummaryResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    TodayTasksResponse,
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
from app.services.growth_service import (
    PROFILE_GUIDANCE,
    encode_tags,
    normalize_tags,
    parse_tags,
    recommend_resources,
    top_topic,
)

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


def deny_student_control_access(
    current_student: Student = Depends(get_current_student)
):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="普通学生无权访问 DeerFlow 控制接口"
    )


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


def _profile_response(profile: StudentProfile = None) -> ProfileResponse:
    if not profile:
        return ProfileResponse(guidance=PROFILE_GUIDANCE)

    interest_tags = parse_tags(profile.interest_tags)
    ability_tags = parse_tags(profile.ability_tags)
    is_empty = not interest_tags and not ability_tags and not profile.summary
    return ProfileResponse(
        interest_tags=interest_tags,
        ability_tags=ability_tags,
        exploration_stage=profile.exploration_stage,
        summary=profile.summary,
        updated_at=profile.updated_at,
        is_empty=is_empty,
        guidance=PROFILE_GUIDANCE if is_empty else None,
    )


@router.get("/api/profile", response_model=ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    profile = db.query(StudentProfile).filter(
        StudentProfile.student_id == current_student.id,
    ).first()
    return _profile_response(profile)


@router.put("/api/profile", response_model=ProfileResponse)
def update_profile(
    request: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    try:
        profile = db.query(StudentProfile).filter(
            StudentProfile.student_id == current_student.id,
        ).first()
        if not profile:
            profile = StudentProfile(student_id=current_student.id)
            db.add(profile)

        interest_tags = (
            normalize_tags(request.interest_tags)
            if request.interest_tags is not None
            else parse_tags(profile.interest_tags)
        )
        ability_tags = (
            normalize_tags(request.ability_tags)
            if request.ability_tags is not None
            else parse_tags(profile.ability_tags)
        )
        profile.interest_tags = encode_tags(interest_tags)
        profile.ability_tags = encode_tags(ability_tags)
        if request.exploration_stage is not None:
            profile.exploration_stage = request.exploration_stage
        if request.summary is not None:
            profile.summary = request.summary.strip()
        profile.updated_at = datetime.now()

        db.add(GrowthEvent(
            student_id=current_student.id,
            event_type="profile_updated",
            title="成长画像已更新",
            description=profile.summary or None,
            topic_tags=profile.interest_tags,
        ))
        db.commit()
        db.refresh(profile)
        return _profile_response(profile)
    except Exception as e:
        db.rollback()
        logger.error(f"画像更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="画像更新失败，请稍后重试",
        )


@router.post("/api/tasks", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    try:
        task = Task(
            student_id=current_student.id,
            description=request.description,
            deadline=request.deadline
        )
        db.add(task)
        db.flush()
        db.add(GrowthEvent(
            student_id=current_student.id,
            task_id=task.id,
            event_type="task_created",
            title="创建微行动",
            description=task.description,
            growth_points=0,
            topic_tags=task.topic_tags,
        ))
        db.commit()
        db.refresh(task)

        await feishu_service.notify_task_created(
            {"id": task.id, "description": task.description},
            {"name": current_student.name, "email": current_student.email}
        )

        logger.info(f"任务创建成功: 学生 {current_student.name}, 任务ID {task.id}")

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
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    task = db.query(Task).filter(
        Task.id == request.task_id,
        Task.student_id == current_student.id
    ).first()
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
        db.add(GrowthEvent(
            student_id=current_student.id,
            task_id=task.id,
            event_type="task_completed",
            title="完成微行动",
            description=task.description,
            growth_points=task.growth_points,
            topic_tags=task.topic_tags,
        ))
        db.commit()
        db.refresh(task)

        await feishu_service.notify_task_complete(
            {"id": task.id, "description": task.description, "feedback": task.feedback},
            {"name": current_student.name, "email": current_student.email}
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
def get_student(
    email: str,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    student = db.query(Student).filter(
        Student.id == current_student.id,
        Student.email == email
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )
    return StudentWithTasksResponse.model_validate(student)


@router.get("/api/tasks/today", response_model=TodayTasksResponse)
def get_today_tasks(
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    tasks = db.query(Task).filter(
        Task.student_id == current_student.id,
        Task.status == TaskStatusEnum.IN_PROGRESS,
    ).all()
    tasks.sort(key=lambda task: (
        task.deadline is None,
        task.deadline or datetime.max,
        task.created_at or datetime.min,
        task.id,
    ))
    return TodayTasksResponse(
        primary_task=tasks[0] if tasks else None,
        tasks=tasks,
    )


@router.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.student_id == current_student.id
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    return TaskResponse.model_validate(task)


@router.get("/api/chat/history", response_model=ConversationHistoryResponse)
def get_chat_history(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    messages = db.query(ConversationMessage).filter(
        ConversationMessage.student_id == current_student.id,
    ).order_by(
        ConversationMessage.created_at.desc(),
        ConversationMessage.id.desc(),
    ).limit(limit).all()
    messages.reverse()
    return ConversationHistoryResponse(messages=messages)


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    msg_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
    result = await deerflow_service.chat(msg_dicts, current_student.name)

    user_turns = sum(1 for m in request.messages if m.role == "user")
    can_extract_task = user_turns >= 3

    persisted = db.query(ConversationMessage).filter(
        ConversationMessage.student_id == current_student.id,
    ).order_by(ConversationMessage.id.asc()).all()
    persisted_pairs = [(message.role, message.content) for message in persisted]
    request_pairs = [
        (message.role, message.content)
        for message in request.messages
        if message.role in {"user", "assistant"}
    ]
    if request_pairs[:len(persisted_pairs)] == persisted_pairs:
        new_pairs = request_pairs[len(persisted_pairs):]
    else:
        new_pairs = request_pairs[-1:] if request_pairs else []

    try:
        for role, content in new_pairs:
            db.add(ConversationMessage(
                student_id=current_student.id,
                role=role,
                content=content,
            ))
        if (
            (new_pairs and new_pairs[-1][0] == "user")
            or (not request_pairs and not persisted_pairs)
        ):
            db.add(ConversationMessage(
                student_id=current_student.id,
                role="assistant",
                content=result["reply"],
            ))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"对话消息保存失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="对话消息保存失败，请稍后重试",
        )

    return ChatResponse(
        success=True,
        reply=result["reply"],
        mode=result["mode"],
        can_extract_task=can_extract_task
    )


@router.post("/api/chat/extract-task", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def extract_task(
    request: ExtractTaskRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    try:
        msg_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
        task_result = await deerflow_service.extract_task(
            msg_dicts,
            current_student.name,
        )

        task = Task(
            student_id=current_student.id,
            description=task_result["description"],
            estimated_minutes=task_result["estimated_minutes"],
            growth_points=task_result["growth_points"],
            topic_tags=encode_tags(task_result["topic_tags"]),
        )
        db.add(task)
        db.flush()
        db.add(GrowthEvent(
            student_id=current_student.id,
            task_id=task.id,
            event_type="task_created",
            title="创建微行动",
            description=task.description,
            growth_points=0,
            topic_tags=task.topic_tags,
        ))
        db.commit()
        db.refresh(task)

        await feishu_service.notify_task_created(
            {"id": task.id, "description": task.description},
            {"name": current_student.name, "email": current_student.email}
        )

        logger.info(f"对话提炼任务成功: 学生 {current_student.name}, 任务ID {task.id}")

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


@router.get("/api/resources", response_model=GrowthResourceListResponse)
def get_growth_resources(
    resource_type: str = Query(None),
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    profile = db.query(StudentProfile).filter(
        StudentProfile.student_id == current_student.id,
    ).first()
    return recommend_resources(
        grade=current_student.grade.value,
        interest_tags=parse_tags(profile.interest_tags) if profile else [],
        ability_tags=parse_tags(profile.ability_tags) if profile else [],
        exploration_stage=profile.exploration_stage if profile else "探索中",
        resource_type=resource_type,
    )


@router.get("/api/growth/events", response_model=GrowthEventListResponse)
def get_growth_events(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    events = db.query(GrowthEvent).filter(
        GrowthEvent.student_id == current_student.id,
    ).order_by(
        GrowthEvent.created_at.desc(),
        GrowthEvent.id.desc(),
    ).limit(limit).all()
    return GrowthEventListResponse(events=events)


@router.get("/api/growth/summary", response_model=GrowthSummaryResponse)
def get_growth_summary(
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    days = 7
    cutoff = datetime.now() - timedelta(days=days)
    recent_tasks = db.query(Task).filter(
        Task.student_id == current_student.id,
        Task.created_at >= cutoff,
    ).all()
    completed_tasks = db.query(Task).filter(
        Task.student_id == current_student.id,
        Task.status == TaskStatusEnum.COMPLETED,
        Task.completed_at >= cutoff,
    ).all()
    return GrowthSummaryResponse(
        days=days,
        created_count=len(recent_tasks),
        completed_count=len(completed_tasks),
        growth_points=sum(task.growth_points for task in completed_tasks),
        top_interest=top_topic(task.topic_tags for task in recent_tasks),
    )


@router.get("/api/deerflow/status", response_model=DeerFlowStatusResponse)
async def get_deerflow_status(
    _: None = Depends(deny_student_control_access)
):
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
async def get_deerflow_skills(
    _: None = Depends(deny_student_control_access)
):
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
async def set_deerflow_skill_enabled(
    name: str,
    request: SkillToggleRequest,
    _: None = Depends(deny_student_control_access)
):
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
async def get_deerflow_models(
    _: None = Depends(deny_student_control_access)
):
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
