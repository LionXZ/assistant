<template>
  <div class="chat-layout">
    <!-- 侧边栏 -->
    <aside class="chat-sidebar">
      <div class="sidebar-head">
        <el-button type="primary" size="small" @click="newChat" :icon="Plus">新对话</el-button>
      </div>
      <div class="sidebar-list">
        <div v-for="t in threads" :key="t.id"
          class="thread-item" :class="{ active: t.id === currentThread }"
          @click="switchThread(t.id)">
          <el-icon><ChatLineSquare /></el-icon>
          <span class="thread-title" :title="t.title">{{ t.title }}</span>
          <span class="thread-time">{{ t.time }}</span>
          <span class="thread-actions">
            <el-button link size="small" :icon="Edit" @click.stop="renameThread(t)" title="重命名" />
            <el-button link size="small" :icon="Delete" @click.stop="deleteThread(t)" title="删除" />
          </span>
        </div>
      </div>
    </aside>

    <!-- 主对话 -->
    <section class="chat-main">
      <div class="msg-list" ref="msgListRef">
        <div v-if="messages.length === 0" class="empty-hint">
          <el-icon :size="48"><ChatDotRound /></el-icon>
          <p>开始和 DevAssistant 对话吧</p>
          <div class="quick-prompts">
            <el-tag v-for="p in quickPrompts" :key="p" class="prompt-tag" @click="send(p)">{{ p }}</el-tag>
          </div>
        </div>

        <div v-for="(msg, i) in messages" :key="i" class="msg-item" :class="msg.role">
          <div class="msg-avatar">
            <el-icon v-if="msg.role === 'user'" :size="20"><User /></el-icon>
            <el-icon v-else :size="20"><Monitor /></el-icon>
          </div>
          <div class="msg-body">
            <div class="msg-role">{{ msg.role === 'user' ? '你' : 'DevAssistant' }}</div>
            <div class="msg-content" v-html="renderHtml(msg.content)" />
            <div v-if="msg.toolCalls && msg.toolCalls.length" class="tool-calls">
              <el-collapse>
                <el-collapse-item v-for="(tc, ti) in msg.toolCalls" :key="ti" :title="'🔧 ' + tc.name">
                  <div class="tool-result">{{ tc.result }}</div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
        </div>

        <div v-if="loading" class="msg-item assistant">
          <div class="msg-avatar"><el-icon :size="20"><Monitor /></el-icon></div>
          <div class="msg-body">
            <div class="typing-dots"><span></span><span></span><span></span></div>
          </div>
        </div>
      </div>

      <div class="msg-input">
        <el-input v-model="input" type="textarea" :rows="2"
          placeholder="输入你的问题，Enter 发送，Shift+Enter 换行" resize="none"
          @keydown.enter.exact.prevent="send(input)" :disabled="loading" />
        <div class="input-actions">
          <span class="thread-id">会话: {{ currentThread }}</span>
          <el-button type="primary" size="small" @click="send(input)"
            :loading="loading" :disabled="!input.trim()">发送</el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted } from 'vue'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { streamChat, listSessions, deleteSessionApi, getSessionMessages } from '../api/chat'
import { useAuthStore } from '../stores/auth'
import { marked } from 'marked'
import { ElMessageBox, ElMessage } from 'element-plus'

// ---- Markdown ----
marked.setOptions({ gfm: true, breaks: true })

function renderHtml(text) {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch {
    return text.replace(/\n/g, '<br>')
  }
}

const auth = useAuthStore()

// ---- 状态 ----
const input = ref('')
const loading = ref(false)
const currentThread = ref('default')
const msgListRef = ref(null)
const threads = ref([])

// 每个会话独立的消息缓存
const messagesByThread = ref({})
const messages = ref([])

const quickPrompts = [
  'Python 装饰器原理是什么？',
  '分析 src/tools/code_tools.py 代码',
  'Go 语言错误处理最佳实践',
  '列出这个项目的文件结构',
]

onMounted(() => fetchSessions(true))

