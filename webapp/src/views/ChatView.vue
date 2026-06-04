<template>
  <div class="chat-layout">
    <!-- 侧边栏 — 会话列表 -->
    <aside class="chat-sidebar">
      <div class="sidebar-head">
        <el-button type="primary" size="small" @click="newChat" :icon="Plus">
          新对话
        </el-button>
      </div>
      <div class="sidebar-list">
        <div
          v-for="t in threads"
          :key="t.id"
          class="thread-item"
          :class="{ active: t.id === currentThread }"
          @click="switchThread(t.id)"
        >
          <el-icon><ChatLineSquare /></el-icon>
          <span class="thread-title">{{ t.title }}</span>
          <span class="thread-time">{{ t.time }}</span>
        </div>
      </div>
    </aside>

    <!-- 主对话区 -->
    <section class="chat-main">
      <!-- 消息列表 -->
      <div class="msg-list" ref="msgListRef">
        <div v-if="messages.length === 0" class="empty-hint">
          <el-icon :size="48"><ChatDotRound /></el-icon>
          <p>开始和 DevAssistant 对话吧</p>
          <div class="quick-prompts">
            <el-tag
              v-for="p in quickPrompts"
              :key="p"
              class="prompt-tag"
              @click="send(p)"
            >
              {{ p }}
            </el-tag>
          </div>
        </div>

        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="msg-item"
          :class="msg.role"
        >
          <div class="msg-avatar">
            <el-icon v-if="msg.role === 'user'" :size="20"><User /></el-icon>
            <el-icon v-else :size="20"><Monitor /></el-icon>
          </div>
          <div class="msg-body">
            <div class="msg-role">{{ msg.role === 'user' ? '你' : 'DevAssistant' }}</div>
            <div class="msg-content" v-html="renderContent(msg.content)" />
            <!-- 工具调用 -->
            <div v-if="msg.toolCalls" class="tool-calls">
              <el-collapse>
                <el-collapse-item
                  v-for="(tc, ti) in msg.toolCalls"
                  :key="ti"
                  :title="'🔧 ' + tc.name"
                >
                  <div class="tool-result">{{ tc.result }}</div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
        </div>

        <!-- 加载动画 -->
        <div v-if="loading" class="msg-item assistant">
          <div class="msg-avatar"><el-icon :size="20"><Monitor /></el-icon></div>
          <div class="msg-body">
            <div class="typing-dots"><span></span><span></span><span></span></div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="msg-input">
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          placeholder="输入你的问题，Enter 发送，Shift+Enter 换行"
          resize="none"
          @keydown.enter.exact.prevent="send(input)"
          :disabled="loading"
        />
        <div class="input-actions">
          <span class="thread-id">会话: {{ currentThread }}</span>
          <el-button
            type="primary"
            size="small"
            @click="send(input)"
            :loading="loading"
            :disabled="!input.trim()"
          >
            发送
          </el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { streamChat } from '../api/chat'

// ---- 状态 ----
const input = ref('')
const loading = ref(false)
const currentThread = ref('default')
const messages = ref([])
const msgListRef = ref(null)

const threads = ref([
  { id: 'default', title: '默认会话', time: new Date().toLocaleTimeString() },
])

const quickPrompts = [
  'Python 装饰器原理是什么？',
  '分析 src/tools/code_tools.py 代码',
  'Go 语言错误处理最佳实践',
  '列出自定义工具项目结构',
]

// ---- 方法 ----
function newChat() {
  const id = 'thread-' + Date.now()
  threads.value.unshift({
    id,
    title: '新会话 ' + threads.value.length,
    time: new Date().toLocaleTimeString(),
  })
  currentThread.value = id
  messages.value = []
}

function switchThread(id) {
  currentThread.value = id
  messages.value = []
}

