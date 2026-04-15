<template>
  <div>
    <el-button @click="loadLogs" :loading="loading">刷新日志</el-button>
    <el-table :data="logFiles" stripe style="width: 100%; margin-top: 20px">
      <el-table-column prop="filename" label="日志文件" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button type="text" @click="viewLog(row.filename)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="日志详情" width="60%">
      <pre style="max-height: 400px; overflow-y: auto;">{{ logContent }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getLogs, getLogContent } from '../api'

const logFiles = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const logContent = ref('')

const loadLogs = async () => {
  loading.value = true
  try {
    const { data } = await getLogs()
    logFiles.value = data
  } catch (e) {
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

const viewLog = async (filename) => {
  logContent.value = '日志内容加载中...'
  dialogVisible.value = true
  try {
    const { data } = await getLogContent(filename)
    logContent.value = data.content || '日志为空'
  } catch (e) {
    logContent.value = '加载日志失败: ' + (e.message || '未知错误')
  }
}

onMounted(loadLogs)
</script>
