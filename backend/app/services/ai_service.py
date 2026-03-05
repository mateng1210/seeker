import json
import logging
import httpx
from typing import Dict, Any, Coroutine, Optional

import PyPDF2
from docx import Document as DocxDocument
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document, UserRole, Resume, Job
from app.config import settings

log = logging.getLogger(__name__)

class AIService:
    @staticmethod
    def parse_document(document_id: int, db: Session) -> int | None:
        log.info( f"开始解析文档 {document_id}")

        # 查询documents表，获取文件路径，读取文件内容
        result = db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            return None

        file_path = document.file_path
        content = ""

        try:
            # 根据文件类型处理不同格式
            if file_path.lower().endswith('.pdf'):
                # 处理PDF文件
                content = AIService._extract_pdf_content(file_path)
            elif file_path.lower().endswith(('.docx', '.doc')):
                # 处理Word文档
                content = AIService._extract_word_content(file_path)
            else:
                # 处理文本文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 最后尝试二进制模式读取
                with open(file_path, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore')

        # 解析简历或职位
        if document.user_type == UserRole.SEEKER:
            # 解析简历
            parsed_data = AIService._parse_resume_with_ai(content)

            resume = Resume(
                user_id=document.user_id,
                skills=parsed_data.get("skills", []),
                experience=parsed_data.get("experience", {}),
                education=parsed_data.get("education", {}),
                projects=parsed_data.get("projects", [])
            )

            if resume.skills:
                resume.skills_embedding = AIService._get_embedding(resume.skills)

            db.add(resume)
            db.commit()

            return resume.id
        else:
            # 解析职位
            parsed_data = AIService._parse_job_description_with_ai(content)

            job = Job(
                user_id=document.user_id,
                document_id=document.id,
                title=parsed_data.get("title", ""),
                location=parsed_data.get("location", ""),
                degree=parsed_data.get("degree", ""),
                required_skills=parsed_data.get("required_skills", []),
                job_responsibility=parsed_data.get("job_responsibility", []),
                job_requirements=parsed_data.get("job_requirements", []),
                benefits=parsed_data.get("benefits", []),
                salary_min=parsed_data.get("salary_min", 0),
                salary_max=parsed_data.get("salary_max", 0),
                work_experience_min=parsed_data.get("work_experience_min", 0),
                work_experience_max=parsed_data.get("work_experience_max", 0),
            )

            # 职位搜索向量（标题 + 要求技能 + 职责 + 要求）
            vector_text = f"{job.title} {' '.join(job.required_skills or [])} {' '.join(job.job_responsibility or [])} {' '.join(job.job_requirements or [])}"
            job.job_vector = AIService._get_embedding(vector_text)

            db.add(job)
            db.commit()

            return job.id

    # 解析简历
    @staticmethod
    def _parse_resume_with_ai(content: str) -> Dict[str, Any]:
        """使用AI解析简历内容"""
        prompt = f"""
        请分析以下简历内容，按要求提取以下信息并以JSON格式返回：

        简历内容：
        {content}

        请提取并返回以下结构的JSON数据：
        {{
            "skills": ["技能1", "技能2", "技能3"],
            "experience": [{{"years": 3, "role": "职位", "company": "公司名称", "job_responsibilities": "工作描述或工作内容"}}],
            "education": [{{"degree": "学历", "major": "专业", "school": "学校", "graduation_year": "毕业年份"}}],
            "projects": [{{"name": "项目名称", "description": "项目描述或项目简介"}}]
        }}

        要求：
        1. 技能总结成列表，技能列表必须是简历中真实存在
        2. 经验信息包括工作年限、职位、公司名称和工作描述或工作内容
        3. 教育背景包括学历、专业、学校和毕业时间
        4. 项目信息包括项目名称、项目描述或项目简介
        5. 只返回有效的JSON格式，不要包含其他文字
        6. 提取的内容语言与简历中一致
        """

        response = AIService._call_siliconflow_api(prompt)

        log.info(f"简历解析结果 {response}")

        try:
            parsed_data = json.loads(response)

            return parsed_data
        except json.JSONDecodeError:
            # 如果AI返回的不是有效JSON，使用默认结构
            return {
                "skills": [],
                "experience": [{"years": 0, "role": "", "company": "", "job_responsibilities": "工作描述或工作内容"}],
                "education": [{"degree": "", "major": "", "school": "", "graduation_year": ""}],
                "projects": [{"name": "", "description": ""}]
            }

    # 解析职位描述
    @staticmethod
    def _parse_job_description_with_ai(content: str) -> Dict[str, Any]:
        """使用AI解析职位描述内容"""
        prompt = f"""
        请分析以下职位描述内容，按要求提取关键信息并以JSON格式返回：

        职位描述：
        {content}

        请提取并返回以下结构的JSON数据：
        {{
            "title": "职位名称",
            "location": "工作地点",        
            "degree": "学历",
            "required_skills": ["技能1", "技能2"],
            "job_responsibility": ["职责1", "职责2"],
            "job_requirements": ["要求1", "要求2"],
            "benefits": ["福利1", "福利2"],
            "salary_min": 1000,
            "salary_max": 5000,
            "work_experience_min": 0,
            "work_experience_max": 5
        }}

        要求：
        1. 职位名称
        2. 工作地点
        3. 学历
        4. 工作技能
        5. 岗位职责
        6. 任职要求
        7. 包含福利待遇信息
        8. 最低薪资和最高薪资
        9. 提取最低和最高工作经验年限
        10. 只返回有效的JSON格式，不要包含其他文字
        """

        response = AIService._call_siliconflow_api(prompt)

        try:
            parsed_data = json.loads(response)
            return parsed_data
        except json.JSONDecodeError:
            # 如果AI返回的不是有效JSON，使用默认结构
            return {
                "title": "职位名称",
                "location": "工作地点",
                "degree": "学历",
                "required_skills": [],
                "job_responsibility": [],
                "job_requirements": [],
                "benefits": [],
                "salary_min": 0,
                "salary_max": 0,
                "work_experience_min": 0,
                "work_experience_max": 0
            }

    @staticmethod
    def _call_siliconflow_api(prompt: str, stream: bool = False) -> str:
        """调用SiliconFlow API"""
        url = f"{settings.SILICONFLOW_API_URL}/v1/messages"

        headers = {
            "Authorization": f"Bearer {settings.SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": settings.CHAT_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": stream,
            "response_format": {
                "type": "json"
            }
        }

        try:
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=payload, timeout=60.0)
                response.raise_for_status()

                result = response.json()

                log.info(f"_call_siliconflow_api API响应结果 {result}")

                tmp = result['content'][0]['text']

                # 先删除字符串首尾的 ``` 再删除前面的 json
                tmp = tmp.strip('`')
                # 删除前面的 json
                if tmp.startswith('json'):
                    tmp = tmp[4:]

                return tmp

        except Exception as e:
            print(f"_call_siliconflow_api API调用错误: {e}")
            # 返回默认响应
            return '''{
                "skills": [], 
                "experience": [{"years": 0, "role": "", "company": "", "project": ""}], 
                "education": [{"degree": "", "major": "", "school": "", "graduation_year": ""}]
            }'''


    # 获取嵌入向量
    def _get_embedding(input_data: any) -> list:
        """调用SiliconFlow API"""
        url = f"{settings.SILICONFLOW_API_URL}/v1/embeddings"

        headers = {
            "Authorization": f"Bearer {settings.SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        }

        # 处理不同类型的输入
        if isinstance(input_data, list):
            # 如果是列表，转换为字符串
            input_text = ", ".join(input_data)
        elif isinstance(input_data, str):
            input_text = input_data
        else:
            input_text = str(input_data)


        payload = {
            "model": settings.EMBEDDING_MODEL,
            "input": input_text
        }

        try:
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=payload, timeout=60.0)
                response.raise_for_status()

                result = response.json()

                log.info(f"_get_embedding API响应结果 {result}")
                return result['data'][0]['embedding']

        except Exception as e:
            print(f"_get_embedding API调用错误: {e}")
            # 返回默认响应
            return []



    @staticmethod
    def match_resume_vs_job(resume_data: Resume, job_data: Job):
        """
        技能匹配引擎
        """
        # 构建匹配提示词
        prompt = f"""
        你是一个专业的简历与职位匹配分析助手，请分析以下简历和职位要求的匹配度：

        简历技能: {resume_data.skills}
        简历经验: {resume_data.experience}
        简历教育: {resume_data.education}

        职位要求技能: {job_data.required_skills}
        职位岗位职责: {job_data.job_responsibility}
        职位任职要求: {job_data.job_requirements}
        职位经验要求: {job_data.work_experience_min} - {job_data.work_experience_max}年
        职位学历要求: {job_data.degree}

        请返回以下JSON格式的分析结果：
        {{
            "match_score": 85,
            "gaps": ["缺失的技能1", "缺失的技能2"],
            "strengths": ["匹配的技能1", "匹配的技能2"],
            "suggestions": ["改进建议1", "改进建议2"]
        }}

        匹配分数范围0-100，80以上为高度匹配。
        
        要求：
        1. match_score评分
        2. gaps缺失的技能列表
        3. strengths匹配的技能列表
        4. suggestions改进建议列表
        5. 只返回有效的JSON格式，不要包含其他文字
        """

        response = AIService._call_siliconflow_api(prompt)

        try:
            match_result = json.loads(response)
            return match_result
        except json.JSONDecodeError:
            # 模拟匹配逻辑

            return {
                "match_score": 0,
                "gaps": [],
                "strengths": [],
                "suggestions": []
            }

    @staticmethod
    def _extract_pdf_content(file_path: str) -> str:
        """提取PDF文件内容"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            print(f"PDF处理错误: {e}")
            return ""

    @staticmethod
    def _extract_word_content(file_path: str) -> str:
        """提取Word文档内容"""
        try:
            doc = DocxDocument(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Word文档处理错误: {e}")
            return ""



    # 根据简历，生成技能分布图，职业发展路线图
    @staticmethod
    def generate_career_advice(skills: list):
        """
        AI 职业助手：生成路线图
        """
        prompt = f"""
            基于以下技能列表，请为求职者提供职业发展建议：
    
            技能列表：{skills}
    
            请返回以下 JSON 格式的建议：
            {{
                "roadmap": ["学习阶段 1", "学习阶段 2", "学习阶段 3"],
                "learning_resources": ["资源 1", "资源 2", "资源 3"],
                "career_paths": ["发展方向 1", "发展方向 2"]
            }}
            """

        response = AIService._call_siliconflow_api(prompt)

        try:
            advice = json.loads(response)
            return advice
        except json.JSONDecodeError:
            return {
                "roadmap": ["进阶 Python 异步编程", "学习系统架构设计"],
                "learning_resources": ["Coursera 架构课", "FastAPI 官方文档"]
            }


    @staticmethod
    def analyze_skill_distribution(resume_data: Resume):
        """
        分析技能分布：将技能按类别分组，并评估掌握程度
        """
        skills = resume_data.skills or []
        experience = resume_data.experience or []
        education = resume_data.education or []

        prompt = f"""
            请分析以下简历的技能、经验和教育背景，生成技能分布分析报告：
    
            技能列表：{skills}
            工作经验：{experience}
            教育背景：{education}
    
            请按以下 JSON 格式返回分析结果：
            {{
                "skill_categories": {{
                    "technical_skills": [{{"name": "技能名", "proficiency": "beginner/intermediate/advanced/expert", "years": 2}}],
                    "soft_skills": [{{"name": "技能名", "proficiency": "beginner/intermediate/advanced/expert", "years": 1}}],
                    "tools_and_frameworks": [{{"name": "技能名", "proficiency": "beginner/intermediate/advanced/expert", "years": 1}}],
                    "languages": [{{"name": "语言", "proficiency": "basic/fluent/native"}}]
                }},
                "skill_summary": {{
                    "total_skills": 10,
                    "strongest_area": "后端开发",
                    "weakest_area": "前端技术",
                    "years_of_experience": 3
                }},
                "skill_gaps": ["需要提升的技能 1", "需要提升的技能 2"],
                "recommended_focus": ["建议优先学习的技能 1", "建议优先学习的技能 2"]
            }}
    
            要求：
            1. proficiency 掌握程度：beginner(入门), intermediate(中级), advanced(高级), expert(专家)
            2. years 表示使用该技能的年限
            3. skill_gaps 是当前技能与行业标准相比的不足
            4. recommended_focus 是建议优先提升的技能
            5. 只返回有效的 JSON 格式，不要包含其他文字
            """

        response = AIService._call_siliconflow_api(prompt)

        try:
            analysis = json.loads(response)
            return analysis
        except json.JSONDecodeError:
            # 返回默认结构
            return {
                "skill_categories": {
                    "technical_skills": [],
                    "soft_skills": [],
                    "tools_and_frameworks": [],
                    "languages": []
                },
                "skill_summary": {
                    "total_skills": len(skills),
                    "strongest_area": "",
                    "weakest_area": "",
                    "years_of_experience": 0
                },
                "skill_gaps": [],
                "recommended_focus": []
            }


    @staticmethod
    def generate_development_roadmap(resume_data: Resume, target_role: Optional[str] = None):
        """
        生成详细的职业发展路线图
        :param resume_data: 简历数据
        :param target_role: 目标职位（可选），如"高级后端工程师"、"技术架构师"
        """
        skills = resume_data.skills or []
        experience = resume_data.experience or []

        target_info = f"目标职位：{target_role}" if target_role else "根据当前技能自然发展"

        prompt = f"""
            请为求职者生成详细的职业发展路线图：
    
            当前技能：{skills}
            工作经验：{experience}
            {target_info}
    
            请按以下 JSON 格式返回发展路线图：
            {{
                "current_level": "初级/中级/高级/专家",
                "timeline": [
                    {{
                        "phase": "短期（0-6 个月）",
                        "goals": ["目标 1", "目标 2"],
                        "skills_to_learn": ["技能 1", "技能 2"],
                        "projects": ["项目建议 1", "项目建议 2"],
                        "resources": ["学习资源 1", "学习资源 2"],
                        "milestones": ["里程碑 1", "里程碑 2"]
                    }},
                    {{
                        "phase": "中期（6-12 个月）",
                        "goals": ["目标 1", "目标 2"],
                        "skills_to_learn": ["技能 1", "技能 2"],
                        "projects": ["项目建议 1", "项目建议 2"],
                        "resources": ["学习资源 1", "学习资源 2"],
                        "milestones": ["里程碑 1", "里程碑 2"]
                    }},
                    {{
                        "phase": "长期（1-2 年）",
                        "goals": ["目标 1", "目标 2"],
                        "skills_to_learn": ["技能 1", "技能 2"],
                        "projects": ["项目建议 1", "项目建议 2"],
                        "resources": ["学习资源 1", "学习资源 2"],
                        "milestones": ["里程碑 1", "里程碑 2"]
                    }}
                ],
                "career_paths": [
                    {{
                        "role": "技术专家路线",
                        "description": "深耕技术领域，成为某方面专家",
                        "required_skills": ["技能 1", "技能 2"],
                        "typical_titles": ["高级工程师", "资深工程师", "技术专家"]
                    }},
                    {{
                        "role": "管理路线",
                        "description": "转向技术管理岗位",
                        "required_skills": ["团队管理", "项目管理", "沟通协调"],
                        "typical_titles": ["技术主管", "工程经理", "技术总监"]
                    }},
                    {{
                        "role": "全栈路线",
                        "description": "扩展前后端技能，成为全栈工程师",
                        "required_skills": ["前端框架", "后端架构", "DevOps"],
                        "typical_titles": ["全栈工程师", "高级全栈工程师", "技术负责人"]
                    }}
                ],
                "certifications": ["推荐证书 1", "推荐证书 2"],
                "networking_advice": ["参加技术社区", "参与开源项目", "参加行业会议"]
            }}
    
            要求：
            1. timeline 分三个阶段，每个阶段包含具体目标、技能、项目、资源和里程碑
            2. career_paths 提供 3 条不同的职业发展路径
            3. certifications 是相关的高价值证书
            4. networking_advice 是人脉建设建议
            5. 只返回有效的 JSON 格式，不要包含其他文字
            """

        response = AIService._call_siliconflow_api(prompt)

        try:
            roadmap = json.loads(response)
            return roadmap
        except json.JSONDecodeError:
            # 返回默认结构
            return {
                "current_level": "中级",
                "timeline": [
                    {
                        "phase": "短期（0-6 个月）",
                        "goals": ["提升核心技能"],
                        "skills_to_learn": [],
                        "projects": [],
                        "resources": [],
                        "milestones": []
                    },
                    {
                        "phase": "中期（6-12 个月）",
                        "goals": ["扩展技术广度"],
                        "skills_to_learn": [],
                        "projects": [],
                        "resources": [],
                        "milestones": []
                    },
                    {
                        "phase": "长期（1-2 年）",
                        "goals": ["成为领域专家"],
                        "skills_to_learn": [],
                        "projects": [],
                        "resources": [],
                        "milestones": []
                    }
                ],
                "career_paths": [],
                "certifications": [],
                "networking_advice": []
            }


    @staticmethod
    async def _chat_with_ai_stream(messages: list, system_prompt: Optional[str] = None):
        """流式调用 SiliconFlow API 进行对话"""
        url = f"{settings.SILICONFLOW_API_URL}/v1/messages"

        headers = {
            "Authorization": f"Bearer {settings.SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        }

        # 构建消息列表
        api_messages = []

        # 如果有系统提示，添加到消息开头
        if system_prompt:
            api_messages.append({
                "role": "system",
                "content": system_prompt
            })

        # 添加用户消息
        api_messages.extend(messages)

        payload = {
            "model": settings.CHAT_MODEL,
            "messages": api_messages,
            "stream": True
        }

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json=payload,
                    timeout=60.0
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        # log.info(line)
                        if line.startswith("data: "):
                            data = line[6:]  # 移除 "data: " 前缀
                            if data.strip() == "[DONE]":
                                break

                            try:
                                import json
                                chunk = json.loads(data)
                                content = chunk.get("type", '')
                                if content == "content_block_delta":
                                    text = chunk.get("delta").get("text", "")
                                    yield text
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            print(f"SSE Chat API 调用错误：{e}")
            yield f"[错误：{str(e)}]"


ai_service = AIService()
