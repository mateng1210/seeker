<script lang="tsx" setup>
import { onMounted, reactive, ref } from 'vue';
import type { UploadCustomRequestOptions, UploadFileInfo } from 'naive-ui';
import {
 documentsUpload, fetchGetResume,
} from '@/service/api/user';
import { $t } from '@/locales';
import { useLoading } from '~/packages/hooks';
import ResumeExperience = Api.Auth.ResumeExperience;
import ResumeEducation = Api.Auth.ResumeEducation;
import ResumeProjects = Api.Auth.ResumeProjects;

defineOptions({ name: 'Resume' });
//
const { loading, startLoading, endLoading } = useLoading();


interface PostFormI {
  skills: string[];
  experience: ResumeExperience[];
  education: ResumeEducation[];
  projects: ResumeProjects[];
}

const postForm = reactive<PostFormI>({
  skills: [],
  experience: null,
  education: null,
  projects: null
});

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
  startLoading();

  const formData = new FormData();
  formData.append('file', file.file as File);

  startLoading();
  const { data } = await documentsUpload(formData, headers)

  Object.assign(postForm, data);
  endLoading();

  fileListRef.value = [];
}

onMounted(async () => {
  startLoading();
  const { data } = await fetchGetResume();

  console.log("-----",data);
  Object.assign(postForm, data);
  endLoading();
})

</script>

<template>
  <NSpin :description="$t('common.loading')" :show="loading">
    <NCard class="h-full" content-class="h-full">
      <NUpload
        v-model:file-list="fileListRef"
        :show-file-list="false"
        :custom-request="docUploadRequest"
        accept="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword"
        class="cursor-pointer"
        @before-upload="beforeAvatarUpload"
      >
        <NPopover trigger="hover">
          <template #trigger>
            <NButton type="primary" size="large" class="absolute left-1050px top-35px">AI解析</NButton>
          </template>
          <span>上传简历，AI解析简历，并更新简历</span>
        </NPopover>
      </NUpload>

      <NForm :model="postForm" class="max-w-980px" label-placement="left" label-width="120" size="medium">
        <NFormItem label="技能列表：">
          <NDynamicTags v-model:value="postForm.skills" :closable="false" />
        </NFormItem>

        <NFormItem label="经验详情：">
          <NCard>
            <NFlex vertical>
              <NLayout v-for="(exp, index) in postForm.experience" :key="index" class="mb-4">
                <NLayoutHeader>
                  <NGradientText type="info">公司名称</NGradientText>：{{ exp.company }} &nbsp; &nbsp; <NGradientText type="info">工作年限</NGradientText>：{{ exp.years }} 年</NLayoutHeader>
                <NLayoutContent>
                  <NGradientText type="info">工作职责</NGradientText>：{{ exp.job_responsibilities }}
                </NLayoutContent>
              </NLayout>
            </NFlex>
          </NCard>
        </NFormItem>

        <NFormItem label="教育背景：">
          <NCard>
            <NFlex vertical>
              <NLayout v-for="(edu, index) in postForm.education" :key="index" class="mb-4">
                <NLayoutHeader>
                  <NGradientText type="info">学校名称</NGradientText>：{{ edu.school }} &nbsp; &nbsp;
                  <NGradientText type="info">专业</NGradientText>：{{ edu.major }} &nbsp; &nbsp;
                  <NGradientText type="info">学历</NGradientText>：{{ edu.degree }} &nbsp; &nbsp;
                  <NGradientText type="info">毕业年份：</NGradientText>{{ edu.graduation_year }}</NLayoutHeader>
              </NLayout>
            </NFlex>
          </NCard>
        </NFormItem>

        <NFormItem label="项目记录：">
          <NCard>
            <NFlex vertical>
              <NLayout v-for="(pro, index) in postForm.projects" :key="index" class="mb-4">
                <NLayoutHeader><NGradientText type="info">项目名称</NGradientText>：{{ pro.name }} &nbsp; &nbsp;</NLayoutHeader>
                <NLayoutContent>
                  <NGradientText type="info">项目描述</NGradientText>：{{ pro.description }}
                </NLayoutContent>
              </NLayout>
            </NFlex>
          </NCard>
        </NFormItem>
      </NForm>
    </NCard>
  </NSpin>

</template>

<style lang="scss" scoped></style>
