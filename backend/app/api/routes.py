import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import (
    Conversation,
    ConversationMessage,
    GradeEnum,
    GrowthEvent,
    Student,
    StudentProfile,
    Task,
    TaskStatusEnum,
)
from app.schemas.schemas import (
    ApiResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatSuggestionsResponse,
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationHistoryResponse,
    ConversationResponse,
    ConversationUpdateRequest,
    DeerFlowStatusResponse,
    ExtractTaskRequest,
    GrowthEventListResponse,
    GrowthResourceListResponse,
    GrowthSummaryResponse,
    ModelItem,
    ModelListResponse,
    OnboardingCompleteRequest,
    PreferencesResponse,
    PreferencesUpdateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    SkillItem,
    SkillListResponse,
    SkillToggleRequest,
    SkillToggleResponse,
    StreamChatRequest,
    StudentLoginRequest,
    StudentRegisterRequest,
    StudentResponse,
    StudentWithTasksResponse,
    TaskCompleteRequest,
    TaskCreateRequest,
    TaskResponse,
    TodayTasksResponse,
    UploadFileResponse,
    UploadFilesResponse,
)
from app.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.services.deerflow_service import DeerFlowUnavailable, deerflow_service
from app.services.email_service import email_service
from app.services.feishu_service import feishu_service
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


def _get_conversation_or_403(db: Session, conv_id: int, student: Student) -> Conversation:
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    if conv.student_id != student.id:
        raise HTTPException(status_code=403, detail="无权访问该会话")
    return conv


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


def _build_student_profile_context(student: Student, db: Session) -> Optional[dict]:
    profile = db.query(StudentProfile).filter(
        StudentProfile.student_id == student.id,
    ).first()
    if not profile:
        return None
    interests = parse_tags(profile.interest_tags)
    abilities = parse_tags(profile.ability_tags)
    summary = profile.summary or ""
    confusion = None
    for prefix in ("当前困惑: ", "当前困惑："):
        if prefix in summary:
            part = summary.split(prefix, 1)[1]
            confusion = part.split(";")[0].split("；")[0].strip()
            break
    ctx: dict = {}
    if interests:
        ctx["interest_tags"] = interests
    if abilities:
        ctx["ability_tags"] = abilities
    if confusion and confusion != "待明确":
        ctx["confusion"] = confusion
    if profile.exploration_stage:
        ctx["exploration_stage"] = profile.exploration_stage
    return ctx or None


def _generate_welcome_message(name: str, grade: str, interests: List[str], confusions: List[str], learning_style: Optional[str]) -> str:
    interest = interests[0] if interests else None
    confusion = confusions[0] if confusions else None
    style_hint = {
        "视觉学习": "要是有视频或图解的内容，你会吸收得更快",
        "阅读学习": "你习惯通过文字和文章来理解新东西",
        "实践学习": "你更愿意边做边学，直接上手试",
        "交流学习": "你喜欢通过和人聊天讨论来理清思路",
    }.get(learning_style or "", None)

    parts = [f"{name}，很高兴认识你 🌊"]
    if interest and interest != "待探索":
        if confusion and confusion not in ("整体困惑",):
            parts.append(f"你对{interest}感兴趣，又想搞清楚{confusion}——")
        else:
            parts.append(f"你对{interest}感兴趣——")
    elif interest == "待探索":
        parts.append("看来你还在寻找自己真正感兴趣的方向——")
    else:
        parts.append("")

    parts.append("我是小海，不会替你做决定，但会陪你从真实经历里慢慢找到线索。")

    if style_hint:
        parts.append(f"我记住了你{style_hint[1:]}，后面会用适合你的方式和你聊。")

    parts.append("最近有没有哪件小事，让你觉得有点好奇，或者有点烦心？随便聊聊就好。")
    return "".join(parts) if not parts[-2] else "\n\n".join(p for p in parts if p)


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
        welcome_message=profile.welcome_message or "",
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