async function fetchSessions(loadFirst = false) {
  try {
    const data = await listSessions()
    threads.value = (data.sessions || []).map(s => ({
      id: s.thread_id,
      title: s.title || '未命名',
      time: s.updated_at?.slice(0, 16) || '',
    }))
    if (threads.value.length === 0) {
      newChat()
      return
    }
    // 只在首次加载时自动打开第一个会话
    if (loadFirst && (!currentThread.value || !threads.value.find(t => t.id === currentThread.value))) {
      await loadThread(threads.value[0].id)
    }
  } catch {
    newChat()
  }
}

async function loadThread(id) {
  currentThread.value = id
  // 先从缓存取
  if (messagesByThread.value[id]) {
    messages.value = messagesByThread.value[id]
    return
  }
  // 从 API 加载历史消息
  messages.value = []
  try {
    const data = await getSessionMessages(id)
    if (data.messages?.length) {
      messages.value = data.messages
      messagesByThread.value = { ...messagesByThread.value, [id]: data.messages }
    }
  } catch {}
}

function newChat() {
  const id = 'thread-' + Date.now()
  threads.value.unshift({ id, title: '新会话', time: '' })
  currentThread.value = id
  messagesByThread.value = { ...messagesByThread.value, [id]: [] }
  messages.value = []
}

async function switchThread(id) {
  // 保存当前会话消息（用 spread 触发响应式）
  if (messages.value.length > 0) {
    messagesByThread.value = { ...messagesByThread.value, [currentThread.value]: [...messages.value] }
  }
  await loadThread(id)
  await nextTick()
  scrollBottom()
}

async function renameThread(t) {
  try {
    const { value } = await ElMessageBox.prompt('会话名称', '重命名', {
      inputValue: t.title,
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    if (value) t.title = value
  } catch {}
}

async function deleteThread(t) {
  try {
    await ElMessageBox.confirm('删除该会话？', '确认', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消',
    })
  } catch { return }

  try {
    await deleteSessionApi(t.id)
    threads.value = threads.value.filter(s => s.id !== t.id)
    const newMap = { ...messagesByThread.value }
    delete newMap[t.id]
    messagesByThread.value = newMap
    if (currentThread.value === t.id) {
      const nextId = threads.value[0]?.id
      if (nextId) await loadThread(nextId)
      else newChat()
    }
    if (threads.value.length === 0) newChat()
  } catch {
    ElMessage.error('删除失败')
  }
}

async function send(text) {
  const msg = text.trim()
  if (!msg || loading.value) return
  input.value = ''

  messages.value.push({ role: 'user', content: msg })
  const aiIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '', toolCalls: [] })
  await nextTick(); scrollBottom()

  loading.value = true
  try {
    let buffer = ''
    let toolBuffer = ''
    let currentToolName = ''

    for await (const chunk of streamChat(msg, currentThread.value)) {
      if (chunk.startsWith('🔧')) {
        toolBuffer = ''
        currentToolName = chunk.replace('🔧 **[调用工具: ', '').replace(']**\n', '').trim()
        continue
      }
      if (chunk.includes('\n📋') && currentToolName) {
        messages.value[aiIdx].toolCalls.push({ name: currentToolName, result: toolBuffer.slice(0, 500) })
        toolBuffer = ''
        continue
      }
      if (currentToolName) { toolBuffer += chunk; continue }

      buffer += chunk
      messages.value[aiIdx].content = buffer
      await nextTick(); scrollBottom()
    }
  } catch (e) {
    messages.value[aiIdx].content = '出错了: ' + e.message
  } finally {
    loading.value = false
    currentToolName = ''
    toolBuffer = ''
    fetchSessions()
  }
}


function scrollBottom() {
  if (msgListRef.value) msgListRef.value.scrollTop = msgListRef.value.scrollHeight
}
watch(currentThread, () => nextTick(scrollBottom))
</script>

<style lang="scss" scoped>
$primary: #409eff;
$bg-sidebar: #f7f8fa;
$bg-chat: #f0f2f5;
$bg-msg-user: #409eff;
$border: #e4e7ed;
$text-dim: #999;

.chat-layout { display: flex; height: 100%; }

.chat-sidebar {
  width: 220px;
  background: $bg-sidebar;
  border-right: 1px solid $border;
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

  .thread-actions {
    display: none;
    gap: 2px;
  }

  &:hover {
    background: #ecf5ff;

    .thread-actions { display: flex; }
  }

  &.active {
    background: #ecf5ff;
    border-left-color: $primary;
    color: $primary;
  }
}

