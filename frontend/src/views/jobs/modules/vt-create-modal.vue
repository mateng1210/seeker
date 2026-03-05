<script setup lang="ts">
import {h, nextTick, onMounted, reactive, ref} from 'vue';
import type {VNodeChild} from 'vue';
import type {
  FormInst,
  SelectOption,
  SelectRenderTag,
  StepsProps,
  UploadCustomRequestOptions,
  UploadFileInfo
} from 'naive-ui';
import {NButton, NIcon, NPopover, useLoadingBar} from 'naive-ui';
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js'
import {getVideoTransFreeCount, projectAdd} from '@/service/api/video-trans';
import {useThemeStore} from '@/store/modules/theme';
import {useSvgIcon} from '@/hooks/common/icon';
import {$t} from '@/locales';
import {useLoading} from '~/packages/hooks';
import WaveSurfer from 'wavesurfer.js';

defineOptions({
  name: 'VideoTransCreate'
});

const emit = defineEmits<{
  (e: 'projectCreated'): void;
}>();

const {SvgIconVNode} = useSvgIcon();

interface Props {
  worldLanguageC: Api.Common.WorldLanguage[];
  sysVoiceC: Api.Common.SysVoice[];
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', {
  default: false
});
const {loading, startLoading, endLoading} = useLoading();

const okStep = ref(0); // 已经ok的步骤数
const nextButtonEnabled = ref(false);
const prevButtonEnabled = ref(false);
const postButtonEnabled = ref(false);

const currentRef = ref<number>(1);
const currentStatus = ref<StepsProps['status']>('process');

function nextStep() {
  if (currentRef.value < 2) {
    currentRef.value++;
  } else {
    nextButtonEnabled.value = false;
  }

  if (currentRef.value > 1) {
    prevButtonEnabled.value = true;
  }

  if (okStep.value >= currentRef.value) {
    nextButtonEnabled.value = true;
  } else {
    nextButtonEnabled.value = false;
  }
}

function prevStep() {
  if (currentRef.value > 1) {
    currentRef.value--;
  }

  if (currentRef.value <= 1) {
    prevButtonEnabled.value = false;
  }

  if (okStep.value >= currentRef.value) {
    nextButtonEnabled.value = true;
  }
  // nextButtonEnabled.value = true;
}

const fileListRef = ref<UploadFileInfo[]>();

function handleUploadChange(data: { fileList: UploadFileInfo[] }) {
  // 如果文件列表长度大于1，只保留第一个文件
  if (data.fileList.length > 1) {
    data.fileList.shift(); // 删除索引1之后的所有元素，只保留第一个
  }
  fileListRef.value = data.fileList;
}

type Model = Omit<
  Api.VideoTrans.VideoTransProjectAddParams,
  'is_lipsync' | 'remove_bgm' | 'is_subtitles' | 'is_video_speed' | 'output_original_video'
> & {
  is_lipsync: boolean;
  remove_bgm: boolean;
  is_subtitles: boolean;
  is_video_speed: boolean;
  output_original_video: boolean;
  thumbnail: string;
  title: string;
  video_duration: number;
  start_time: number;
  end_time: number;
  video_file: File;
};

const projectAddParams = reactive<Model>({
  language_source_code: '',
  language_target_code: null,
  video_url: '',
  video_attachment_id: 0,
  subtitle_attachment_id: 0,
  is_lipsync: true,
  remove_bgm: false,
  is_subtitles: false,
  is_video_speed: true,
  output_original_video: false,
  sys_voice_id: 1,
  clone_voice_id: null,
  group_id: 0,
  thumbnail: '',
  title: '',
  video_duration: 0,
  start_time: 0,
  end_time: 0,
  file: null
});


// 显示免费尝试次数
const showFreeCount = ref(false);
const tryCount = reactive({
  free_count: 0,
  sum_count: 0,
  max_second: 0
});

const loadingBar = useLoadingBar();
let avCvs = null;
const videoUrl = ref<string>('');
const cutRegions = reactive({
  start_time: 0,
  end_time: 0
});