@router.post("/api/onboarding/complete", response_model=ApiResponse)
def complete_onboarding(
    request: OnboardingCompleteRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    try:
        current_student.onboarding_completed = True

        profile = db.query(StudentProfile).filter(
            StudentProfile.student_id == current_student.id,
        ).first()
        if not profile:
            profile = StudentProfile(student_id=current_student.id)
            db.add(profile)

        interest_tags = normalize_tags(request.interest_tags)
        confusion_tags = normalize_tags(request.confusion_tags)
        learning_style = request.learning_style.strip() if request.learning_style else None

        all_tags = list(interest_tags) + list(confusion_tags)
        profile.interest_tags = encode_tags(all_tags)
        if learning_style:
            profile.ability_tags = encode_tags([learning_style])
        profile.exploration_stage = "兴趣探索"
        profile.summary = (
            f"兴趣方向: {', '.join(interest_tags) if interest_tags else '待探索'}; "
            f"当前困惑: {', '.join(confusion_tags) if confusion_tags else '待明确'}; "
            f"学习偏好: {learning_style or '待了解'}"
        )
        grade_str = (
            current_student.grade.value
            if hasattr(current_student.grade, 'value')
            else str(current_student.grade)
        )
        profile.welcome_message = _generate_welcome_message(
            name=current_student.name,
            grade=grade_str,
            interests=interest_tags,
            confusions=confusion_tags,
            learning_style=learning_style,
        )
        profile.updated_at = datetime.now()

        db.add(GrowthEvent(
            student_id=current_student.id,
            event_type="onboarding_completed",
            title="完成入门引导",
            description=f"开始探索 {', '.join(request.interest_tags) if request.interest_tags else '兴趣方向'}",
            topic_tags=profile.interest_tags,
        ))

        db.commit()
        db.refresh(profile)
        return ApiResponse(success=True, message="onboarding 完成", data={
            "onboarding_completed": True,
            "welcome_message": profile.welcome_message,
            "student": {
                "id": current_student.id,
                "name": current_student.name,
                "email": current_student.email,
                "grade": current_student.grade.value if hasattr(current_student.grade, 'value') else current_student.grade,
                "onboarding_completed": True,
            }
        })
    except Exception as e:
        db.rollback()
        logger.error(f"Onboarding 完成失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Onboarding 完成失败，请稍后重试",
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


# ─── Conversations (Thread-based, DeerFlow as source of truth) ───

@router.get("/api/conversations", response_model=List[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    convs = db.query(Conversation).filter(
        Conversation.student_id == current_student.id,
        Conversation.is_active.is_(True),
    ).order_by(Conversation.updated_at.desc()).all()
    return [ConversationResponse.model_validate(c) for c in convs]


@router.post("/api/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    request: ConversationCreateRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    try:
        thread_id = await deerflow_service.create_thread()
    except DeerFlowUnavailable as e:
        raise HTTPException(status_code=503, detail=e.detail)

    conv = Conversation(
        student_id=current_student.id,
        thread_id=thread_id,
        title=request.title or "新对话",
        model_name=request.model_name,
        thinking_enabled=request.thinking_enabled,
        is_plan_mode=request.is_plan_mode,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return ConversationResponse.model_validate(conv)


@router.get("/api/conversations/{conv_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    conv = _get_conversation_or_403(db, conv_id, current_student)
    try:
        messages = await deerflow_service.get_thread_messages(conv.thread_id)
    except DeerFlowUnavailable as e:
        raise HTTPException(status_code=503, detail=e.detail)

    # Build user/assistant only messages (skip system/tool for UI)
    ui_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
        if m["role"] in ("user", "assistant")
    ]
    result = ConversationResponse.model_validate(conv).model_dump()
    result["messages"] = ui_messages
    return result


@router.patch("/api/conversations/{conv_id}", response_model=ConversationResponse)
def update_conversation(
    conv_id: int,
    request: ConversationUpdateRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    conv = _get_conversation_or_403(db, conv_id, current_student)
    if request.title is not None:
        conv.title = request.title[:200]
    if request.model_name is not None:
        conv.model_name = request.model_name
    if request.thinking_enabled is not None:
        conv.thinking_enabled = request.thinking_enabled
    if request.is_plan_mode is not None:
        conv.is_plan_mode = request.is_plan_mode
    conv.updated_at = datetime.now()
    db.commit()
    db.refresh(conv)
    return ConversationResponse.model_validate(conv)


@router.delete("/api/conversations/{conv_id}", response_model=ApiResponse)
async def delete_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    conv = _get_conversation_or_403(db, conv_id, current_student)
    try:
        await deerflow_service.delete_thread(conv.thread_id)
    except DeerFlowUnavailable:
        pass
    conv.is_active = False
    db.commit()
    return ApiResponse(success=True, message="会话已删除")


# ─── SSE Streaming Chat (the primary chat path) ───

def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/api/chat/stream")
async def chat_stream(
    request: StreamChatRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    conv: Optional[Conversation] = None
    if request.conversation_id:
        conv = _get_conversation_or_403(db, request.conversation_id, current_student)
        thread_id = conv.thread_id
        model_name = request.model_name or conv.model_name
        thinking = request.thinking_enabled or conv.thinking_enabled
        plan_mode = request.is_plan_mode or conv.is_plan_mode
    else:
        try:
            thread_id = await deerflow_service.create_thread()
        except DeerFlowUnavailable as e:
            raise HTTPException(status_code=503, detail=e.detail)
        conv = Conversation(
            student_id=current_student.id,
            thread_id=thread_id,
            title=request.message[:30] + ("…" if len(request.message) > 30 else ""),
            model_name=request.model_name,
            thinking_enabled=request.thinking_enabled,
            is_plan_mode=request.is_plan_mode,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        model_name = request.model_name
        thinking = request.thinking_enabled
        plan_mode = request.is_plan_mode

    user_turns = 0
    try:
        existing_msgs = await deerflow_service.get_thread_messages(thread_id, limit=200)
        user_turns = sum(1 for m in existing_msgs if m.get("role") == "user")
    except DeerFlowUnavailable:
        pass

    messages = [{"role": "user", "content": request.message}]
    unlock_after = current_student.unlock_after_turns or 3
    chat_mode = current_student.chat_mode or "explore_first"
    student_profile_ctx = _build_student_profile_context(current_student, db)
    file_ids = request.file_ids

    async def event_generator():
        yield _sse_event("meta", {
            "conversation_id": conv.id,
            "thread_id": thread_id,
            "can_extract_task": (user_turns + 1) >= unlock_after,
        })
        full_reply_parts: List[str] = []
        error_msg: Optional[str] = None
        try:
            async for ev in deerflow_service.stream_chat(
                messages,
                student_name=current_student.name,
                thread_id=thread_id,
                unlock_after_turns=unlock_after,
                chat_mode=chat_mode,
                model_name=model_name,
                thinking_enabled=thinking,
                is_plan_mode=plan_mode,
                student_profile=student_profile_ctx,
                file_ids=file_ids,
            ):
                t = ev.get("type")
                if t == "text":
                    full_reply_parts.append(ev["content"])
                    yield _sse_event("text", {"content": ev["content"]})
                elif t == "thinking":
                    yield _sse_event("thinking", {"content": ev["content"]})
                elif t == "plan":
                    yield _sse_event("plan", {"steps": ev.get("steps", [])})
                elif t == "artifact":
                    yield _sse_event("artifact", {"artifact": ev.get("artifact")})
                elif t == "tool":
                    yield _sse_event("tool", {"name": ev.get("name", ""), "input": ev.get("input")})
                elif t == "error":
                    error_msg = ev.get("message", "对话出错")
                    yield _sse_event("error", {"message": error_msg})
                elif t == "done":
                    yield _sse_event("done", {
                        "reply": ev.get("reply", ""),
                        "thinking": ev.get("thinking", ""),
                        "artifacts": ev.get("artifacts", []),
                        "plan_steps": ev.get("plan_steps", []),
                        "can_extract_task": (user_turns + 1) >= unlock_after,
                    })
        except Exception as e:
            logger.error(f"SSE stream 异常: {e}")
            error_msg = str(e)
            yield _sse_event("error", {"message": error_msg})

        if not error_msg and full_reply_parts:
            try:
                conv.updated_at = datetime.now()
                db.commit()
            except Exception as e:
                logger.error(f"更新会话时间失败: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Legacy /api/chat (non-streaming, kept for backwards compat) ───

@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    msg_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
    student_profile_ctx = _build_student_profile_context(current_student, db)
    try:
        result = await deerflow_service.chat(
            msg_dicts,
            current_student.name,
            unlock_after_turns=current_student.unlock_after_turns,
            chat_mode=current_student.chat_mode,
            student_profile=student_profile_ctx,
        )
    except DeerFlowUnavailable as e:
        raise HTTPException(status_code=503, detail=e.detail)

    user_turns = sum(1 for m in request.messages if m.role == "user")
    can_extract_task = user_turns >= (current_student.unlock_after_turns or 3)

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


# ─── Legacy history endpoints (maintained for non-Thread UI paths) ───

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


@router.delete("/api/chat/history", response_model=ApiResponse)
def clear_chat_history(
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    db.query(ConversationMessage).filter(
        ConversationMessage.student_id == current_student.id,
    ).delete(synchronize_session=False)
    db.commit()
    return ApiResponse(success=True, message="对话历史已清空，可以开始新的对话。")


# ─── Task extraction from a specific conversation ───

@router.post("/api/chat/extract-task", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def extract_task(
    request: ExtractTaskRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    try:
        msg_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
        student_profile_ctx = _build_student_profile_context(current_student, db)
        task_result = await deerflow_service.extract_task(
            msg_dicts,
            current_student.name,
            unlock_after_turns=current_student.unlock_after_turns,
            chat_mode=current_student.chat_mode,
            student_profile=student_profile_ctx,
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
    except DeerFlowUnavailable as e:
        raise HTTPException(status_code=503, detail=e.detail)
    except Exception as e:
        db.rollback()
        logger.error(f"对话提炼任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="任务生成失败，请稍后重试"
        )


# ─── Suggestions ───

@router.post("/api/chat/suggestions", response_model=ChatSuggestionsResponse)
async def get_suggestions(
    request: ChatRequest,
    current_student: Student = Depends(get_current_student),
):
    msg_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
    suggestions = await deerflow_service.get_suggestions(msg_dicts)
    return ChatSuggestionsResponse(suggestions=suggestions)


# ─── File Upload ───

@router.post("/api/chat/upload", response_model=UploadFilesResponse)
async def upload_chat_files(
    conversation_id: int = Query(..., description="会话 ID"),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    conv = _get_conversation_or_403(db, conversation_id, current_student)
    file_tuples = []
    results = []
    for f in files:
        content = await f.read()
        file_tuples.append((f.filename or "upload.bin", content, f.content_type or "application/octet-stream"))
        results.append(UploadFileResponse(
            filename=f.filename or "upload.bin",
            size=len(content),
            mime_type=f.content_type,
        ))
    try:
        uploaded = await deerflow_service.upload_files(conv.thread_id, file_tuples)
        for i, u in enumerate(uploaded):
            if i < len(results):
                results[i].file_id = u.get("file_id") or u.get("id")
    except DeerFlowUnavailable as e:
        for r in results:
            r.error = e.detail
    return UploadFilesResponse(files=results)


# ─── Resources / Growth ───

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


# ─── DeerFlow Capabilities (open to students now) ───

@router.get("/api/deerflow/status", response_model=DeerFlowStatusResponse)
async def get_deerflow_status():
    try:
        st = await deerflow_service.get_status()
        return DeerFlowStatusResponse(
            online=st.get("online", False),
            assistant_id=deerflow_service.assistant_id,
            model=st.get("current_model"),
            error=st.get("error"),
        )
    except Exception as e:
        logger.error(f"DeerFlow status 异常: {e}")
        return DeerFlowStatusResponse(
            online=False,
            assistant_id=deerflow_service.assistant_id,
            error=str(e),
        )


@router.get("/api/deerflow/models", response_model=ModelListResponse)
async def get_deerflow_models():
    try:
        raw_models = await deerflow_service.list_models()
        models = []
        for m in raw_models:
            mid = m.get("id") or m.get("name") or ""
            if not mid:
                continue
            models.append(ModelItem(
                id=str(mid),
                name=m.get("display_name") or m.get("name") or str(mid),
                provider=m.get("provider") or m.get("vendor"),
                raw=m,
            ))
        return ModelListResponse(online=True, models=models)
    except DeerFlowUnavailable as e:
        return ModelListResponse(online=False, models=[], error=e.detail)
    except Exception as e:
        logger.error(f"DeerFlow models 异常: {e}")
        return ModelListResponse(online=False, models=[], error=str(e))


@router.get("/api/deerflow/skills", response_model=SkillListResponse)
async def get_deerflow_skills():
    try:
        raw_skills = await deerflow_service.list_skills()
        skills = []
        for s in raw_skills:
            name = s.get("name") or s.get("id") or ""
            if not name:
                continue
            skills.append(SkillItem(
                name=str(name),
                description=s.get("description") or s.get("display_name"),
                enabled=s.get("enabled", True),
                raw=s,
            ))
        return SkillListResponse(online=True, skills=skills)
    except DeerFlowUnavailable as e:
        return SkillListResponse(online=False, skills=[], error=e.detail)
    except Exception as e:
        logger.error(f"DeerFlow skills 异常: {e}")
        return SkillListResponse(online=False, skills=[], error=str(e))


@router.put("/api/deerflow/skills/{name}", response_model=SkillToggleResponse)
async def set_deerflow_skill_enabled(
    name: str,
    request: SkillToggleRequest,
    _: Student = Depends(get_current_student),
):
    try:
        await deerflow_service.set_skill_enabled(name, request.enabled)
        return SkillToggleResponse(
            online=True,
            skill=SkillItem(name=name, enabled=request.enabled),
        )
    except DeerFlowUnavailable as e:
        return SkillToggleResponse(
            online=False,
            skill=SkillItem(name=name, enabled=None),
            error=e.detail,
        )
    except Exception as e:
        logger.error(f"DeerFlow skill 开关异常: {e}")
        return SkillToggleResponse(
            online=False,
            skill=SkillItem(name=name, enabled=None),
            error=str(e),
        )


# ─── Student Preferences ───

CHAT_MODE_LABELS = {
    "explore_first": "先探索，再行动",
    "balanced": "平衡模式",
    "direct_action": "直接给建议",
}

UNLOCK_LABELS = {
    2: "快速解锁（2 轮后）",
    3: "探索 3 轮后解锁",
    4: "探索 4 轮后解锁",
    5: "深入探索（5 轮后）",
    6: "深度探索（6 轮后）",
    7: "深度探索（7 轮后）",
    8: "深度探索（8 轮后）",
}


@router.get("/api/students/me/preferences", response_model=PreferencesResponse)
def get_preferences(
    current_student: Student = Depends(get_current_student),
):
    chat_mode_val = current_student.chat_mode or "explore_first"
    unlock_val = current_student.unlock_after_turns or 3
    return PreferencesResponse(
        chat_mode=chat_mode_val,
        unlock_after_turns=unlock_val,
        chat_mode_label=CHAT_MODE_LABELS.get(chat_mode_val, "先探索，再行动"),
        unlock_label=UNLOCK_LABELS.get(unlock_val, f"探索 {unlock_val} 轮后解锁"),
    )


@router.put("/api/students/me/preferences", response_model=PreferencesResponse)
def update_preferences(
    request: PreferencesUpdateRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    if request.chat_mode is not None:
        current_student.chat_mode = request.chat_mode.value if hasattr(request.chat_mode, 'value') else request.chat_mode
    if request.unlock_after_turns is not None:
        current_student.unlock_after_turns = request.unlock_after_turns
    current_student.operation_log = datetime.utcnow()
    db.commit()
    db.refresh(current_student)

    chat_mode_val = current_student.chat_mode or "explore_first"
    unlock_val = current_student.unlock_after_turns or 3
    return PreferencesResponse(
        chat_mode=chat_mode_val,
        unlock_after_turns=unlock_val,
        chat_mode_label=CHAT_MODE_LABELS.get(chat_mode_val, "先探索，再行动"),
        unlock_label=UNLOCK_LABELS.get(unlock_val, f"探索 {unlock_val} 轮后解锁"),
    )


@router.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ─── Artifacts ───

@router.get("/api/conversations/{conv_id}/artifacts")
async def list_conversation_artifacts(
    conv_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    conv = _get_conversation_or_403(db, conv_id, current_student)
    try:
        artifacts = await deerflow_service.list_artifacts(conv.thread_id)
        return ApiResponse(success=True, data={"artifacts": artifacts})
    except DeerFlowUnavailable as e:
        raise HTTPException(status_code=503, detail=e.detail)


@router.get("/api/conversations/{conv_id}/artifacts/{artifact_path:path}")
async def get_conversation_artifact(
    conv_id: int,
    artifact_path: str,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    conv = _get_conversation_or_403(db, conv_id, current_student)
    try:
        from fastapi.responses import Response
        content, content_type = await deerflow_service.get_artifact(conv.thread_id, artifact_path)
        return Response(content=content, media_type=content_type)
    except DeerFlowUnavailable as e:
        raise HTTPException(status_code=503, detail=e.detail)


# ─── Feedback ───

class FeedbackRequest(BaseModel):
    rating: Optional[str] = Field(None, description="反馈评分: up/down")
    comment: Optional[str] = Field(None, max_length=1000, description="文字反馈")


@router.put("/api/conversations/{conv_id}/runs/{run_id}/feedback", response_model=ApiResponse)
async def submit_feedback(
    conv_id: int,
    run_id: str,
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    conv = _get_conversation_or_403(db, conv_id, current_student)
    try:
        await deerflow_service.submit_feedback(
            conv.thread_id, run_id,
            rating=request.rating,
            comment=request.comment,
        )
        return ApiResponse(success=True, message="反馈已提交")
    except DeerFlowUnavailable as e:
        raise HTTPException(status_code=503, detail=e.detail)


# ─── Input Polish ───

class InputPolishRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


@router.post("/api/input-polish", response_model=ApiResponse)
async def polish_input(
    request: InputPolishRequest,
    _: Student = Depends(get_current_student),
):
    polished = await deerflow_service.polish_input(request.text)
    return ApiResponse(success=True, data={"polished_text": polished, "original_text": request.text})


# ─── MCP Servers ───

@router.get("/api/mcp", response_model=ApiResponse)
async def list_mcp_servers(
    _: Student = Depends(get_current_student),
):
    servers = await deerflow_service.list_mcp_servers()
    return ApiResponse(success=True, data={"servers": servers})


# ─── Run History ───

@router.get("/api/runs", response_model=ApiResponse)
async def list_all_runs(
    _: Student = Depends(get_current_student),
):
    runs = await deerflow_service.list_runs()
    return ApiResponse(success=True, data={"runs": runs})


@router.get("/api/conversations/{conv_id}/runs", response_model=ApiResponse)
async def list_conversation_runs(
    conv_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    conv = _get_conversation_or_403(db, conv_id, current_student)
    runs = await deerflow_service.list_runs(conv.thread_id)
    return ApiResponse(success=True, data={"runs": runs})


# ─── Scheduled Tasks ───

@router.get("/api/scheduled-tasks", response_model=ApiResponse)
async def list_scheduled_tasks(
    _: Student = Depends(get_current_student),
):
    tasks = await deerflow_service.list_scheduled_tasks()
    return ApiResponse(success=True, data={"tasks": tasks})


class ScheduledTaskCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    prompt: str = Field(..., min_length=1)
    schedule: str = Field(..., description="Cron 表达式或间隔描述")
    enabled: bool = True


@router.post("/api/scheduled-tasks", response_model=ApiResponse)
async def create_scheduled_task(
    request: ScheduledTaskCreateRequest,
    _: Student = Depends(get_current_student),
):
    try:
        result = await deerflow_service.create_scheduled_task(request.model_dump())
        return ApiResponse(success=True, message="定时任务已创建", data=result)
    except DeerFlowUnavailable as e:
        raise HTTPException(status_code=503, detail=e.detail)
