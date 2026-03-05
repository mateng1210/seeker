from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import selectinload, Session
from app.database import get_db
from app.models import User, Document, UserRole, Resume, Job
from app.schemas import DocumentResponse, CommonResponse, JobResponse, ResumeResponse
from app.routers.auth import get_current_user  # 导入认证函数
import os
from datetime import datetime
from typing import List

from app.services.ai_service import AIService

router = APIRouter(prefix="/documents", tags=["文档管理"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=CommonResponse[JobResponse] | CommonResponse[ResumeResponse], name="上传文档")
async def upload_document(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),  # 启用认证
    ):

    # 检查是否为错误响应
    if isinstance(current_user, CommonResponse):
        return current_user

    # 验证文件格式（只允许Word和PDF）
    allowed_types = {
        'application/pdf',  # PDF文件
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/msword'  # .doc
    }

    file_extension = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = {'.pdf', '.doc', '.docx'}

    if file.content_type not in allowed_types or file_extension not in allowed_extensions:
        return CommonResponse[DocumentResponse](
            code=400,
            msg=f"只支持上传Word(.doc/.docx)和PDF文件，当前文件类型: {file.content_type}，扩展名: {file_extension}",
            data=None
        )

    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # 异步保存文件并获取文件大小
    content = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    file_size = len(content)

    # 创建文档记录（包含所有新增字段）
    document = Document(
        user_id=current_user.id,
        user_type=current_user.role,
        file_name=file.filename,
        file_path=file_path,
        file_size=file_size,
        file_ext=file_extension
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    response_data = DocumentResponse(
        id=document.id,
        user_type=document.user_type,
        file_name=file.filename,
        file_path=file_path,
        file_size=file_size,
        file_ext=file_extension,
        created_at=document.created_at
    )

    # 启用后台任务处理文档解析
    # background_tasks.add_task(AIService.parse_document, document.id, db)

    AIService.parse_document(document.id, db)

    if current_user.role == UserRole.SEEKER:
        # 获取当前用户的简历
        result = db.execute(
            select(Resume).where(Resume.user_id == current_user.id)
            .order_by(Resume.id.desc()).limit(1)
        )

        resume = result.scalar_one_or_none()

        return CommonResponse[ResumeResponse](data=resume)

    else:
        # 获取当前用户的职位
        result = db.execute(
            select(Job).where(Job.document_id == document.id)
            .order_by(Job.id.desc()).limit(1)
        )

        job = result.scalar_one_or_none()

        return CommonResponse[JobResponse](data=job)


@router.get("/", response_model=CommonResponse[List[DocumentResponse]], name="列出所有文档")
async def list_documents(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有文档"""
    # 检查是否为错误响应
    if isinstance(current_user, CommonResponse):
        return current_user

    # 使用 selectinload 预加载关系属性，避免在列表推导式中访问关系导致的问题
    result = db.execute(
        select(Document)
        .options(selectinload(Document.analysis))  # 预加载分析关系
        .where(Document.user_id == current_user.id)
        .where(Document.user_type == current_user.role)
    )
    documents = result.scalars().all()

    document_list = []
    for doc in documents:
        # 在循环中安全地访问关系属性
        has_analysis = doc.analysis is not None if hasattr(doc, 'analysis') else False
        document_list.append(
            DocumentResponse(
                id=doc.id,
                user_type=doc.user_type,
                created_at=doc.created_at,
                has_analysis=has_analysis
            )
        )

    return CommonResponse[List[DocumentResponse]](
        data=document_list
    )


@router.get("/{document_id}", response_model=CommonResponse[DocumentResponse], name="获取文档详情")
async def get_document(
        document_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """获取特定文档"""
    # 检查是否为错误响应
    if isinstance(current_user, CommonResponse):
        return current_user

    # 预加载分析关系
    result = db.execute(
        select(Document)
        .options(selectinload(Document.analysis))
        .where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        return CommonResponse[DocumentResponse](
            code=404,
            msg="文档不存在",
            data=None
        )

    # 安全地检查分析是否存在
    has_analysis = document.analysis is not None if hasattr(document, 'analysis') else False

    response_data = DocumentResponse(
        id=document.id,
        user_type=document.user_type,
        created_at=document.created_at,
        has_analysis=has_analysis
    )

    return CommonResponse[DocumentResponse](
        code=200,
        msg="获取文档成功",
        data=response_data
    )

