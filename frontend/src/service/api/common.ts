import {request} from '../request';

/**
 * 全球语言
 */
export function fetchWorldLanguage() {
  return request<Api.Common.CommonResponse>({url: '/api/v1/common/language/list'});
}

/**
 * 发送验证码
 */
export function fetchSendCode(account: string, account_type: string) {
  return request<Api.Common.CommonResponse>({
    url: '/api/v1/common/user/send_code',
    params: { account, account_type }
  });
}

/**
 * 获取套餐列表
 */
export function fetchPlansList() {
  return request<Api.Common.CommonResponse>({url: '/api/v1/common/plans/list'});
}