.thread-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.thread-time { font-size: 11px; color: $text-dim; }

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.msg-list { flex: 1; overflow-y: auto; padding: 24px; }

.empty-hint {
  text-align: center;
  margin-top: 120px;
  color: #aaa;

  p { margin: 12px 0; font-size: 15px; }
}

.quick-prompts {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.prompt-tag {
  cursor: pointer;
  font-size: 13px;

  &:hover { background: $primary; color: #fff; }
}

.msg-item {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  max-width: 85%;

  &.user {
    margin-left: auto;
    flex-direction: row-reverse;

    .msg-avatar { background: $primary; color: #fff; }
    .msg-role { text-align: right; }
    .msg-content { background: $primary; color: #fff; }
  }

  &.assistant .msg-avatar { background: #e6f7ff; color: $primary; }
}

.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.msg-role { font-size: 12px; color: $text-dim; margin-bottom: 4px; }

.msg-content {
  background: $bg-chat;
  padding: 16px 20px;
  border-radius: 12px;
  font-size: 14px;
  word-break: break-word;
  line-height: 1.75;

  // ===== v-html Markdown: :global 去作用域 =====
  :global(p) { display: block; margin: .8em 0 !important; }
  :global(p:first-child) { margin-top: 0 !important; }
  :global(p:last-child) { margin-bottom: 0 !important; }
  :global(h1), :global(h2), :global(h3), :global(h4) {
    display: block;
    margin: 1.2em 0 .6em !important;
    font-weight: 600;
    line-height: 1.4;
  }
  :global(h1) { font-size: 1.4em; border-bottom: 1px solid #dcdfe6; padding-bottom: .3em; }
  :global(h2) { font-size: 1.2em; border-bottom: 1px solid $border; padding-bottom: .3em; }
  :global(h3) { font-size: 1.1em; }
  :global(ul), :global(ol) { display: block; padding-left: 1.8em !important; margin: .6em 0 !important; }
  :global(li) { display: list-item; margin: .15em 0; }
  :global(blockquote) {
    border-left: 4px solid $primary;
    padding: 4px 16px;
    margin: 12px 0;
    background: rgba($primary, .05);
    color: #555;
    display: block;
  }
  :global(code) {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: .9em;
    background: rgba(0, 0, 0, .06);
    padding: 2px 6px;
    border-radius: 4px;
    color: #e74c3c;
  }
  :global(pre) {
    background: #0d1117;
    border-radius: 8px;
    padding: 16px;
    overflow-x: auto;
    margin: 12px 0;
    display: block;

    :global(code) {
      background: transparent;
      color: #c9d1d9;
      font-size: 13px;
      line-height: 1.6;
      padding: 0;
      border-radius: 0;
    }
  }
  :global(table) { border-collapse: collapse; margin: 12px 0; width: 100%; display: table; }
  :global(th), :global(td) { border: 1px solid #dcdfe6; padding: 8px 12px; text-align: left; font-size: 13px; }
  :global(th) { background: #f5f7fa; font-weight: 600; }
  :global(hr) { border: none; border-top: 1px solid #dcdfe6; margin: 20px 0; display: block; }
  :global(a) { color: $primary; text-decoration: none; }
  :global(a:hover) { text-decoration: underline; }
  :global(strong) { font-weight: 600; }
  :global(em) { font-style: italic; }
}

// 用户消息中的 code/pre
.msg-item.user .msg-content {
  :global(pre) { background: rgba(0, 0, 0, .8); }
  :global(code) { background: rgba(255, 255, 255, .2); color: #e74c3c; }
}

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

.msg-input {
  border-top: 1px solid $border;
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

.typing-dots {
  display: flex;
  gap: 6px;
  padding: 8px 0;

  span {
    width: 8px;
    height: 8px;
    background: #bbb;
    border-radius: 50%;
    animation: bounce 1.4s ease-in-out infinite both;

    &:nth-child(1) { animation-delay: -.32s; }
    &:nth-child(2) { animation-delay: -.16s; }
  }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
