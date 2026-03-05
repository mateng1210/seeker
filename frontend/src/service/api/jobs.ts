import { request } from '../request';
import JobsPageSearchParams = Api.Jobs.JobsSearchParams;

/**
 * jobs列表
 */
export function fetchJobsPage(params?: JobsPageSearchParams) {
  return request<Api.Jobs.JobsList>({ url: '/jobs', params });
}

/**
 * jobs列表
 */
export function fetchJobView(job_id: number) {
  return request({ url: `/jobs/${job_id}` });
}

/**
 * 获取匹配匹配分数
 */
export function fetchJobsMatch(job_id: number, is_refresh = 0) {
  return request({ url: `/ai/match`, params: { job_id, is_refresh } });
}
