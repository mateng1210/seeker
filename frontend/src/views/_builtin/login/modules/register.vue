<script setup lang="ts">
import { computed, reactive } from 'vue';
import { useRouterPush } from '@/hooks/common/router';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { useCaptcha } from '@/hooks/business/captcha';
import { $t } from '@/locales';
import {fetchRegister} from "@/service/api";
import RegisterParams = Api.Auth.RegisterParams;

defineOptions({
  name: 'Register'
});

const { toggleLoginModule } = useRouterPush();
const { formRef, validate } = useNaiveForm();
const { label, isCounting, loading, getCaptcha } = useCaptcha();

interface FormModel {
  email: string;
  password: string;
  confirmPassword: string;
  role: number;
}

const model: FormModel = reactive<RegisterParams>({
  email: '',
  password: '',
  confirmPassword: '',
  role: 1
});

const rules = computed<Record<keyof FormModel, App.Global.FormRule[]>>(() => {
  const { formRules, createConfirmPwdRule } = useFormRules();

  return {
    email: formRules.email,
    password: formRules.pwd,
    confirmPassword: createConfirmPwdRule(model.password)
  };
});

async function handleSubmit() {
  try {
    await validate();

    const { data } = await fetchRegister(model);

    window.$message?.success('注册成功');

    //等待跳转
    await new Promise(resolve => setTimeout(resolve, 2000));

    toggleLoginModule('pwd-login');
  }catch (errors){
    const firstError = Object.values(errors)[0] as string;
    window.$message?.error(firstError[0].message);
  }
}
</script>

<template>
  <NForm ref="formRef" :model="model" :rules="rules" size="large" :show-label="false" @keyup.enter="handleSubmit">
    <NFormItem path="email">
      <NInput v-model:value="model.email" placeholder="请输入邮箱" />
    </NFormItem>
    <NFormItem path="password">
      <NInput
        v-model:value="model.password"
        type="password"
        show-password-on="click"
        :placeholder="$t('page.login.common.passwordPlaceholder')"
      />
    </NFormItem>
    <NFormItem path="confirmPassword">
      <NInput
        v-model:value="model.confirmPassword"
        type="password"
        show-password-on="click"
        :placeholder="$t('page.login.common.confirmPasswordPlaceholder')"
      />
    </NFormItem>
    <NFormItem>
      <NRadioGroup v-model:value="model.role">
        <NRadio :value="1">我是应聘者</NRadio>
        <NRadio :value="2">我是招聘者</NRadio>
      </NRadioGroup>
    </NFormItem>
    <NSpace vertical :size="18" class="w-full">
      <NButton type="primary" size="large" round block @click="handleSubmit">
        {{ $t('common.confirm') }}
      </NButton>
      <NButton size="large" round block @click="toggleLoginModule('pwd-login')">
        {{ $t('page.login.common.back') }}
      </NButton>
    </NSpace>
  </NForm>
</template>

<style scoped></style>
