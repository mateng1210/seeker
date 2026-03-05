<script setup lang="tsx">
import {h, onMounted, reactive, ref} from 'vue';
import {NButton, NIcon, NPopover, NSpace, NTag, useDialog} from 'naive-ui';
import { runStatusRecord } from '@/constants/business';
import {fetchJobsPage, fetchJobView} from "@/service/api/jobs";
import { useTable } from '@/hooks/common/table';
import { useSvgIcon } from '@/hooks/common/icon';
import {localStg} from '@/utils/storage';
import VideoTransCreate from '@/views/video/video-translate/modules/vt-create-modal.vue';
import { $t } from '@/locales';
import SvgIcon from '@/components/custom/svg-icon.vue';
import JobSearch from "@/views/jobs/modules/vt-search.vue";
import ViewJobPage from "@/views/jobs/modules/vt-view-job-drawer.vue";

const { SvgIconVNode } = useSvgIcon();

const dialog = useDialog();

const currentPage = ref(1);
const pageNum = ref(10);

const { pagination, data, getData, getDataByPage, loading, searchParams, resetSearchParams, columns } = useTable({
  apiFn: fetchJobsPage,
  showTotal: true,
  apiParams: {
    page: currentPage.value,
    num: pageNum.value,
    // if you want to use the searchParams in Form, you need to define the following properties, and the value is null
    // the value can not be undefined, otherwise the property in Form will not be reactive
    keyword: null
  },
  columns: () => [
    {
      title: 'ID',
      key: 'id',
      width: 60
    },
    {
      title: '岗位',
      key: 'title',
      minWidth: 200
    },
    {
      title: '技能',
      key: 'required_skills',
      minWidth: 200,
      render(row) {
        return h(
          NSpace,
          {
            size: 'small',
            wrap: true
          },
          {
            default: () => row.required_skills.map(skill => {
              return h(
                  NTag,
              {
                    size: 'small',
                    type: 'primary'
                },
                { default: () => skill }
              )
            })
          }
        )
      }
    },
    {
      title: '地址',
      key: 'location',
      minWidth: 200
    },
    {
      title: '学历',
      key: 'degree',
      width: 100
    },
    {
      title: '工作经验(年)',
      key: 'work_experience_min',
      width: 110,
      render(row) {
        return `${row.work_experience_min  } - ${  row.work_experience_max}`
      }
    },
    {
      title: '薪资',
      key: 'salary_min',
      width: 180,
      render(row) {
        return `${row.salary_min  } - ${  row.salary_max}`
      }
    },
    {
      title: '操作',
      minWidth: 200,
      key: 'actions',
      render(row) {
        return h('div', { style: 'display: flex; gap: 8px;' }, [
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              onClick: () => jobView(row.id)
            },
            { default: () => '查看' }
          ),
          // h(
          //   NButton,
          //   {
          //     size: 'small',
          //     type: 'warning',
          //     onClick: () => jobEdit(row.id)
          //   },
          //   { default: () => '编辑' }
          // ),
          // h(
          //   NButton,
          //   {
          //     size: 'small',
          //     type: 'error',
          //     onClick: () => jobDelete(row.id)
          //   },
          //   { default: () => '删除' }
          // )
        ])
      }
    },
  ]
});

const viewJobVisible = ref(false);
const viewJob = reactive({
  id: 0,
  title: '',
  location: '',
  degree: '',
  required_skills: [],
  job_responsibility: [],
  job_requirements: [],
  salary_min: 0,
  salary_max: 0,
  work_experience_min: 0,
  work_experience_max: 0,
  benefits: ''
});

async function jobView(job_id: number) {
  loading.value = true;

  const { data } = await fetchJobView(job_id);

  Object.assign(viewJob, data);
  viewJobVisible.value = true;
  loading.value = false;
}

function jobEdit(job_id:number) {

}

function jobDelete(job_id:number) {

}
</script>

<template>
  <NSpin :description="$t('common.loading')" :show="loading" class="h-full" content-class="h-full">
    <div class="min-h-500px flex-col-stretch gap-10px overflow-hidden lt-sm:overflow-auto h-full">
      <JobSearch v-model:model="searchParams" @reset="resetSearchParams" v-model:loading="loading" @search="getDataByPage"  />
      <NCard
        :bordered="false"
        size="small"
        class="h-full card-wrapper sm:flex-1-hidden"
        content-class="h-full overflow-y-auto"
      >
        <NFlex vertical class="h-full">
          <NScrollbar class="flex-1">
            <NEmpty class="mt-50px" v-if="data.length === 0" :description="$t('common.noData')" />

            <NDataTable v-else
              :columns="columns"
              :data="data"
              :bordered="false"
            />
          </NScrollbar>

          <NPagination
            v-model:page="currentPage"
            class="flex-0 h-30px flex justify-end"
            :item-count="pagination.itemCount"
            :page-sizes="pagination.pageSizes"
            :page-size="pageNum"
            show-size-picker
            @update:page="getDataByPage"
            @update:page-size="
            pageSize => {
              pagination.pageSize = pageSize;
              pageNum = pageSize;
              getDataByPage(1);
            }
          "
          >
            <template #prefix="{ itemCount }">
              共 {{ itemCount }} 项
            </template>
          </NPagination>
        </NFlex>
      </NCard>

<!--      <VideoTransCreate-->
<!--        v-if="createModalVisible"-->
<!--        v-model:visible="createModalVisible"-->
<!--        :sys-voice-c="sysVoice"-->
<!--        :world-language-c="worldLanguage"-->
<!--        @project-created="getData"-->
<!--      />-->

      <ViewJobPage
        v-if="viewJobVisible"
        ref="videoTransDrawerRef"
        v-model:visible="viewJobVisible"
        :viewJob-c="viewJob"
      />
    </div>
  </NSpin>
</template>

<style scoped>
/* 在 <style scoped> 中添加 */
.hide-border-input {
  --n-border: none;
  --n-border-hover: none;
  --n-border-focus: none;
  --n-border-bottom: 1px solid transparent;
  --n-border-bottom-hover: 1px solid #d1d5db;
  --n-border-bottom-focus: 1px solid #3b82f6;
  --n-box-shadow: none;
  --n-box-shadow-focus: none;
  --n-padding-left: 2px !important;
  background-color: transparent;
}

.hide-border-input:hover {
  --n-border-bottom: 1px solid #d1d5db;
}

.hide-border-input :deep(.n-input__input-el:focus) {
  border-bottom: 1px solid #3b82f6 !important;
}
</style>
