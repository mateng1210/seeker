/**
 * Namespace Api
 *
 * All backend api type
 */
declare namespace Api {
  import type {
    STATUS_BALANCE_NOT_ENOUGH,
    STATUS_CANCEL,
    STATUS_COMPLETE,
    STATUS_DRAFT,
    STATUS_EXCEPTION,
    STATUS_RUNNING,
    STATUS_STOP,
    STATUS_WAITING
  } from '@/constants/common';

  namespace Common {
    /** common params of paginating */
    interface PaginatingCommonParams {
      /** current page number */
      page: number;
      /** page size */
      num: number;
      /** total count */
      total: number;
    }

    /** common params of paginating query list data */
    interface PaginatingQueryRecord<T = any> extends PaginatingCommonParams {
      list: T[];
    }

    /** common search params of table */
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'page' | 'num'>;

    /**
     * enable status
     *
     * - "1": enabled
     * - "2": disabled
     */
    type EnableStatus = '1' | '2';

    /** common record */
    type CommonRecord<T = any> = {
      /** record id */
      id: number;
      /** record creator */
      createBy: string;
      /** record create time */
      created_at: string;
      /** record updater */
      updateBy: string;
      /** record update time */
      updated_at: string;
      /** record status */
      status: EnableStatus | null;
    } & T;

    /**
     * common backend response
     */
    type CommonResponse = {
      code: number;
      msg: string;
      data?: any;
    };

    /**
     * world language
     */
    type WorldLanguage = {
      id: number;
      name: string;
      self_name: string;
      language_code: string;
      is_video_trans: number;
    };

    type UserGender = '1' | '2';

    type SysVoice = {
      id: number;
      name: string;
      url: string;
      image: string;
      gender: UserGender;
    };

    // 0草稿，100等待中，1000运行中，2400运行完成，3100已停止，3200已关闭或取消，3300余额不足，3400异常.
    type RunStatus =
      | STATUS_DRAFT
      | STATUS_WAITING
      | STATUS_RUNNING
      | STATUS_COMPLETE
      | STATUS_STOP
      | STATUS_CANCEL
      | STATUS_BALANCE_NOT_ENOUGH
      | STATUS_EXCEPTION;
  }

  /**
   * namespace Auth
   *
   * backend api module: "auth"
   */
  namespace Auth {
    interface LoginToken {
      token_type: string;
      access_token: string;
      refresh_token: ?string;
      expires_in: number;
    }

    interface UserInfo {
      id: string;
      avatar: string;
      created_at: string;
      email: string;
      google_id: string;
      is_enabled: string;
      nick_name: string;
      phone: string;
      real_name: string;
      tenant_id: number;
      isset_password: boolean;
      roles: string[];
      role: number;
      buttons: string[];
    }

    interface LoginResponse {
      token: LoginToken;
      user: UserInfo;
    }

    interface IMToken {
      token: string;
      expireTimeSeconds: number;
      user_id: string;
    }

    interface RegisterParams {
      email: string;
      password: string;
      confirmPassword: string;
      role: number;
    }

    // 经验详情类型定义
    type ResumeProjects = {
      name: string;
      description: string;
      project_role: string;
    };

    // 经验详情类型定义
    type ResumeExperience = {
      years: string;
      role: string;
      company: string;
      job_responsibilities: string;
    };

    // 教育经历类型定义
    type ResumeEducation = {
      degree: string;        // 学位/学历
      major: string;         // 专业
      school: string;        // 学校
      graduation_year: string; // 毕业年份
    };
  }

  /**
   * namespace Route
   *
   * backend api module: "route"
   */
  namespace Route {
    type ElegantConstRoute = import('@elegant-router/types').ElegantConstRoute;

    interface MenuRoute extends ElegantConstRoute {
      id: string;
    }

    interface UserRoute {
      routes: MenuRoute[];
      home: import('@elegant-router/types').LastLevelRouteKey;
    }
  }


  namespace Jobs {
    // 岗位
    type Jobs = Common.CommonRecord<{
      id: number;
      title: string;
      location: string;
      required_skills: string[];
      degree: string;
      salary_min: number;
      salary_max: number;
      work_experience_min: number;
      work_experience_max: number;
    }>;

    /** project search params */
    type JobsSearchParams = CommonType.RecordNullable<
      { keyword?: string } & Api.Common.CommonSearchParams
    >;

    type JobsList = Common.PaginatingQueryRecord<Jobs>;

    type JobMatch = Common.CommonRecord<{
      id: number;
      resume_id: number;
      job_id: number;
      match_score: number;
      gaps: string[];
      strengths: string[];
      suggestions: string[];
    }>;
  }

  /**
   * namespace 用户
   * 用户
   */
  namespace User {
    // 文件上传
    type FileUploadParams = CommonType.RecordNullable<{
      file: File;
      group_id?: number;
    }>;

    // 更新密码
    type UpadtePasswordParams = CommonType.RecordNullable<{
      old_password?: string;
      new_password1: string;
      new_password2: string;
    }>;


    type ConsumeParams = CommonType.RecordNullable<{
      module: number;
      sub_module: number;
      created_at_range: number[];
    }>;
  }
}