let uploadVideo = null;
async function customRequest({file, headers}: UploadCustomRequestOptions) {
  const video = document.createElement('video');
  video.src = URL.createObjectURL(file.file);
  videoUrl.value = video.src;

  uploadVideo = file.file;
  video.onloadedmetadata = async () => {
    projectAddParams.title = file.name;
    projectAddParams.video_duration = Number.parseFloat(video.duration.toFixed(2)); // 单位：秒

    cutRegions.start_time = 0;
    cutRegions.end_time = projectAddParams.video_duration;

    // 2. 提取封面（例如第1秒的帧）
    const coverBlob = await extractVideoFrame(file.file, 0.2);
    if (coverBlob) {
      // coverImg.src = URL.createObjectURL(coverBlob);
      projectAddParams.thumbnail = URL.createObjectURL(coverBlob);
    }
  };

  nextStep();
  // 第一步完成
  okStep.value = 1;
}

// 提取视频某一时刻的帧（返回 Blob）
async function extractVideoFrame(file, timeInSeconds = 1) {
  return new Promise(resolve => {
    const video = document.createElement('video');
    video.muted = true;
    video.crossOrigin = 'anonymous';

    const url = URL.createObjectURL(file);
    video.src = url;

    video.onloadeddata = () => {
      // 确保视频可seek（某些格式需等待 canplay）
      video.currentTime = timeInSeconds;
    };

    video.onseeked = () => {
      // 绘制当前帧到 canvas
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // 转为 PNG Blob
      canvas.toBlob(blob => {
        URL.revokeObjectURL(url);
        resolve(blob);
      }, 'image/png', 0.8);
    };

    video.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(null);
    };
  });
}

const isPlay = ref(false);

function playVideo() {
  if (isPlay.value) {
    avCvs.pause();
    isPlay.value = false;
  } else {
    avCvs.play({start: 0, end: projectAddParams.video_duration * 1000 * 1000});
    isPlay.value = true;
  }
}

const showCutVideoModal = ref(false);
const waveSurfer = ref<WaveSurfer>();
const tmpCutRegions = reactive({
  start_time: 0,
  end_time: 0
});

// 剪切视频
function cutVideo() {
  showCutVideoModal.value = true;

  const regions = RegionsPlugin.create();
  regions.on('region-updated', (region) => {
    console.log('Updated region', region);

    tmpCutRegions.start_time = Number.parseFloat(region.start.toFixed(2));
    tmpCutRegions.end_time = Number.parseFloat(region.end.toFixed(2));
  });

  // 清空
  projectAddParams.start_time = 0;
  projectAddParams.end_time = 0;

  nextTick(() => {
    const container = document.querySelector('#waveform');
    if (container) {
      waveSurfer.value = WaveSurfer.create({
        container: '#waveform',
        waveColor: '#C1BCBCFF',
        progressColor: '#4098fc',
        cursorColor: '#115fcf',
        cursorWidth: 4,
        media: document.querySelector('video'),
        height: 30,
        plugins: [regions],
      });

      waveSurfer.value.on('decode', () => {
        const regionParams = {
          start: cutRegions.start_time,
          end: cutRegions.end_time,
          resize: true,
          minLength: 1,
          maxLength: 999999,
          color: 'rgba(139,195,255,0.3)'
        };

        if (showFreeCount.value) {
          regionParams.maxLength = tryCount.max_second;
          regionParams.end = tryCount.max_second;

          if (cutRegions.end_time > tryCount.max_second) {
            cutRegions.end_time = tryCount.max_second;
          }
        }

        regions.addRegion(regionParams);
      });
    }
  });
}

// 确定剪切视频时间范围
function cutVideoConfirm() {
  cutRegions.start_time = tmpCutRegions.start_time;
  cutRegions.end_time = tmpCutRegions.end_time;

  projectAddParams.start_time = cutRegions.start_time;
  projectAddParams.end_time = cutRegions.end_time;

  showCutVideoModal.value = false;
}

function languageTargetCodeChange() {
  // okStep.value = 2;
  // postButtonEnabled.value = true;
  if (projectAddParams.language_target_code === null || projectAddParams.language_target_code.length === 0) {
    postButtonEnabled.value = false;
  } else {
    postButtonEnabled.value = true;
  }
}

