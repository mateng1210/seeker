<script setup lang="ts">
import { computed } from 'vue';
import { useRouterPush } from '@/hooks/common/router';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { $t } from '@/locales';

defineOptions({
  name: 'HeaderBanner'
});

const appStore = useAppStore();
const authStore = useAuthStore();
const { routerPush } = useRouterPush();

const gap = computed(() => (appStore.isMobile ? 0 : 16));

interface StatisticData {
  id: number;
  label: string;
  value: string;
}

const statisticData = computed<StatisticData[]>(() => [
  {
    id: 0,
    label: $t('page.home.projectCount'),
    value: '25'
  },
  {
    id: 1,
    label: $t('page.home.todo'),
    value: '4/16'
  },
  {
    id: 2,
    label: $t('page.home.message'),
    value: '12'
  }
]);
</script>

<template>
  <NCard :bordered="false" class="card-wrapper">
    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:18">
        <div class="flex-y-center">
          <div class="size-72px shrink-0 overflow-hidden rd-1/2">
            <img src="@/assets/imgs/soybean.jpg" class="size-full" />
          </div>
          <div class="pl-12px">
            <h3 class="text-18px font-semibold">
              {{ $t('page.home.greeting', { userName: authStore.userInfo.nick_name }) }}
            </h3>
            <p class="text-#999 leading-30px">{{ $t('page.home.weatherDesc') }}</p>
          </div>
        </div>
      </NGi>
      <NGi span="24 s:24 m:6">
        <NSpace :size="24" justify="end">
          <NButton
            v-if="authStore.userInfo.role === 1"
            size="large"
            type="primary"
            @click="routerPush({ name: 'user-center', query: { tab: 'resume' } })"
          >
            个人简历
          </NButton>
        </NSpace>
      </NGi>
    </NGrid>
  </NCard>
</template>

<style scoped></style>
