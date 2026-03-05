<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';

// 定义 props
const props = defineProps({
  data: {
    type: Object,
    required: true
  },
  onChange: {
    type: Function,
    required: false
  },
  onCompleted: {
    type: Function,
    required: true
  }
});

// 定义接收消息的方法
function receiveMessage(event) {
  if (event.data && !event.data.type) {
    const postData = JSON.parse(event.data);
    const { type, data } = postData;
    switch (type) {
      case 'base64':
        props.onCompleted(data);
        break;
      case 'psd':
        props.onChange?.(data);
        break;
      case 'autoHeight':
        const iframe = document.getElementById('editor-Iframe');
        if (iframe) {
          iframe.style.height = data.editorHeight + 'px';
        }
        break;
      default:
        break;
    }
  }
}

// 定义发送消息的方法
function postMessage() {
  const iFrame = document.getElementById('editor-Iframe');
  const { sourceLang, targetLang, templateJson } = props.data;
  if (iFrame) {
    iFrame.onload = function() {
      const data = {
        sourceLang,
        targetLang,
        templateJson,
        locale: 'zh-cn'
      };
      iFrame.contentWindow.postMessage(JSON.stringify(data), '*');
    };
  }
}

// 生命周期钩子
onMounted(() => {
  window.addEventListener('message', receiveMessage, true);
  postMessage();
});

// 清理事件监听器
onUnmounted(() => {
  window.removeEventListener('message', receiveMessage, true);
});
</script>

<template>
  <div class="picture-editor-component">
    <iframe id="editor-Iframe" src="https://www.alifanyi.com/erp/imageTrans.html" frameborder="no" scrolling="no" />
  </div>
</template>

<style scoped>
.picture-editor-component {
  width: 1440px;
  margin: 0 auto;
  margin-bottom: 20px;
}
iframe {
  width: 1440px;
  height: 600px;
}
</style>
