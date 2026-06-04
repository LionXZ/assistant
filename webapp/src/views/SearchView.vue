<template>
  <div class="search-layout">
    <div class="search-header">
      <h2>知识库检索</h2>
      <p class="subtitle">搜索编程文档、最佳实践和设计模式</p>
      <div class="search-bar">
        <el-input
          v-model="query"
          size="large"
          placeholder="输入关键词搜索知识库..."
          clearable
          @keydown.enter="doSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" size="large" @click="doSearch" :loading="loading">
          搜索
        </el-button>
      </div>
    </div>

    <div class="search-results">
      <el-empty v-if="!searched" description="输入关键词搜索知识库" />
      <el-empty v-else-if="results.length === 0 && !loading" description="未找到相关结果" />
      <div v-else class="result-list">
        <div v-for="(r, i) in results" :key="i" class="result-card">
          <div class="result-num">{{ i + 1 }}</div>
          <div class="result-body">
            <div class="result-source">{{ r.source }}</div>
            <div class="result-content" v-html="r.html" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { chat } from '../api/chat'
import { Search } from '@element-plus/icons-vue'

const query = ref('')
const loading = ref(false)
const searched = ref(false)
const results = ref([])

async function doSearch() {
  const q = query.value.trim()
  if (!q || loading.value) return

  loading.value = true
  searched.value = true
  results.value = []

  try {
    const res = await chat(q, 'search-' + Date.now())
    // 解析回复中的定位信息
    const html = res.content
      .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
      .replace(/\n/g, '<br>')

    results.value = [{ source: 'AI 回答', html }]
  } catch (e) {
    results.value = [{ source: '错误', html: '请求失败: ' + e.message }]
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.search-layout { height: 100%; display: flex; flex-direction: column; }
.search-header {
  text-align: center;
  padding: 40px 24px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}
.search-header h2 { font-size: 24px; margin-bottom: 6px; }
.subtitle { font-size: 14px; opacity: .85; margin-bottom: 24px; }
.search-bar {
  display: flex;
  gap: 12px;
  max-width: 640px;
  margin: 0 auto;
}
.search-bar :deep(.el-input__wrapper) {
  background: rgba(255,255,255,.95);
}
.search-results {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f5f7fa;
}
.result-list { max-width: 800px; margin: 0 auto; }
.result-card {
  display: flex;
  gap: 16px;
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.result-num {
  width: 32px; height: 32px;
  background: #409eff;
  color: #fff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}
.result-source {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}
.result-content {
  font-size: 14px;
  line-height: 1.8;
  color: #333;
}
.result-content :deep(pre) {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
  font-size: 13px;
}
.result-content :deep(code) {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}
</style>
