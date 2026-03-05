<script lang="tsx" setup>
import { reactive, ref } from 'vue';
import type { FormInst, FormItemRule, FormRules, UploadCustomRequestOptions, UploadFileInfo } from 'naive-ui';
import {
  apiUpdateAvatar,
  apiUpdateNickName,
  apiUpdatePassword,
  apiUpdatePhone, apiUserUpdate
} from '@/service/api/user';
import { fetchSendCode } from '@/service/api/common';
import { useAuthStore } from '@/store/modules/auth';
import { $t } from '@/locales';
import { useLoading } from '~/packages/hooks';

defineOptions({ name: 'UserSet' });
//
const { loading, startLoading, endLoading } = useLoading();
const authStore = useAuthStore();

interface PostFormI {
  nick_name: string;
  old_phone: string;
  isset_password: boolean;
  new_phone: string;
  sms_code: string;
  old_password: string;
  new_password1: string;
  new_password2: string;
}

const nickNameFormRef = ref<FormInst>();
const phoneFormRef = ref<FormInst>();
const passwordFormRef = ref<FormInst>();
const postForm = reactive<PostFormI>({
  nick_name: authStore.userInfo.nick_name,
  old_phone: authStore.userInfo.phone,
  isset_password: authStore.userInfo.isset_password,
  new_phone: '',
  sms_code: '',
  old_password: '',
  new_password1: '',
  new_password2: ''
});

const nickNameRules = reactive<FormRules<PostFormI>>({
  nick_name: [
    { required: true, message: '请输入账号名称，长度1-20位', trigger: 'blur' },
    { min: 1, max: 20, message: '请输入账号名称，长度1-20位', trigger: 'blur' }
  ]
});
const phoneRules = reactive<FormRules<PostFormI>>({
  new_phone: [
    { type: 'number', required: true, message: '请输入正确的手机号', trigger: 'blur' },
    { min: 11, max: 11, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  sms_code: [
    { required: true, message: '请输入5位数字验证码', trigger: 'blur' },
    { min: 5, max: 5, message: '请输入5位数字验证码', trigger: 'blur' }
  ]
});
const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入旧密码，长度6-18位', trigger: 'blur' },
    { min: 6, max: 18, message: '请输入旧密码，长度6-18位', trigger: 'blur' }
  ],
  new_password1: [
    { required: true, message: '请输入新密码，长度6-18位', trigger: 'blur' },
    { min: 6, max: 18, message: '请输入新密码，长度6-18位', trigger: 'blur' }
  ],
  new_password2: [
    { required: true, message: '请再次确认新密码，长度6-18位', trigger: 'blur' },
    { min: 6, max: 18, message: '请再次确认新密码，长度6-18位', trigger: 'blur' },
    {
      validator: (rule: FormItemRule, value, callback) => {
        if (value !== postForm.new_password1) {
          callback(new Error('两次输入的密码不一致!'));
        } else {
          callback();
        }
      },
      trigger: ['input', 'blur']
    }
  ]
};

const avatarUrl = authStore.userInfo?.avatar ? ref(authStore.userInfo.avatar) : ref(null);

// 上传图片之前
async function beforeAvatarUpload(data: { file: UploadFileInfo; fileList: UploadFileInfo[] }) {
  // image/jpeg、image/jpg、image/pjpeg、image/png、image/webp
  if (data.file.file?.size / 1024 / 1024 > 2) {
    window.$message?.error('图片必须小于2MB');
    return false;
  }

  return true;
}

const fileListRef = ref<UploadFileInfo[]>();
// 上传头像
async function avatarUploadRequest({ file, headers }: UploadCustomRequestOptions) {
  startLoading();

  const formData = new FormData();
  formData.append('file', file.file as File);
  formData.append('wait_deleted', '1');

  fileUpload(formData, headers)
    .then(async res => {
      const data = res.data;
      avatarUrl.value = data.url;

      apiUpdateAvatar(data.id, data.path)
        .then(res2 => {
          authStore.setUserInfo({
            ...authStore.userInfo,
            avatar: data.url
          });
        })
        .catch(error => {
          console.log(error);
        })
        .finally(() => {
          endLoading();
      });
    })
    .catch(error => {
      console.log(error);
    })
    .finally(() => {
    });


  fileListRef.value = [];
}

// 修改账号名称
const nickNameModalVisible = ref(false);

