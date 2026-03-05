from sqlalchemy import Column, Integer, String,  DateTime, JSON
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import enum
from app.database import Base

# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
class UserRole(int, enum.Enum):
    SEEKER = 1  # 应聘者
    RECRUITER = 2  # 招聘者

# 用户
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False, comment="邮箱，登录账号")
    hashed_password = Column(String, nullable=False)
    nick_name = Column(String, comment="用户名")
    phone = Column(String, comment="手机号")
    role = Column(Integer, default=UserRole.SEEKER)
    company = Column(String, comment="公司名称", default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# 文档
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, comment="所属用户ID，users表ID")
    user_type = Column(Integer, nullable=False, comment="用户角色")
    file_name = Column(String, nullable=False, comment="文件名称")
    file_path = Column(String, nullable=False, comment="文件路径")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    file_ext = Column(String, nullable=False, comment="文件扩展名")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# AI分析
class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, comment="关联resumes表ID")
    job_id = Column(Integer, comment="关联jobs表ID")
    match_score = Column(Integer, comment="匹配分数")  # 匹配分数 (0-100)
    gaps = Column(JSON, comment="技能差距")  # 技能差距
    strengths = Column(JSON, comment="优势技能")  # 优势技能
    suggestions = Column(JSON, comment="改进建议")  # 改进建议
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# 简历
class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, comment="用户ID，users表ID")
    skills = Column(JSON, comment="技能列表")
    experience = Column(JSON, comment="经验详情")
    education = Column(JSON, comment="教育背景")
    projects = Column(JSON, comment="项目记录")
    skills_embedding = Column(Vector, comment="技能向量化结果")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# 职位状态
class JobStatus(int, enum.Enum):
    DRAFT = 1      # 草稿
    PUBLISHED = 2  # 已发布
    CLOSED = 3     # 已关闭
    ARCHIVED = 4   # 已归档

#  职位
class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, comment="招聘者ID，users表ID" )
    document_id = Column(Integer, default=0, comment="文档ID，documents表ID" )
    title = Column(String, nullable=False, comment="职位标题")
    location = Column(String, nullable=False, comment="工作地点")
    degree = Column(String, nullable=False, comment="学历")
    required_skills = Column(JSON, comment="职位要求技能列表")
    job_responsibility = Column(JSON, comment="岗位职责")
    job_requirements = Column(JSON, comment="任职要求")
    salary_min = Column(Integer, default=0, comment="最低薪资")
    salary_max = Column(Integer, default=0, comment="最高薪资")
    work_experience_min = Column(Integer, default=0, comment="最低工作年限")
    work_experience_max = Column(Integer, default=0, comment="最高工作年限")
    benefits = Column(JSON, comment="职位福利待遇")
    status = Column(Integer, default=JobStatus.PUBLISHED, comment="职位状态")
    job_vector = Column(Vector, comment="职位搜索向量（标题 + 要求技能 + 职责 + 要求）")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
