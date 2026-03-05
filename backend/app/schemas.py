from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
from app.models import UserRole

# 泛型类型变量
T = TypeVar('T')

# --- 通用响应模型 ---
class CommonResponse(BaseModel, Generic[T]):
    code: int = 200
    msg: str = "success"
    data: Optional[T] = None

# --- 认证 ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nick_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.SEEKER

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    field: str
    value: str

class UserPWDUpdate(BaseModel):
    new_password1: str
    new_password2: str

class Token(BaseModel):
    access_token: str
    expires_in: int
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: str
    nick_name: str
    role: UserRole
    phone: Optional[str] = None
    class Config:
        from_attributes = True

# --- 文档 ---
class DocumentUpload(BaseModel):
    user_type: UserRole

class DocumentResponse(BaseModel):
    id: int
    user_type: int
    created_at: datetime
    file_name: str
    file_path: str
    file_ext: str
    file_size: int
    class Config:
        from_attributes = True

# --- AI 分析 ---
class AnalysisResponse(BaseModel):
    skills: List[str]
    experience: Dict[str, Any]
    education: Dict[str, Any]
    match_score: Optional[int] = None
    gaps: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None


# --- 职位相关枚举 ---
from enum import IntEnum

class JobStatusEnum(IntEnum):
    DRAFT = 1
    PUBLISHED = 2
    CLOSED = 3
    ARCHIVED = 4

class EmploymentTypeEnum(IntEnum):
    FULL_TIME = 1
    PART_TIME = 2
    CONTRACT = 3
    INTERNSHIP = 4
    FREELANCE = 5

class ExperienceLevelEnum(IntEnum):
    ENTRY = 1
    MID = 2
    SENIOR = 3
    EXECUTIVE = 4


# --- 职位管理 ---
class JobCreate(BaseModel):
    title: str
    company: str
    location: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    employment_type: EmploymentTypeEnum = EmploymentTypeEnum.FULL_TIME
    experience_level: ExperienceLevelEnum = ExperienceLevelEnum.MID
    description: str
    requirements: List[str] = []
    benefits: List[str] = []
    is_remote: bool = False

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    employment_type: Optional[EmploymentTypeEnum] = None
    experience_level: Optional[ExperienceLevelEnum] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    is_remote: Optional[bool] = None
    status: Optional[JobStatusEnum] = None

class JobResponse(BaseModel):
    id: int
    title: str
    location: str
    degree: str
    required_skills: List[str]
    job_responsibility: List[str]
    job_requirements: List[str]
    salary_min: int = 0
    salary_max: int = 0
    work_experience_min: int = 0
    work_experience_max: int = 0
    benefits: List[str]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobListResponse(BaseModel):
    id: int
    title: str
    location: str
    degree: str
    required_skills: Optional[List[str]] = []
    salary_min: Optional[int] = 0
    salary_max: Optional[int] = 0
    work_experience_min: Optional[int] = 0
    work_experience_max: Optional[int] = 0
    created_at: datetime

    class Config:
        from_attributes = True

class PaginatedJobResponse(BaseModel):
    total: int
    list: List[JobListResponse]


# 简历
class ResumeResponse(BaseModel):
    id: int
    user_id: int
    skills: Optional[list[str]] = []
    experience: Optional[list[dict]] = []
    education: Optional[list[dict]] = []
    projects: Optional[list[dict]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 技能分布分析响应
class SkillDistributionResponse(BaseModel):
    skill_categories: dict
    skill_summary: dict
    skill_gaps: list[str]
    recommended_focus: list[str]

# 职业发展路线图响应
class CareerRoadmapResponse(BaseModel):
    current_level: str
    timeline: list[dict]
    career_paths: list[dict]
    certifications: list[str]
    networking_advice: list[str]

# 综合职业发展建议响应
class CareerDevelopmentResponse(BaseModel):
    skill_distribution: SkillDistributionResponse
    career_roadmap: CareerRoadmapResponse


class ChatHistory(BaseModel):
    content: str
    role: str

class ChatData(BaseModel):
    isStream: Optional[bool] = True
    query: str
    imgBase64: Optional[str] = None
    history: Optional[list[ChatHistory]] = []