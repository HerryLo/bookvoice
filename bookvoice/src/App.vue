<template>
  <div id="app">
    <el-container>
      <el-header>
        <h1>BookVoice - 图文转语音系统</h1>
      </el-header>
      <el-main>
        <el-tabs v-model="activeTab">
          <el-tab-pane label="任务列表" name="tasks">
            <TaskList />
          </el-tab-pane>
          <el-tab-pane label="上传文件" name="upload">
            <Upload @uploaded="onUploaded" />
          </el-tab-pane>
          <el-tab-pane label="日志查看" name="logs">
            <Logs />
          </el-tab-pane>
        </el-tabs>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import TaskList from './views/TaskList.vue'
import Upload from './views/Upload.vue'
import Logs from './views/Logs.vue'

const activeTab = ref('tasks')

const onUploaded = () => {
  activeTab.value = 'tasks'
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
}
.el-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
}
.el-header h1 {
  margin: 0;
}
</style>
