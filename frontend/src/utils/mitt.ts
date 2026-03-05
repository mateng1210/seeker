import type { Emitter } from 'mitt';
import mitt from 'mitt';

/** 全局公共事件需要在此处添加类型 */
type Events = {
  aiVideoTranslate: string;
  aiImageTranslate: string;
};

export const emitter: Emitter<Events> = mitt<Events>();
