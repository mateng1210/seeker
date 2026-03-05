import { transformRecordToOption } from '@/utils/common';

export const yesOrNoRecord: Record<CommonType.YesOrNo, App.I18n.I18nKey> = {
  Y: 'common.yesOrNo.yes',
  N: 'common.yesOrNo.no'
};

export const yesOrNoOptions = transformRecordToOption(yesOrNoRecord);

export const AI = 'ai';
export const AI_VIDEO_TRANSLATE = 'ai_video_translate';
export const AI_IMAGE_TRANSLATE = 'ai_image_translate';

//  状态：0草稿，100等待，1000运行中，2400运行完成，3100已停止，3200已关闭或取消，3300余额不足，3400异常.
export const STATUS_DRAFT = 0;
export const STATUS_WAITING = 100;
export const STATUS_RUNNING = 1000;
export const STATUS_COMPLETE = 2400;
export const STATUS_STOP = 3100;
export const STATUS_CANCEL = 3200;
export const STATUS_BALANCE_NOT_ENOUGH = 3300;
export const STATUS_EXCEPTION = 3400;

export const appModule: Record<string, string> = {
  ai: 'AI',
  ai_video_translate: 'AI视频翻译',
  ai_image_translate: 'AI图片翻译',
  vip: '开通会员'
};
