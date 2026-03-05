import { localStg } from '@/utils/storage';

/** Get token */
export function getToken() {
  const expiresIn = localStg.get('expires_in');

  if (expiresIn === null || expiresIn < Date.now()) {
    clearAuthStorage();
  }

  return localStg.get('token') || '';
}

/** Get IM token */
export function getIMToken() {
  const expiresIn = localStg.get('im_expires_in');

  if (expiresIn === null || expiresIn < Date.now()) {
    clearAuthStorage();
    return null;
  }

  const imToken: Api.Auth.IMToken = {
    token: localStg.get('im_token') || '',
    user_id: localStg.get('im_user_id') || '',
    expireTimeSeconds: localStg.get('im_expires_in') || 0
  };

  return imToken;
}

/** Clear auth storage */
export function clearAuthStorage() {
  localStg.remove('token');
  localStg.remove('refreshToken');
  localStg.remove('expires_in');

  // IM remove
  localStg.remove('im_token');
  localStg.remove('im_user_id');
  localStg.remove('im_expires_in');
}