async function send(text) {
  const msg = text.trim()
  if (!msg || loading.value) return

  input.value = ''

  // 用户消息
  messages.value.push({ role: 'user', content: msg })

  // assistant 消息占位
  const aiIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '', toolCalls: [] })

  // 滚动到底部
  await nextTick()
  scrollBottom()

  loading.value = true

  try {
    let buffer = ''
    let toolBuffer = ''
    let currentToolName = ''

    for await (const chunk of streamChat(msg, currentThread.value)) {
      // 工具调用标记
      if (chunk.startsWith('🔧')) {
        toolBuffer = ''
        currentToolName = chunk.replace('🔧 **[调用工具: ', '').replace(']**\n', '').trim()
        continue
      }
      // 工具返回
      if (chunk.startsWith('\n📋')) {
        const toolResult = toolBuffer
        messages.value[aiIdx].toolCalls.push({
          name: currentToolName,
          result: toolResult.slice(0, 500),
        })
        toolBuffer = ''
        continue
      }

      // 在工具输出区
      if (currentToolName && !chunk.startsWith('\n📋')) {
        toolBuffer += chunk
        continue
      }

      // 正常文本
      buffer += chunk
      messages.value[aiIdx].content = buffer
      await nextTick()
      scrollBottom()
    }
  } catch (e) {
    messages.value[aiIdx].content = '出错了: ' + e.message
  } finally {
    loading.value = false
    currentToolName = ''
    toolBuffer = ''
  }
}

function scrollBottom() {
  if (msgListRef.value) {
    msgListRef.value.scrollTop = msgListRef.value.scrollHeight
  }
}

/**
 * 简单渲染：`` ` `` 代码块 → <pre><code>, 换行 → <br>
 */
function renderContent(text) {
  if (!text) return ''
  return text
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/\n/g, '<br>')
}

watch(currentThread, () => nextTick(scrollBottom))
</script>

<style scoped>
.chat-layout { display: flex; height: 100%; }
/* ---- 侧边栏 ---- */
.chat-sidebar {
  width: 220px;
  background: #f7f8fa;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}
.sidebar-head { padding: 12px; }
.sidebar-list { flex: 1; overflow-y: auto; }
.thread-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  font-size: 13px;
  border-left: 3px solid transparent;
}
.thread-item:hover { background: #ecf5ff; }
.thread-item.active {
  background: #ecf5ff;
  border-left-color: #409eff;
  color: #409eff;
}
.thread-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.thread-time { font-size: 11px; color: #999; }

/* ---- 主区 ---- */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
}
.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
.empty-hint {
  text-align: center;
  margin-top: 120px;
  color: #aaa;
}
.empty-hint p { margin: 12px 0; font-size: 15px; }
.quick-prompts { margin-top: 16px; display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.prompt-tag { cursor: pointer; font-size: 13px; }
.prompt-tag:hover { background: #409eff; color: #fff; }

/* 消息 */
.msg-item {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  max-width: 85%;
}
.msg-item.user { margin-left: auto; flex-direction: row-reverse; }
.msg-avatar {
  width: 36px; height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.msg-item.user .msg-avatar { background: #409eff; color: #fff; }
.msg-item.assistant .msg-avatar { background: #e6f7ff; color: #409eff; }
.msg-role { font-size: 12px; color: #999; margin-bottom: 4px; }
.msg-item.user .msg-role { text-align: right; }
.msg-content {
  background: #f0f2f5;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.7;
  font-size: 14px;
  word-break: break-word;
}
.msg-item.user .msg-content { background: #409eff; color: #fff; }
.msg-content :deep(pre) {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
  font-size: 13px;
  line-height: 1.5;
}
.msg-content :deep(code) {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

/* 工具调用 */
.tool-calls { margin-top: 8px; }
.tool-result {
  font-size: 12px;
  color: #666;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  background: #fafafa;
  padding: 8px;
  border-radius: 4px;
}

/* 输入区 */
.msg-input {
  border-top: 1px solid #e4e7ed;
  padding: 16px 24px;
  background: #fafafa;
}
.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.thread-id { font-size: 12px; color: #bbb; }

/* 打字动画 */
.typing-dots { display: flex; gap: 6px; padding: 8px 0; }
.typing-dots span {
  width: 8px; height: 8px;
  background: #bbb;
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite both;
}
.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
