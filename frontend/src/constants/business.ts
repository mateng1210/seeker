import { transformRecordToOption } from '@/utils/common';

export const enableStatusRecord: Record<Api.Common.EnableStatus, App.I18n.I18nKey> = {
  '1': 'page.manage.common.status.enable',
  '2': 'page.manage.common.status.disable'
};

export const enableStatusOptions = transformRecordToOption(enableStatusRecord);

export const userGenderRecord: Record<Api.SystemManage.UserGender, App.I18n.I18nKey> = {
  '1': 'page.manage.user.gender.male',
  '2': 'page.manage.user.gender.female'
};

export const userGenderOptions = transformRecordToOption(userGenderRecord);

export const menuTypeRecord: Record<Api.SystemManage.MenuType, App.I18n.I18nKey> = {
  '1': 'page.manage.menu.type.directory',
  '2': 'page.manage.menu.type.menu'
};

export const menuTypeOptions = transformRecordToOption(menuTypeRecord);

export const menuIconTypeRecord: Record<Api.SystemManage.IconType, App.I18n.I18nKey> = {
  '1': 'page.manage.menu.iconType.iconify',
  '2': 'page.manage.menu.iconType.local'
};

export const menuIconTypeOptions = transformRecordToOption(menuIconTypeRecord);

export const runStatusRecord: Record<Api.Common.RunStatus, App.I18n.I18nKey> = {
  '0': 'common.runStatus.draft',
  '100': 'common.runStatus.running',
  '1000': 'common.runStatus.running',
  '2400': 'common.runStatus.complete',
  '3100': 'common.runStatus.stop',
  '3200': 'common.runStatus.cancel',
  '3300': 'common.runStatus.notEnough',
  '3400': 'common.runStatus.exception'
};
export const projectStatusOptions = transformRecordToOption(runStatusRecord);
