import { request } from '../request';
import FileUploadParams = Api.User.FileUploadParams;
import UpadtePasswordParams = Api.User.UpadtePasswordParams;

/**
 * 文件上传列表
 */
export function documentsUpload(params: FileUploadParams, headers: Record<string, string>) {
  // {"status":"success","code":200,"data":{"id":12,"url":"https://ai-api.pigmentv.com/uploads/1/1/1/68e85bea0df65.mp4","title":"68e85bea0df65.mp4","original":"9月8日.mp4","group_id":0,"thumbnail":"https://ai-api.pigmentv.com/uploads/1/1/1/68e85bea0df65.jpg"}}
  return request({ url: '/documents/upload', data: params, method: 'post', headers, timeout: 600000 });
}


/**
 * 用户更新昵称
 */
export function apiUserUpdate(field: string, value: string) {
  return request<Api.Common.CommonResponse>({
    url: '/auth/update',
    data: { field, value },
    method: 'put'
  });
}

/**
 * 用户更新头像
 */
export function apiUpdateAvatar(attachment_id: number, avatar: string) {
  return request<Api.Common.CommonResponse>({ url: '/api/v1/user/update/avatar', params: { avatar, attachment_id }, method: 'put' });
}

/**
 * 用户更新密码
 */
export function apiUpdatePassword(params: UpadtePasswordParams) {
  return request<Api.Common.CommonResponse>({ url: '/auth/change_password', data: params, method: 'put' });
}

/**
 * 用户更新手机号
 */
export function apiUpdatePhone(new_phone: string, code: string) {
  return request<Api.Common.CommonResponse>({
    url: '/api/v1/user/update/phone',
    data: { new_phone, code },
    method: 'put'
  });
}

/**
 * 用户充值记录分页
 */
export function fetchGetResume() {
  return request<Api.Common.CommonResponse>({
    url: '/resumes'
  });
}

/**
 * 用户消费记录分页
 */
export function fetchUserConsumePage(params?: Api.User.ConsumeParams) {
  return request<Api.Common.CommonResponse>({
    url: '/api/v1/user/consume/page',
    params
  });
}

/**
 * 购买计划
 * @param plan_id
 */
export function buyPlan(plan_id: number) {
  return request<Api.Common.CommonResponse>({
    url: '/api/v1/user/buy/plan',
    params: { plan_id }
  });
}