function updateNickName() {
  nickNameFormRef.value?.validate(async errors => {
    if (errors) {
      console.log(errors);
    } else {
      startLoading();
      const { error } = await apiUserUpdate('nick_name', postForm.nick_name);

      if (!error) {
        window.$message?.success('更新成功！');
        nickNameModalVisible.value = false;

        authStore.setUserInfo({
          ...authStore.userInfo,
          nick_name: postForm.nick_name
        });
      }

      endLoading();
    }
  });
}

// 修改手机号码
const phoneModalVisible = ref(false);

function updatePhone() {
  phoneFormRef.value?.validate(async errors => {
    if (errors) {
      console.log(errors);
    } else {
      startLoading();
      const { error } = await apiUserUpdate('phone', postForm.new_phone);

      if (!error) {
        window.$message?.success('更新成功！');
        phoneModalVisible.value = false;

        authStore.setUserInfo({
          ...authStore.userInfo,
          phone: postForm.new_phone
        });
      }

      endLoading();
    }
  });
}

// 获取验证码
const countdown = ref(0); // 倒计时秒数
const isCounting = ref(false); // 是否正在倒计时

// 开始倒计时
const timer = ref<NodeJS.Timeout | null>(null);
const startCountdown = () => {
  if (isCounting.value) return; // 如果已经在倒计时，直接返回
  isCounting.value = true;
  countdown.value = 60;

  timer.value = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      clearInterval(timer.value);
      isCounting.value = false;
    }
  }, 1000);
};

async function sendCode() {
  if (postForm.new_phone.length !== 11) {
    window.$message?.error('请输入11位新手机号');
    return;
  }

  startCountdown(); // 开始倒计时
  const { error } = await fetchSendCode(postForm.new_phone, '1');

  if (!error) {
    window.$message?.success('发送成功，请注意查收。');
  } else {
    isCounting.value = false;
    clearInterval(timer.value);
  }
}

// 修改密码
const passwordModalVisible = ref(false);

function updatePassword() {
  passwordFormRef.value?.validate(async errors => {
    if (errors) {
      console.log(errors);
    } else {
      startLoading();

      const { error } = await apiUpdatePassword({
        new_password1: postForm.new_password1,
        new_password2: postForm.new_password2,
        old_password: postForm.old_password
      });

      if (!error) {
        window.$message?.success('更新成功！');
        passwordModalVisible.value = false;
      }

      endLoading();
    }
  });
}

const closeModal = (type: string = 'nick_name') => {
  switch (type) {
    case 'phone':
      postForm.new_phone = '';
      postForm.sms_code = '';
      postForm.old_phone = authStore.userInfo.phone;
      break;
    case 'password':
      postForm.old_password = '';
      postForm.new_password1 = '';
      postForm.new_password2 = '';
      break;
    default:
      postForm.nick_name = authStore.userInfo.nick_name;
      break;
  }
};
</script>

<template>
  <NSpin :description="$t('common.loading')" :show="loading">
    <NCard class="h-full">
      <NForm :model="postForm" class="max-w-380px" label-placement="left" label-width="120" size="medium">
