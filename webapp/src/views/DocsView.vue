<template>
  <div class="docs-layout">
    <!-- 上传区域 -->
    <div class="upload-zone" @click="triggerUpload">
      <el-icon :size="40"><UploadFilled /></el-icon>
      <p>点击或拖拽文件上传到知识库</p>
      <span class="upload-hint">支持 .txt .md .pdf，AI 自动分类到对应目录</span>

      <el-upload
        ref="uploadRef"
        :action="`${BASE}/rag/upload`"
        :auto-upload="false"
        :multiple="true"
        :show-file-list="false"
        :on-change="onFileChange"
        accept=".txt,.md,.pdf"
        style="display:none"
      >
        <div ref="uploadTrigger" />
      </el-upload>
    </div>

    <!-- 上传中提示 -->
    <div v-if="uploading" class="uploading-bar">
      <el-icon class="is-loading"><Loading /></el-icon> 正在上传和 AI 分类...
    </div>

    <!-- 文档目录树 -->
    <div class="docs-tree">
      <div class="tree-head">
        <h3>
          <el-icon><FolderOpened /></el-icon>
          文档目录 ({{ docs.length }} 个文件，{{ indexCount }} 片段已索引)
        </h3>
      </div>

      <el-empty v-if="!hasDocs" :image-size="80" description="暂无文档，上传 .txt .md .pdf 文件" />

      <div v-else class="tree-body">
        <div v-for="group in docGroups" :key="group.name" class="category-group">
          <div class="category-head">
            <el-icon><Folder /></el-icon>
            <span class="cat-name">{{ group.name }}</span>
            <el-tag size="small" round>{{ group.files.length }}</el-tag>
          </div>
          <div v-for="doc in group.files" :key="doc.fullpath" class="doc-row">
            <el-icon class="doc-icon"><Document /></el-icon>
            <span class="doc-name" :title="doc.fullpath">{{ doc.name }}</span>
            <span class="doc-path">{{ group.name }}</span>
            <el-button type="danger" link size="small" :icon="Delete" @click.stop="delDoc(doc.fullpath)" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { UploadFilled, Loading, FolderOpened, Folder, Document, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const BASE = '/api/v1'

const docs = ref([])
const indexCount = ref(0)
const uploading = ref(false)
const uploadRef = ref(null)

const hasDocs = computed(() => docs.value.length > 0)

const docGroups = computed(() => {
  const groups = {}
  for (const filepath of docs.value) {
    const parts = filepath.split('/')
    const category = parts.length > 1 ? parts[0] : '(未分类)'
    const name = parts[parts.length - 1]
    if (!groups[category]) groups[category] = []
    groups[category].push({ name, fullpath: filepath })
  }
  return Object.entries(groups).map(([name, files]) => ({ name, files }))
})

onMounted(fetchDocs)

async function fetchDocs() {
  try {
    const res = await fetch(`${BASE}/rag/documents`)
    const data = await res.json()
    docs.value = data.documents
    indexCount.value = data.indexed_count
  } catch {}
}

function triggerUpload() {
  uploadRef.value?.$el?.querySelector('input')?.click()
}

async function onFileChange(file) {
  uploading.value = true
  try {
    const form = new FormData()
    form.append('files', file.raw)
    const res = await fetch(`${BASE}/rag/upload`, { method: 'POST', body: form })
    const data = await res.json()

    if (data.uploaded > 0) {
      ElMessage.success(`已上传 ${data.uploaded} 个文件，新增 ${data.total_chunks} 个索引片段`)
    }
    if (data.errors.length > 0) {
      data.errors.forEach(e => ElMessage.warning(e))
    }
    await fetchDocs()
  } catch (e) {
    ElMessage.error('上传失败: ' + e.message)
  } finally {
    uploading.value = false
  }
}

async function delDoc(filepath) {
  try {
    await ElMessageBox.confirm(`确定删除「${filepath}」？`, '确认', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消',
    })
  } catch { return }

  try {
    await fetch(`${BASE}/rag/delete?filepath=${encodeURIComponent(filepath)}`, { method: 'POST' })
    ElMessage.success('已删除')
    await fetchDocs()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}
</script>

<style lang="scss" scoped>
$primary: #409eff;
$bg: #f5f7fa;
$border-dashed: #d3d6db;

.docs-layout {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: $bg;
}

.upload-zone {
  margin: 24px auto 0;
  width: 90%;
  max-width: 600px;
  padding: 40px;
  text-align: center;
  border: 2px dashed $border-dashed;
  border-radius: 16px;
  background: #fff;
  cursor: pointer;
  transition: border-color .2s, background .2s;

  &:hover {
    border-color: $primary;
    background: #ecf5ff;
  }

  p {
    margin: 12px 0 4px;
    font-size: 15px;
    color: #333;
  }
}

.upload-hint {
  font-size: 13px;
  color: #999;
}

.uploading-bar {
  text-align: center;
  padding: 12px;
  color: $primary;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.docs-tree {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 24px;
}

.tree-head {
  padding: 20px 0 12px;

  h3 {
    font-size: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: #333;
  }
}

.tree-body {
  max-width: 700px;
}

.category-group {
  margin-bottom: 16px;
}

.category-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  color: #333;
  box-shadow: 0 1px 3px rgba(0, 0, 0, .05);
}

.cat-name {
  flex: 1;
}

.doc-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px 8px 28px;
  font-size: 13px;
  color: #555;
  border-bottom: 1px solid #ebeef5;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: #ecf5ff;
    border-radius: 6px;
  }
}

.doc-icon {
  color: #909399;
}

.doc-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-path {
  font-size: 11px;
  color: #c0c4cc;
}
</style>
