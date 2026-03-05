import axios from 'axios';
import dayjs from 'dayjs';
import { $t } from '@/locales';

/**
 * Transform record to option
 *
 * @example
 *   ```ts
 *   const record = {
 *     key1: 'label1',
 *     key2: 'label2'
 *   };
 *   const options = transformRecordToOption(record);
 *   // [
 *   //   { value: 'key1', label: 'label1' },
 *   //   { value: 'key2', label: 'label2' }
 *   // ]
 *   ```;
 *
 * @param record
 */
export function transformRecordToOption<T extends Record<string, string>>(record: T) {
  return Object.entries(record).map(([value, label]) => ({
    value,
    label
  })) as CommonType.Option<keyof T, T[keyof T]>[];
}

/**
 * Translate options
 *
 * @param options
 */
export function translateOptions(options: CommonType.Option<string, App.I18n.I18nKey>[]) {
  return options.map(option => ({
    ...option,
    label: $t(option.label)
  }));
}

/**
 * Toggle html class
 *
 * @param className
 */
export function toggleHtmlClass(className: string) {
  function add() {
    document.documentElement.classList.add(className);
  }

  function remove() {
    document.documentElement.classList.remove(className);
  }

  return {
    add,
    remove
  };
}

// 触发下载函数
export function triggerDownload(url: string, fileType: string = 'image', filename?: string): void {
  if (['pdf', 'image'].includes(fileType)) {
    axios.get(url, {
      responseType: 'blob'
    })
      .then(res => {
        // 获取响应头中的Content-Type
        const contentType = res.headers['content-type'] || 'image/jpeg';
        const blob = new Blob([res.data], { type: contentType });
        const url2 = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url2;
        // 设置合适的文件扩展名
        link.download = filename || generateFilename(contentType);
        link.click();
        window.URL.revokeObjectURL(url2);
      });
  } else {
    // 尝试使用 a 链接（同域有效）
    const link = document.createElement('a');
    link.href = url;
    link.target = '_self';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

function generateFilename(contentType: string): string {
  const extension = getExtensionFromMimeType(contentType);
  const timestamp = Date.now();
  return `download_${timestamp}.${extension}`;
}

function getExtensionFromMimeType(mimeType: string): string {
  const mimeToExtension: Record<string, string> = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/gif': 'gif',
    'image/webp': 'webp',
    'video/mp4': 'mp4',
    'video/avi': 'avi'
  };
  return mimeToExtension[mimeType] || 'file';
}

// 添加格式化函数
export function formatDateTime(dateString: string, format: string = 'MM-DD HH:mm') {
  if (!dateString) return '';
  return dayjs(dateString).format(format);
}

/**
 * 运行状态标签映射
 */
export const runStatusTagMap: Record<Api.Common.RunStatus, NaiveUI.ThemeColor> = {
  0: 'default',
  1000: 'primary',
  2400: 'success',
  3100: 'warning',
  3200: 'warning',
  3300: 'error',
  3400: 'error'
};
