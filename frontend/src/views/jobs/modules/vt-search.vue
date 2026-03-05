<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import type { UploadCustomRequestOptions, UploadFileInfo } from 'naive-ui';
import { documentsUpload } from '@/service/api/user';
import { useAuthStore } from '@/store/modules/auth';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

const authStore = useAuthStore();

defineOptions({
  name: 'JobSearch'
});

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
  (e: 'update:loading', value: boolean): void;
}

const emit = defineEmits<Emits>();

const loading = defineModel<boolean>('loading', {
  default: false
});

const { formRef, validate, restoreValidation } = useNaiveForm();

const model = defineModel<Api.Jobs.JobsSearchParams>('model', { required: true });

async function reset() {
  await restoreValidation();
  emit('reset');
}

async function search() {
  await validate();
  emit('search');
}

// 上传文件之前
async function beforeAvatarUpload(data: { file: UploadFileInfo; fileList: UploadFileInfo[] }) {
  if (data.file.file?.size / 1024 / 1024 > 10) {
    window.$message?.error('文件必须小于10MB');
    return false;
  }

  return true;
}

const fileListRef = ref<UploadFileInfo[]>();
// 上传文件
async function docUploadRequest({ file, headers }: UploadCustomRequestOptions) {
  const formData = new FormData();
  formData.append('file', file.file as File);

  loading.value = true;
  const { data } = await documentsUpload(formData, headers);
  reset();
  search();

  loading.value = false;
  fileListRef.value = [];
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NForm ref="formRef" :model="model" label-placement="left" :label-width="80">
      <NGrid responsive="screen" item-responsive>
        <NFormItemGi span="24 s:12 m:6" label="职位：" class="pr-24px">
          <NInput v-model:value="model.keyword" placeholder="搜索相关职位" clearable />
        </NFormItemGi>

        <NFormItemGi span="24 m:12" class="pr-24px">
          <NSpace class="w-full" justify="end">
            <NButton @click="reset">
              <template #icon>
                <icon-ic-round-refresh class="text-icon" />
              </template>
              {{ $t('common.reset') }}
            </NButton>
            <NButton type="success" @click="search">
              <template #icon>
                <icon-ic-round-search class="text-icon" />
              </template>
              {{ $t('common.search') }}
            </NButton>

            <NUpload
              v-if="authStore.userInfo.role == 2"
              v-model:file-list="fileListRef"
              :show-file-list="false"
              :custom-request="docUploadRequest"
              accept="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword"
              class="cursor-pointer"
              @before-upload="beforeAvatarUpload"
            >
              <NPopover trigger="hover">
                <template #trigger>
                  <NButton type="primary">AI解析</NButton>
                </template>
                <span>上传JD，AI解析JD，并生成新的岗位</span>
              </NPopover>
            </NUpload>
          </NSpace>
        </NFormItemGi>
      </NGrid>
    </NForm>
  </NCard>
</template>

<style scoped></style>
