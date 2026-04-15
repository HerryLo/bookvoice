<template>
  <div>
    <el-button @click="refreshTasks" :loading="loading">刷新</el-button>
    <el-table :data="tasks" stripe style="width: 100%; margin-top: 20px">
      <el-table-column prop="filename" label="文件名" width="200" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="output_mode" label="输出模式" width="100" />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'completed'"
            type="primary"
            size="small"
            @click="downloadFile(row.id)"
          >下载</el-button>
          <el-button
            v-if="row.status === 'failed'"
            type="warning"
            size="small"
            @click="retryTask(row.id)"
          >重试</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getTasks, downloadTask, retryTask as retryTaskApi } from '../api'

const tasks = ref([])
const loading = ref(false)

const getStatusType = (status) => {
  const types = { pending: 'info', processing: 'warning', completed: 'success', failed: 'danger' }
  return types[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = { pending: '待处理', processing: '处理中', completed: '已完成', failed: '失败' }
  return labels[status] || status
}

const refreshTasks = async () => {
  loading.value = true
  try {
    const { data } = await getTasks()
    tasks.value = data
  } catch (e) {
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

const downloadFile = async (taskId) => {
  try {
    const { data } = await downloadTask(taskId)
    const url = window.URL.createObjectURL(new Blob([data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${taskId}.mp3`
    link.click()
  } catch (e) {
    ElMessage.error('下载失败')
  }
}

const retryTask = async (taskId) => {
  try {
    await retryTaskApi(taskId)
    ElMessage.success('任务已重新提交')
    refreshTasks()
  } catch (e) {
    ElMessage.error('重试失败')
  }
}

onMounted(refreshTasks)
</script>
