<script setup lang="ts">
import { computed } from 'vue';
import { LAYOUT_SCROLL_EL_ID } from '@sa/materials';
import { useAppStore } from '@/store/modules/app';
import { useThemeStore } from '@/store/modules/theme';
import { useRouteStore } from '@/store/modules/route';
import { useTabStore } from '@/store/modules/tab';
import {SuspendedBallChat} from "ai-suspended-ball-chat";
import {getAuthorization} from "@/service/request/shared";
import {getServiceBaseURL} from "@/utils/service";
import {useAuthStore} from "@/store/modules/auth";

defineOptions({
  name: 'GlobalContent'
});

interface Props {
  /** Show padding for content */
  showPadding?: boolean;
}

withDefaults(defineProps<Props>(), {
  showPadding: true
});

const appStore = useAppStore();
const themeStore = useThemeStore();
const routeStore = useRouteStore();
const tabStore = useTabStore();
const authStore = useAuthStore();

const transitionName = computed(() => (themeStore.page.animate ? themeStore.page.animateMode : ''));

function resetScroll() {
  const el = document.querySelector(`#${LAYOUT_SCROLL_EL_ID}`);

  el?.scrollTo({ left: 0, top: 0 });
}

const isHttpProxy = import.meta.env.DEV && import.meta.env.VITE_HTTP_PROXY === 'Y';
const { baseURL } = getServiceBaseURL(import.meta.env, isHttpProxy);

const customRequestConfig = {
  headers: {
    Authorization: getAuthorization(),
    'Content-Type': 'application/json'
  },
  timeout: 30000,
  retryCount: 3,
  retryDelay: 1000
}
const apiUrl = `${baseURL}/ai/chat`;
const appName = 'aaaa';
const domainName = 'cccccc';
const callbacks = {
  onMessage: (message) => {
    console.log('onMessage', message);
  },
  onError: (error) => {
    console.log('onError', error);
  },
  onFinish: () => {
    console.log('onFinish');
  },
};
</script>

<template>
  <RouterView v-slot="{ Component, route }">
    <Transition
      :name="transitionName"
      mode="out-in"
      @before-leave="appStore.setContentXScrollable(true)"
      @after-leave="resetScroll"
      @after-enter="appStore.setContentXScrollable(false)"
    >
      <KeepAlive :include="routeStore.cacheRoutes" :exclude="routeStore.excludeCacheRoutes">
        <component
          :is="Component"
          v-if="appStore.reloadFlag"
          :key="tabStore.getTabIdByRoute(route)"
          :class="{ 'p-16px': showPadding }"
          class="flex-grow bg-layout transition-300"
        />
      </KeepAlive>
    </Transition>
  </RouterView>
  <SuspendedBallChat
    :url="apiUrl"
    :app-name="appName"
    :domain-name="domainName"
    :enable-streaming="true"
    :enable-context="true"
    :enable-local-storage="true"
    :enable-voice-input="true"
    :callbacks="callbacks"
    :custom-request-config="customRequestConfig"
    :enable-image-upload="false"
    :storage-key="authStore.userInfo.id + 'ai_chat'"
    :show-clear-button="true"
  />
</template>

<style></style>
