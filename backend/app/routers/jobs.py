from fastapi import APIRouter, Depends
from sqlalchemy import select, and_, or_, func, String
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Job, UserRole, JobStatus
from app.schemas import (
    JobUpdate, JobResponse,
    CommonResponse, PaginatedJobResponse
)
from app.routers.auth import get_current_user
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/jobs", tags=["职位管理"])

@router.put("/{job_id}", response_model=CommonResponse[JobResponse])
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新职位信息"""
    # 检查是否为错误响应
    if isinstance(current_user, CommonResponse):
        return current_user

    # 只有招聘者可以更新职位
    if current_user.role != UserRole.RECRUITER:
        return CommonResponse[JobResponse](
            code=403,
            msg="权限不足",
            data=None
        )

    # 查找职位
    result = db.execute(
        select(Job).where(
            and_(Job.id == job_id, Job.user_id == current_user.id)
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        return CommonResponse[JobResponse](
            code=404,
            msg="职位不存在或无权修改",
            data=None
        )

    # 更新字段
    update_data = job_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    return CommonResponse[JobResponse](
        code=200,
        msg="职位更新成功",
        data=job
    )

@router.put("/{job_id}/status/{status}", response_model=CommonResponse[JobResponse])
async def update_job_status(
    job_id: int,
    status: JobStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新职位状态（发布/关闭/存档）"""
    # 检查是否为错误响应
    if isinstance(current_user, CommonResponse):
        return current_user

    # 只有招聘者可以更新职位状态
    if current_user.role != UserRole.RECRUITER:
        return CommonResponse[JobResponse](
            code=403,
            msg="权限不足",
            data=None
        )

    # 查找职位
    result = db.execute(
        select(Job).where(
            and_(Job.id == job_id, Job.user_id == current_user.id)
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        return CommonResponse[JobResponse](
            code=404,
            msg="职位不存在或无权修改",
            data=None
        )

    # 更新状态
    job.status = status
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    status_msg = {
        JobStatus.DRAFT: "已设为草稿",
        JobStatus.PUBLISHED: "已发布",
        JobStatus.CLOSED: "已关闭",
        JobStatus.ARCHIVED: "已归档"
    }

    return CommonResponse[JobResponse](
        code=200,
        msg=f"职位{status_msg.get(status, '状态')}成功",
        data=job
    )

@router.delete("/{job_id}", response_model=CommonResponse[dict])
async def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除职位"""
    # 检查是否为错误响应
    if isinstance(current_user, CommonResponse):
        return current_user

    # 只有招聘者可以删除职位
    if current_user.role != UserRole.RECRUITER:
        return CommonResponse[dict](
            code=403,
            msg="权限不足",
            data={}
        )

    # 查找职位
    result = db.execute(
        select(Job).where(
            and_(Job.id == job_id, Job.user_id == current_user.id)
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        return CommonResponse[dict](
            code=404,
            msg="职位不存在或无权删除",
            data={}
        )

    # 删除职位（会级联删除相关申请）
    db.delete(job)
    db.commit()

    return CommonResponse[dict](
        code=200,
        msg="职位删除成功",
        data={"message": "Job deleted successfully"}
    )

@router.get("", response_model=CommonResponse[PaginatedJobResponse])
async def search_jobs(
    keyword: Optional[str] = None,
    location: Optional[str] = None,
    min_salary: Optional[int] = None,
    max_salary: Optional[int] = None,
    page: Optional[int] = 1,
    num: Optional[int] = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """搜索职位（所有用户可用）"""
    # 检查是否为错误响应
    if isinstance(current_user, CommonResponse):
        return current_user

    keyword_embedding = None
    if current_user.role == UserRole.RECRUITER:
        query = select(Job).where(Job.user_id == current_user.id)
    else:
        query = select(Job)

        # 添加搜索条件
        if keyword:
            from app.services.ai_service import AIService

            # 获取关键词的向量
            keyword_embedding = AIService._get_embedding(keyword)

            if keyword_embedding:
                # 同时使用向量相似度和关键字匹配
                query = query.where(Job.job_vector.cosine_distance(keyword_embedding) < 0.7)
            else:
                # 回退到纯关键字搜索
                query = query.where(
                    or_(
                        Job.title.contains(keyword),
                        Job.required_skills.cast(String).contains(keyword),
                        Job.job_responsibility.cast(String).contains(keyword),
                        Job.job_requirements.cast(String).contains(keyword)
                    )
                )

    if location:
        query = query.where(Job.location.contains(location))

    if min_salary:
        query = query.where(Job.salary_max >= min_salary)

    if max_salary:
        query = query.where(Job.salary_min <= max_salary)


    # 获取总数
    total_query = select(func.count()).select_from(query.subquery())
    total = db.execute(total_query).scalar()

    if keyword_embedding:
        query = query.order_by(
            Job.job_vector.cosine_distance(keyword_embedding)
        ).limit(num).offset((page - 1) * num)
    else:
        query = query.order_by(Job.id.desc()).limit(num).offset((page - 1) * num)

    result = db.execute(query)
    jobs = result.scalars().all()

    return CommonResponse[PaginatedJobResponse](
        code=200,
        msg="获取职位列表成功",
        data={
            "total": total,
            "list": jobs
        }
    )

# 获取职位详情
@router.get("/{job_id}", response_model=CommonResponse[JobResponse])
async def get_job_detail(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取职位详情"""
    # 检查是否为错误响应
    if isinstance(current_user, CommonResponse):
        return current_user

    # 查询职位详情
    result = db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        return CommonResponse[JobResponse](
            code=404,
            msg="职位不存在",
            data=None
        )

    return CommonResponse[JobResponse](
        data=job
    )
