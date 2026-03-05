from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Resume
from app.schemas import (
    CommonResponse, ResumeResponse,
    SkillDistributionResponse,
    CareerRoadmapResponse,
    CareerDevelopmentResponse
)
from app.routers.auth import get_current_user
from app.services.ai_service import AIService

router = APIRouter(prefix="/resumes", tags=["简历管理"])

# 获取简历详情
@router.get("", response_model=CommonResponse)
async def get_resume(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if isinstance(current_user, CommonResponse):
        return current_user

    result = db.execute(
        select(Resume).where(Resume.user_id == current_user.id)
        .order_by(Resume.id.desc()).limit(1)
    )

    resume = result.scalar_one_or_none()

    if resume is None:
        return CommonResponse(code=404, msg="简历不存在，请上传简历")

    return CommonResponse[ResumeResponse](data=resume)


# 生成技能分布图
@router.get("/analysis/skill-distribution", response_model=CommonResponse)
async def analyze_skill_distribution(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    分析简历技能分布：按类别分组并评估掌握程度
    """
    if isinstance(current_user, CommonResponse):
        return current_user

    # 获取用户简历
    result = db.execute(
        select(Resume).where(Resume.user_id == current_user.id)
        .order_by(Resume.id.desc()).limit(1)
    )

    resume = result.scalar_one_or_none()

    if not resume:
        return CommonResponse(code=404, msg="请先上传简历")

    # 调用 AI 服务分析技能分布
    try:
        skill_distribution = AIService.analyze_skill_distribution(resume)

        return CommonResponse[SkillDistributionResponse](
            code=200,
            msg="技能分布分析成功",
            data=skill_distribution
        )
    except Exception as e:
        return CommonResponse(code=500, msg=f"分析失败：{str(e)}")


# 生成职业发展路线图
@router.get("/analysis/career-roadmap", response_model=CommonResponse)
async def generate_career_roadmap(
        target_role: Optional[str] = Query(None, description="目标职位，如'高级后端工程师'、'技术架构师'"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    生成职业发展路线图：包含短期、中期、长期目标
    """
    if isinstance(current_user, CommonResponse):
        return current_user

    # 获取用户简历
    result = db.execute(
        select(Resume).where(Resume.user_id == current_user.id)
        .order_by(Resume.id.desc()).limit(1)
    )

    resume = result.scalar_one_or_none()

    if not resume:
        return CommonResponse(code=404, msg="请先上传简历")

    # 调用 AI 服务生成路线图
    try:
        roadmap = AIService.generate_development_roadmap(resume, target_role)

        return CommonResponse[CareerRoadmapResponse](
            code=200,
            msg="职业发展路线图生成成功",
            data=roadmap
        )
    except Exception as e:
        return CommonResponse(code=500, msg=f"生成失败：{str(e)}")


# 获取完整的职业发展建议（技能分布 + 路线图）
@router.get("/analysis/career-development", response_model=CommonResponse)
async def get_career_development_analysis(
        target_role: Optional[str] = Query(None, description="目标职位，如'高级后端工程师'、'技术架构师'"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取完整的职业发展分析：包含技能分布和职业发展路线图
    """
    if isinstance(current_user, CommonResponse):
        return current_user

    # 获取用户简历
    result = db.execute(
        select(Resume).where(Resume.user_id == current_user.id)
        .order_by(Resume.id.desc()).limit(1)
    )

    resume = result.scalar_one_or_none()

    if not resume:
        return CommonResponse(code=404, msg="请先上传简历")

    # 调用 AI 服务进行分析
    try:
        skill_distribution = AIService.analyze_skill_distribution(resume)
        roadmap = AIService.generate_development_roadmap(resume, target_role)

        return CommonResponse[CareerDevelopmentResponse](
            code=200,
            msg="职业发展分析完成",
            data={
                "skill_distribution": skill_distribution,
                "career_roadmap": roadmap
            }
        )
    except Exception as e:
        return CommonResponse(code=500, msg=f"分析失败：{str(e)}")