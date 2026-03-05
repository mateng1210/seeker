import { request } from '../request';
import ImageTransSearchParams = Api.Image.ImageTransSearchParams;
import ImageTransAddParams = Api.Image.ImageTransAddParams;

/**
 * 图片翻译列表
 */
export function imageTransPage(params?: ImageTransSearchParams) {
  return request<Api.VideoTrans.VideoTransProjectList>({ url: '/api/v1/user/image/trans/page', params });
}

/**
 * 图片翻译创建
 */
export function imageTransAdd(params: ImageTransAddParams) {
  return request<Api.VideoTrans.VideoTransProjectList>({
    url: '/api/v1/user/image/trans/add',
    data: params,
    method: 'post'
  });
}

/**
 * 图片翻译编辑
 */
export function imageTransEdit(id: number) {
  return request<Api.VideoTrans.VideoTransProjectList>({ url: '/api/v1/user/image/trans/edit', params: { id } });
}

/**
 * 图片翻译免费次数
 */
export function getImageTransFreeCount(trans_type) {
  return request<Api.Common.CommonResponse>({ url: '/api/v1/user/image/trans/free_count', params: { trans_type }});
}
