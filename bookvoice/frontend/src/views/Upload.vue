<template>
  <div>
    <el-radio-group v-model="outputMode" style="margin-bottom: 20px">
      <el-radio label="single">独立MP3</el-radio>
      <el-radio label="merged">合并MP3</el-radio>
    </el-radio-group>

    <el-upload
      ref="uploadRef"
      drag
      :auto-upload="false"
      :on-change="handleFileChange"
      :file-list="fileList"
      multiple
      accept=".png,.jpg,.jpeg,.pdf,.docx"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">拖拽文件或点击上传</div>
      <template #tip>
        <div class="el-upload__tip">支持 PNG, JPG, PDF, DOCX 格式</div>
      </template>
    </el-upload>

    <el-button type="primary" @click="submitUpload" :loading="uploading">开始上传</el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadFiles } from '../api'

const emit = defineEmits(['uploaded'])

const uploadRef = ref()
const fileList = ref([])
const outputMode = ref('single')
const uploading = ref(false)

const handleFileChange = (file, files) => {
  fileList.value = files
}

const submitUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  const formData = new FormData()
  formData.append('output_mode', outputMode.value)
  fileList.value.forEach(file => {
    formData.append('files', file.raw)
  })

  try {
    await uploadFiles(formData)
    ElMessage.success('上传成功')
    fileList.value = []
    emit('uploaded')
  } catch (e) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}
</script>