async function postAdd() {
  // projectAdd(projectAddParams);
  console.log('postAdd', projectAddParams);

  loadingBar.start();
  postButtonEnabled.value = false;
  startLoading();

  const {error, data} = await projectAdd({
    ...projectAddParams,
    is_lipsync: projectAddParams.is_lipsync ? 1 : 0,
    remove_bgm: projectAddParams.remove_bgm ? 1 : 0,
    is_subtitles: projectAddParams.is_subtitles ? 1 : 0,
    is_video_speed: projectAddParams.is_video_speed ? 1 : 0,
    output_original_video: projectAddParams.output_original_video ? 1 : 0,
    video_file: uploadVideo
  });

  postButtonEnabled.value = true;
  endLoading();
  if (error) {
    loadingBar.error();
    // window.$message?.error('创建失败，请再试一次');
    return;
  }

  console.log(data);
  visible.value = false;
  window.$message?.success('提交成功');

  // 触发项目创建成功的事件
  emit('projectCreated');
  loadingBar.finish();
}

const formRef = ref<FormInst | null>(null);
const rules = {
  language_target_code: {
    required: true,
    message: '请选择目标语言'
  }
};

const worldLanguageOptions = ref<SelectOption[]>([]);
const videoTargetLanguageOptions = ref<SelectOption[]>([]);
const sysVoiceOptions = ref<SelectOption[]>([]);
const userVoiceOptions = ref<SelectOption[]>([]);

props.worldLanguageC.forEach(item => {
  worldLanguageOptions.value.push({
    label: `${item.name} (${item.self_name})`,
    value: item.language_code
  });

  if (item.video_trans_target === 1) {
    videoTargetLanguageOptions.value.push({
      label: `${item.name} (${item.self_name})`,
      value: item.language_code
    });
  }
});

// 播放状态管理
const currentPlayIndex = ref('');
const playStates = ref<Record<boolean>>({});
const playIndex = ref('');
const audio = new Audio();

// 播放结束
audio.addEventListener('ended', () => {
  playStates.value[currentPlayIndex.value] = false;
  currentPlayIndex.value = '';
});

/**
 * 播放音频
 * @param option
 * @param type sys | user
 */
function playAudio(option: SelectOption, type: 'sys' | 'user') {
  playIndex.value = `${option.value}_${type}`;
  audio.pause();
  if (currentPlayIndex.value === playIndex.value) {
    playStates.value[playIndex.value] = false;
    currentPlayIndex.value = '';
  } else {
    playStates.value[currentPlayIndex.value] = false;
    playStates.value[playIndex.value] = true;
    currentPlayIndex.value = playIndex.value;

    audio.src = option.audio_src;
    audio.play();
  }
}

const themeStore = useThemeStore();

function getPlayIcon(option: SelectOption, type: 'sys' | 'user') {
  const state = playStates.value[`${option.value}_${type}`];

  const icon = reactive({
    icon: 'ic:baseline-play-arrow',
    fontSize: 18,
    color: '#000'
  });

  if (state) {
    icon.icon = 'ic:baseline-pause';
    icon.color = themeStore.themeColor;
  }

  return icon;
}

/**
 * 渲染下拉选项
 * @param option 选项
 * @param type sys | user
 */
function renderVoiceOptionsLabel(option: SelectOption, type: 'sys' | 'user'): VNodeChild {
  return h(
    'div',
    {
      class: 'flex justify-center items-center w-full'
    },
    [
      h(
        NPopover,
        {
          trigger: 'hover',
          placement: 'top'
        },
        {
          trigger: () =>
            h(
              NButton,
              {
                text: true,
                size: 'small',
                onClick: (e: MouseEvent) => {
                  e.stopPropagation();
                  e.preventDefault();
                  playAudio(option, type);
                }
              },
              {
                default: () => h(SvgIconVNode(getPlayIcon(option, type)))
              }
            ),
          default: () => '点击试听'
        }
      ),

      h(
        'span',
        {
          class: 'ml-8px'
        },
        option.label as string
      )
    ]
  );
}

/**
 * 渲染选中的选项
 * @param option
 */
const renderVoiceOptionsTag: SelectRenderTag = ({option}) => {
  return h(
    'div',
    {
      style: {
        display: 'inline-flex',
        alignItems: 'center'
      }
    },
    [h('span', {}, option.label as string)]
  );
};

props.sysVoiceC.map(item => {
  sysVoiceOptions.value.push({
    label: item.name,
    value: item.id,
    audio_src: item.url
  });
});

const isGetUserVoice = ref(false);
const userVoiceLoading = ref(false);


onMounted(async () => {

});
</script>

