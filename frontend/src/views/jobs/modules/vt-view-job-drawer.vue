<script lang="tsx" setup xmlns="http://www.w3.org/1999/html">
import { NButton, NFlex, useDialog, NPopconfirm, NPopover, NTag, NText } from 'naive-ui';
import { $t } from '@/locales';
import 'vue3-video-play/dist/style.css';
import { useThemeStore } from "@/store/modules/theme";
import {onMounted, reactive, ref} from 'vue';
import {useAuthStore} from "@/store/modules/auth";
import {fetchJobsMatch} from "@/service/api/jobs";
import {useLoading} from "~/packages/hooks";

const {loading, startLoading, endLoading} = useLoading();
const dialog = useDialog();
const authStore = useAuthStore();

defineOptions({
  name: 'ViewJobPage'
});

interface Props {
  viewJobC: {
    id: number;
    title: string;
    location: string;
    degree: string;
    required_skills: string[];
    job_responsibility: string[];
    job_requirements: string[];
    salary_min: number;
    salary_max: number;
    work_experience_min: number;
    work_experience_max: number;
    benefits: string;
  };
}

const visible = defineModel<boolean>('visible', {
  default: false
});
const props = defineProps<Props>();

const matchView = reactive({
  match_score: 0,
  gaps: [],
  strengths: [],
  suggestions: [],
});
const showMatchScore = ref(false);

function viewMatch() {
  showMatchScore.value = true;
}


function refreshMatch() {
  dialog.info({
    title: 'AI分析',
    content: '将使用AI重新评估你与当前职位的匹配度，确定开始评估？',
    positiveText: '确定',
    negativeText: '取消',
    draggable: true,
    onPositiveClick: () => {
      getJobMatch(props.viewJobC.id, 1);
    },
    onNegativeClick: () => {

    }
  })
}

async function getJobMatch(job_id: number, is_refresh = 0) {
  startLoading();
  // 获取职位匹配度
  const { data } = await fetchJobsMatch(job_id, is_refresh);
  Object.assign(matchView, data);

  endLoading();
}

onMounted(async () => {
  if (authStore.userInfo.role === 1) {
    // 获取职位匹配度
    getJobMatch(props.viewJobC.id);
  }
});

</script>

<template>
  <NDrawer v-model:show="visible" width="70%">
    <NDrawerContent >
      <template #header>
        <NSpace justify="space-between">
          <NSpace class="leading-28px" :size="[30,0]">
            <NText class="font-bold">{{props.viewJobC.title}}</NText>
            <NText class="text-red-5 font-medium">
              <NIcon class="left-8px top-2px">
                <SvgIcon icon="fa7-solid:rmb" />
              </NIcon>
              {{props.viewJobC.salary_min}} - {{props.viewJobC.salary_max}}
            </NText>
          </NSpace>

          <NButton size="small" type="info" @click="visible = false">
            {{ $t('common.close') }}
          </NButton>
        </NSpace>
      </template>

      <NFlex justify="space-between">
        <NFlex vertical class="flex-1 overflow-auto">
          <NSpace class="leading-28px" :size="[30,0]">
            <NText class="text-base">
              <NIcon class="top-2px">
                <SvgIcon icon="material-symbols:location-on" />
              </NIcon>
              {{ props.viewJobC.location }}
            </NText>
            <NText class="text-base">
              <NIcon class="top-2px mr-3px text-size-18px">
                <SvgIcon icon="material-symbols:shopping-bag" />
              </NIcon>
              <span v-if="props.viewJobC.work_experience_min > 0">
                {{props.viewJobC.work_experience_min}}年以上
              </span>
              <span v-else>
                不限
              </span>
            </NText>
            <NText class="text-base">
              <NIcon class="top-4px mr-5px text-size-18px">
                <SvgIcon icon="icon-park-solid:degree-hat" />
              </NIcon>
              <span v-if="props.viewJobC.degree">
                {{ props.viewJobC.degree }}
              </span>
              <span v-else>
                不限
              </span>
            </NText>
          </NSpace>
          <NText class="pt-10px text-lg font-bold">
            职位描述
          </NText>
          <NSpace>
            <NTag v-for="(skill, index) in props.viewJobC.required_skills" :key="index" type="primary">
              {{ skill }}
            </NTag>
          </NSpace>

          <NSpace v-if="props.viewJobC.job_responsibility" class="pt-10px" size="small" vertical>
            <NText class="text-size-16px">岗位职责</NText>
            <span v-for="(line, index) in props.viewJobC.job_responsibility" :key="index">{{ index+1 }}. {{ line }}</span>
          </NSpace>
          <NSpace v-if="props.viewJobC.job_requirements" class="pt-10px" size="small" vertical>
            <NText class="text-size-16px">任职要求</NText>
            <span v-for="(line, index) in props.viewJobC.job_requirements" :key="index">{{ index+1 }}. {{ line }}</span>
          </NSpace>
        </NFlex>

        <span v-if="authStore.userInfo.role === 1" class="flex-0 w-150px pt-20px">
          <NPopover trigger="hover" placement="left">
            <template #trigger>
              <NProgress
                class="cursor-pointer"
                type="circle"
                :percentage="matchView.match_score"
                :stroke-width="9"
                @click="viewMatch(props.viewJobC.id)"
              >
                <NGradientText class="text-center text-22px font-bold" type="info">{{ matchView.match_score }}分</NGradientText>
              </NProgress>
            </template>
            <span>你与当前职位匹配度，点击查看详情。</span>
          </NPopover>
        </span>
      </NFlex>

    </NDrawerContent>

    <NModal
      v-model:show="showMatchScore"
      :mask-closable="false"
      preset="card"
      class="h-500px w-800px"
      content-class="h-full overflow-y-auto"
    >

      <NSpin :description="$t('common.loading')" :show="loading" class="h-full" content-class="h-full">
        <NForm
          label-placement="left"
          label-width="120">
          <NFormItem label="技能差距：">
            <NSpace>
              <NTag v-for="(skill, index) in matchView.gaps" :key="index" type="warning">
                {{ skill }}
              </NTag>
            </NSpace>
          </NFormItem>
          <NFormItem label="技能优势技能：">
            <NSpace>
              <NTag v-for="(strength, index) in matchView.strengths" :key="index" type="primary">
                {{ strength }}
              </NTag>
            </NSpace>
          </NFormItem>
          <NFormItem label="改进建议：">
            <NSpace>
              <NText v-for="(suggestion, index) in matchView.suggestions" :key="index">
                {{ suggestion }}
              </NText>
            </NSpace>
          </NFormItem>

        </NForm>
      </NSpin>


      <template #footer>
        <NSpace justify="end">
          <NButton attr-type="button" type="info" @click="showMatchScore = false">
            关闭
          </NButton>
          <NButton attr-type="button" type="success" @click="refreshMatch()">
            重新评估
          </NButton>
        </NSpace>
      </template>
    </NModal>

  </NDrawer>
</template>

<style scoped></style>
