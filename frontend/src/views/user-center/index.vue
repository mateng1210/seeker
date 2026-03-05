<script lang="tsx" setup>
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import UserSet from '@/views/user-center/modules/user-set.vue';
import Resume from '@/views/user-center/modules/resume.vue';
import { useLoading } from '~/packages/hooks';

const route = useRoute();
const activeName = ref('userSet');
const { loading } = useLoading();

// 监听路由参数变化，自动切换选项卡
watch(
  () => route.query.tab,
  (tab) => {
    if (tab === 'resume') {
      activeName.value = 'resume';
    } else if (tab === 'userSet') {
      activeName.value = 'userSet';
    }
  },
  { immediate: true }
);

</script>

<template>
  <NSpin :show="loading" class="h-full" content-class="h-full" description="请等待...">
    <div class="h-full min-h-500px flex-col-stretch gap-10px overflow-hidden lt-sm:overflow-auto">
      <NCard class="h-full" content-style=" overflow: auto;">
        <NTabs v-model:value="activeName" class="h-full">
          <NTabPane class="h-full" name="userSet" tab="个人信息">
            <UserSet />
          </NTabPane>
          <NTabPane class="h-full" name="resume" tab="个人简历">
            <Resume />
          </NTabPane>
        </NTabs>
      </NCard>
    </div>
  </NSpin>
</template>

<style scoped></style>