<template>
  <NModal
    v-model:show="visible"
    preset="card"
    class="h-700px min-h-700px min-w-900px w-50%"
    :title="$t('page.ai.project.createdVideoTranslate')"
    :mask-closable="false"
  >
    <div v-show="showFreeCount" class="text-red-4  mb-20px">免费账号最长支持 {{ tryCount.max_second }} 秒的视频。</div>
    <NFlex vertical class="h-full">
      <div class="flex-0 h-40px">
        <NSteps :current="currentRef as number" :status="currentStatus" size="small">
          <NStep :title="$t('page.ai.project.uploadVideoFile')"></NStep>
          <NStep :title="$t('page.ai.project.selectParams')"></NStep>
        </NSteps>
      </div>
      <div class="flex-1">
        <NSpin :show="loading">
          <div v-show="currentRef === 1" class="h-full">
            <NUpload
              v-model:file-list="fileListRef"
              :show-file-list="false"
              :custom-request="customRequest"
              directory-dnd
              accept="video/*"
              @change="handleUploadChange"
            >
              <NUploadDragger class="h-380px">
                <div class="mb-12px">
                  <NImage
                    v-if="projectAddParams.thumbnail"
                    :preview-disabled="true"
                    width="300"
                    height="150"
                    :src="projectAddParams.thumbnail"
                  />
                  <NIcon v-else :depth="3" size="48">
                    <SvgIcon icon="ic:baseline-cloud-upload" size="60"/>
                  </NIcon>
                </div>

                <NText class="text-16px">
                  {{ projectAddParams.title ? projectAddParams.title : $t('page.ai.project.uploadVideoFileTips1') }}
                </NText>
                <NP class="py-0 pb-0 pt-8px" depth="3">{{ $t('page.ai.project.uploadVideoFileTips2') }}</NP>
                <NP class="py-0 pb-0 pt-8px" depth="3">注意事项：面部表情清晰，带有高质量口播音频，避免多人出镜。</NP>
                <NP v-if="showFreeCount" depth="3" class="mt-1px text-red-4">
                  本月可免费试用 {{ tryCount.free_count }} 次，视频长度{{ tryCount.max_second }}秒内。
                </NP>
              </NUploadDragger>
            </NUpload>
          </div>

          <div v-show="currentRef === 2" class="h-full">
            <NForm ref="formRef" :label-width="80" :rules="rules" :model="projectAddParams">
              <NFlex>
                <div class="flex-1">
                  <NFormItem label="原视频语言">
                    <NSelect
                      v-model:value="projectAddParams.language_source_code"
                      :options="worldLanguageOptions"
                      clearable
                      filterable
                      placeholder="自动识别视频语言"
                    />
                  </NFormItem>

                  <NEllipsis class="h-40px text-20px/40px !w-450px">
                    {{ projectAddParams.title }}
                  </NEllipsis>
                  <NText class="h-30px text-14px/30px">视频时长：{{ projectAddParams.video_duration }} 秒</NText>
                </div>

                <div class="flex-1 pl-10px">
                  <NFormItem label="目标视频语言" rule-path="language_target_code">
                    <NSelect
                      v-model:value="projectAddParams.language_target_code"
                      :max-tag-count="1"
                      multiple
                      placeholder="请选择目标语言"
                      filterable
                      clearable
                      :options="videoTargetLanguageOptions"
                      @update:value="languageTargetCodeChange"
                      @clear="languageTargetCodeChange"
                    />
                  </NFormItem>
                  <NFormItem>
                    <template #label>
                      <NText>系统语音</NText>
                      <NPopover trigger="hover">
                        <template #trigger>
                          <NIcon size="14" class="ml-5px">
                            <SvgIcon icon="ic:outline-help"/>
                          </NIcon>
                        </template>
                        <span>系统预设的语音，使用选中的系统语音配音。</span>
                      </NPopover>
                    </template>
                    <NSelect
                      v-model:value="projectAddParams.sys_voice_id"
                      :options="sysVoiceOptions"
                      placeholder="请选系统语音"
                      filterable
                      clearable
                      :render-label="option => renderVoiceOptionsLabel(option, 'sys')"
                      :render-tag="renderVoiceOptionsTag"
                      @update:value="languageTargetCodeChange"
                      @clear="languageTargetCodeChange"
                    />
                  </NFormItem>
                  <NFormItem>
                    <template #label>
                      <NText>我的语音</NText>
                      <NPopover trigger="hover">
                        <template #trigger>
                          <NIcon size="14" class="ml-5px">
                            <SvgIcon icon="ic:outline-help"/>
                          </NIcon>
                        </template>
                        <span>我的语音，将优先使用此处选中的语音。</span>
                      </NPopover>
                    </template>

                    <NSelect
                      v-model:value="projectAddParams.clone_voice_id"
                      :loading="userVoiceLoading"
                      placeholder="请选我的语音"
                      filterable
                      clearable
                      :options="userVoiceOptions"
                      :render-label="option => renderVoiceOptionsLabel(option, 'user')"
                      :render-tag="renderVoiceOptionsTag"
                      @update:value="languageTargetCodeChange"
                    />
                  </NFormItem>
                  <NGrid :cols="2" :y-gap="8" class="mt-10px">
                    <NGi>
                      <NSwitch v-model:value="projectAddParams.is_lipsync"/>
                      口型同步
                      <NPopover trigger="hover">
                        <template #trigger>
                          <NIcon size="14">
                            <SvgIcon icon="ic:outline-help"/>
                          </NIcon>
                        </template>
                        <span>视频中的语音口型会自动同步到视频中。</span>
                      </NPopover>
                    </NGi>
                    <NGi>
                      <NSwitch v-model:value="projectAddParams.remove_bgm"/>
                      移除背景音乐
                    </NGi>
                    <NGi>
                      <NSwitch v-model:value="projectAddParams.is_subtitles"/>
                      启用字幕
                      <NPopover trigger="hover">
                        <template #trigger>
                          <NIcon size="14">
                            <SvgIcon icon="ic:outline-help"/>
                          </NIcon>
                        </template>
                        <span>按翻译后的声音重新生成字幕。</span>
                      </NPopover>
                    </NGi>
                    <NGi>
                      <NSwitch v-model:value="projectAddParams.is_video_speed"/>
                      动态调整时长
                      <NPopover trigger="hover">
                        <template #trigger>
                          <NIcon size="14">
                            <SvgIcon icon="ic:outline-help"/>
                          </NIcon>
                        </template>
                        <span>通过调整视频时长来提升配音效果，关闭后将保持原时长。</span>
                      </NPopover>
                    </NGi>
                  </NGrid>
                </div>
              </NFlex>
            </NForm>
          </div>
        </NSpin>
      </div>
    </NFlex>

    <template #footer>
      <NFlex justify="space-around" size="large">
        <NButton :disabled="!prevButtonEnabled" type="primary" @click="prevStep">
          {{ $t('common.previousStep') }}
        </NButton>

        <NButton v-if="currentRef < 2" :disabled="!nextButtonEnabled" type="primary" @click="nextStep">
          {{ $t('common.nextStep') }}
        </NButton>
        <NButton v-else :disabled="!postButtonEnabled" type="primary" @click="postAdd">
          {{ $t('common.create') }}
        </NButton>
      </NFlex>
    </template>
  </NModal>

  <NModal
    v-model:show="showCutVideoModal"
    preset="card"
    class="h-700px min-h-700px min-w-900px w-50%"
    content-class="h-full overflow-y-auto"
    :mask-closable="false"
  >
    <template #header>
      <NText>剪辑视频</NText>
      <NPopover trigger="hover">
        <template #trigger>
          <NIcon size="14">
            <SvgIcon icon="ic:outline-help"/>
          </NIcon>
        </template>
        <span>可选择视频时间片段进行翻译。</span>
      </NPopover>
    </template>
    <video
      :src="videoUrl"
      controls
      playsinline
      style="width: 100%; margin: 0 auto; display: block;"
    />
    <div class="mt-10px h-20px text-center">
      剪辑范围：{{ tmpCutRegions.start_time }} - {{ tmpCutRegions.end_time }}秒 视频总时长：{{ projectAddParams.video_duration }}
      秒
    </div>
    <div id="waveform" class=" mt-10px h-30px border-red-2 border-1"></div>

    <NFlex justify="space-between" class="mt-10px">
      <NButton type="default" @click="showCutVideoModal = false">
        返回
      </NButton>
      <NButton type="primary" @click="cutVideoConfirm">
        确定
      </NButton>
    </NFlex>
  </NModal>
</template>

<style scoped></style>
