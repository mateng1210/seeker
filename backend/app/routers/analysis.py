import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, AIAnalysis, User, UserRole, Job, Resume
from app.schemas import CommonResponse, ChatData, ChatHistory
from app.services.ai_service import ai_service
from app.routers.auth import get_current_user
import json

router = APIRouter(prefix="/ai", tags=["AI"])

log = logging.getLogger(__name__)

# 职位匹配分析
@router.get("/match", response_model=CommonResponse[dict], name="职位匹配分析")
def match_resume_job(
    job_id: int,    # 职位ID
    is_refresh: Optional[int] = 0, #是否重新分析
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 检查是否为错误响应
    if isinstance(current_user, CommonResponse):
        return current_user

    # 查询简历信息
    resume_result = db.execute(
        select(Resume).where(Resume.user_id == current_user.id)
        .order_by(Resume.id.desc()).limit(1)
    )
    resume = resume_result.scalar_one_or_none()

    if not resume:
        return CommonResponse[dict](
            code=404,
            msg="请上传简历"
        )

    resume_id = resume.id

    # 查询职位信息
    job_result = db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = job_result.scalar_one_or_none()

    if not job:
        return CommonResponse[dict](
            code=404,
            msg="职位不存在"
        )

    # 获取已有的分析结果或进行分析
    analysis_result = db.execute(
        select(AIAnalysis).where(AIAnalysis.resume_id == resume_id)
        .where(AIAnalysis.job_id == job_id)
    )

    resume_analysis = analysis_result.scalar_one_or_none()

    # 如果没有分析结果，先进行分析
    if not resume_analysis or is_refresh:
        analysis_result = ai_service.match_resume_vs_job(resume, job)

        if resume_analysis:
            resume_analysis.match_score = analysis_result.get("match_score", 0)
            resume_analysis.gaps = analysis_result.get("gaps", [])
            resume_analysis.strengths = analysis_result.get("strengths", [])
            resume_analysis.suggestions = analysis_result.get("suggestions", [])

            db.add(resume_analysis)
        else:
            resume_analysis = AIAnalysis(
                resume_id=resume_id,
                job_id=job_id,
                match_score=analysis_result.get("match_score", 0),
                gaps=analysis_result.get("gaps", []),
                strengths=analysis_result.get("strengths", []),
                suggestions=analysis_result.get("suggestions", [])
            )
            db.add(resume_analysis)

        db.commit()
        db.refresh(resume_analysis)

    return CommonResponse[dict](
        data={
            "match_score": resume_analysis.match_score,
            "gaps": resume_analysis.gaps,
            "strengths": resume_analysis.strengths,
            "suggestions": resume_analysis.suggestions
        }
    )


@router.post("/chat", name="AI Chat (SSE)")
async def chat_with_ai(
    chat_data: ChatData,
    current_user: User = Depends(get_current_user)
):
    """
    AI Chat - SSE 流式对话
    使用 Server-Sent Events 模式实时返回 AI 响应
    """
    # 检查是否为错误响应
    if isinstance(current_user, CommonResponse):
        raise HTTPException(status_code=401, detail="请登录")

    async def generate_response():
        # 系统提示词（设定 AI 角色）
        system_prompt = """你是一个智能助手，请用友好、专业的语气回答用户的问题。"""

        # # 构建对话消息
        messages = []
        # 先添加历史消息
        if chat_data.history:
            for msg in chat_data.history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": chat_data.query
        })

        # 使用流式 API 获取响应
        async for text in ai_service._chat_with_ai_stream(messages, system_prompt):
            # SSE 格式：data: {"content": "..."}\n\n

            response_data = json.dumps({"code": 0, "result": text, "is_end": False}, ensure_ascii=False)
            yield f"{response_data}\n\n"

            # 发送结束标记
        end_data = json.dumps({"code": 0, "result": "", "is_end": True}, ensure_ascii=False)
        yield f"{end_data}\n\n"

    # 返回 SSE 流
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Nginx 禁用缓冲
        }
    )