<!--        <NFormItem label="头像：">-->
<!--          <NUpload-->
<!--            v-model:file-list="fileListRef"-->
<!--            :show-file-list="false"-->
<!--            :custom-request="avatarUploadRequest"-->
<!--            accept="image/jpeg,image/jpg,image/pjpeg,image/png,image/webp"-->
<!--            class="cursor-pointer"-->
<!--            @before-upload="beforeAvatarUpload"-->
<!--          >-->
<!--            <NAvatar v-if="avatarUrl" :size="80" :src="avatarUrl" />-->
<!--            <NIcon v-else class="text-80px color-#c0c4cc">-->
<!--              <SvgIcon icon="carbon:user-avatar-filled" />-->
<!--            </NIcon>-->
<!--          </NUpload>-->
<!--        </NFormItem>-->

        <NFormItem label="昵称：">
          <NInputGroup>
            <NInput v-model:value="postForm.nick_name" :readonly="true" />
            <NPopover placement="top" trigger="hover">
              <template #trigger>
                <NButton type="primary" @click="nickNameModalVisible = true">
                  <NIcon>
                    <SvgIcon icon="material-symbols:edit-square-outline" />
                  </NIcon>
                </NButton>
              </template>
              <span>修改昵称</span>
            </NPopover>
          </NInputGroup>
        </NFormItem>

        <NFormItem label="手机号码：">
          <NInputGroup>
            <NInput v-model:value="postForm.old_phone" :readonly="true" />
            <NPopover placement="top" trigger="hover">
              <template #trigger>
                <NButton type="primary" @click="phoneModalVisible = true">
                  <NIcon>
                    <SvgIcon icon="material-symbols:edit-square-outline" />
                  </NIcon>
                </NButton>
              </template>
              <span>修改手机号码</span>
            </NPopover>
          </NInputGroup>
        </NFormItem>

        <NFormItem label="密码：">
          <NInputGroup>
            <NInput :readonly="true" value="********" />
            <NPopover placement="top" trigger="hover">
              <template #trigger>
                <NButton type="primary" @click="passwordModalVisible = true">
                  <NIcon>
                    <SvgIcon icon="material-symbols:edit-square-outline" />
                  </NIcon>
                </NButton>
              </template>
              <span>修改密码</span>
            </NPopover>
          </NInputGroup>
        </NFormItem>
      </NForm>
    </NCard>
  </NSpin>

  <NModal
    v-model:show="nickNameModalVisible"
    :mask-closable="false"
    preset="dialog"
    title="修改昵称"
    width="350px"
    @after-leave="closeModal('nick_name')"
  >
    <NSpin :description="$t('common.loading')" :show="loading">
      <NForm
        ref="nickNameFormRef"
        :model="postForm"
        :rules="nickNameRules"
        class="mt-20px"
        label-placement="left"
        label-width="100"
      >
        <NFormItem label="昵称：" prop="nick_name">
          <NInput v-model:value="postForm.nick_name" maxlength="20" placeholder="请输入昵称" />
        </NFormItem>
      </NForm>
      <NSpace justify="end">
        <NButton @click="nickNameModalVisible = false">取消</NButton>
        <NButton type="primary" @click="updateNickName">确认</NButton>
      </NSpace>
    </NSpin>
  </NModal>

  <NModal
    v-model:show="phoneModalVisible"
    :mask-closable="false"
    preset="dialog"
    title="修改手机号"
    width="450px"
    @after-leave="closeModal('phone')"
  >
    <NSpin :description="$t('common.loading')" :show="loading">
      <NForm
        ref="phoneFormRef"
        :model="postForm"
        :rules="phoneRules"
        class="mt-20px"
        label-placement="left"
        label-width="100"
      >
        <NFormItem label="旧手机号：">
          <NInput v-model:value="postForm.old_phone" disabled maxlength="20" />
        </NFormItem>
        <NFormItem label="新手机号：" prop="new_phone">
          <NInput
            v-model:value="postForm.new_phone"
            clearable
            maxlength="11"
            minlength="11"
            placeholder="请输入11位手机号"
          />
        </NFormItem>
        <NFormItem label="验证码：" prop="new_phone">
          <NInputGroup>
            <NInput v-model:value="postForm.sms_code" clearable maxlength="20" placeholder="请输入验证码" />
            <NButton :disabled="isCounting" @click="sendCode">{{ isCounting ? `${countdown}秒` : '验证码' }}</NButton>
          </NInputGroup>
        </NFormItem>
      </NForm>

      <NSpace justify="end">
        <NButton @click="phoneModalVisible = false">取消</NButton>
        <NButton type="primary" @click="updatePhone">确认</NButton>
      </NSpace>
    </NSpin>
  </NModal>

  <NModal
    v-model:show="passwordModalVisible"
    :mask-closable="false"
    preset="dialog"
    title="修改密码"
    width="350px"
    @after-leave="closeModal('password')"
  >
    <NSpin :description="$t('common.loading')" :show="loading">
      <NForm
        ref="passwordFormRef"
        :model="postForm"
        :rules="passwordRules"
        class="mt-20px"
        label-placement="left"
        label-width="100"
      >
        <NFormItem v-if="postForm.isset_password" label="旧密码：" path="old_password">
          <NInput
            v-model:value="postForm.old_password"
            clearable
            maxlength="16"
            minlength="6"
            placeholder="请输入旧密码"
            show-password-on="click"
            type="password"
          />
        </NFormItem>
        <NFormItem label="新密码：" path="new_password1">
          <NInput
            v-model:value="postForm.new_password1"
            clearable
            maxlength="16"
            minlength="6"
            placeholder="新密码，长度6-16位"
            show-password-on="click"
            type="password"
          />
        </NFormItem>
        <NFormItem label="确认密码：" path="new_password2">
          <NInput
            v-model:value="postForm.new_password2"
            clearable
            maxlength="16"
            minlength="6"
            placeholder="确认密码，长度6-16位"
            show-password-on="click"
            type="password"
          />
        </NFormItem>
        <NSpace justify="end">
          <NButton @click="passwordModalVisible = false">取消</NButton>
          <NButton type="primary" @click="updatePassword">确认</NButton>
        </NSpace>
      </NForm>
    </NSpin>
  </NModal>
</template>

<style lang="scss" scoped></style>
