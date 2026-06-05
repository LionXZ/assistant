<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2>创建账号</h2>
      <p class="auth-sub">注册后验证邮箱即可使用</p>

      <!-- 步骤1: 注册表单 -->
      <el-form v-if="step === 1" @submit.prevent="doRegister" label-position="top" size="large">
        <el-form-item label="用户名">
          <el-input v-model="username" placeholder="2-30 个字符" :prefix-icon="User" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="email" placeholder="your@email.com" :prefix-icon="Message" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" show-password placeholder="至少 6 位" :prefix-icon="Lock" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" class="submit-btn">
          注册
        </el-button>
      </el-form>

      <!-- 步骤2: 邮箱验证 -->
      <div v-else class="verify-step">
        <el-icon :size="48" color="#67c23a"><CircleCheck /></el-icon>
        <p class="verify-hint">验证码已发送至 <b>{{ email }}</b></p>
        <el-input
          v-model="code"
          placeholder="请输入 6 位验证码"
          maxlength="6"
          size="large"
          class="code-input"
          @keydown.enter="doVerify"
        />
        <el-button type="primary" size="large" :loading="loading" @click="doVerify" class="submit-btn">
          验证
        </el-button>
        <p class="auth-switch">
          <el-button link type="primary" @click="resendCode" :disabled="countdown > 0">
            {{ countdown > 0 ? `重发 (${countdown}s)` : '重新发送验证码' }}
          </el-button>
        </p>
      </div>

      <p class="auth-switch">
        已有账号？
        <router-link to="/login">返回登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'

const router = useRouter()
const BASE = (window.electronAPI?.isElectron) ? 'http://127.0.0.1:19876/api/v1' : '/api/v1'

const username = ref('')
const email = ref('')
const password = ref('')
const code = ref('')
const loading = ref(false)
const step = ref(1)
const userId = ref(null)
const countdown = ref(0)

async function doRegister() {
  if (!username.value || !email.value || !password.value) return
  loading.value = true
  try {
    const res = await fetch(`${BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, email: email.value, password: password.value }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '注册失败')
    }
    const data = await res.json()
    userId.value = data.user_id
    step.value = 2
    startCountdown()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function doVerify() {
  if (!code.value || code.value.length !== 6) return
  loading.value = true
  try {
    const res = await fetch(`${BASE}/auth/verify-email?user_id=${userId.value}&code=${code.value}`, { method: 'POST' })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '验证失败')
    }
    ElMessage.success('邮箱验证成功，请登录')
    router.push('/login')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function resendCode() {
  if (countdown.value > 0) return
  loading.value = true
  try {
    const res = await fetch(`${BASE}/auth/send-code?user_id=${userId.value}`, { method: 'POST' })
    if (res.ok) {
      ElMessage.success('验证码已重新发送')
      startCountdown()
    }
  } catch {} finally { loading.value = false }
}

function startCountdown() {
  countdown.value = 60
  const t = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(t)
  }, 1000)
}
</script>

<style lang="scss" scoped>
.auth-page {
  height: 100%; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.auth-card {
  width: 400px; background: #fff; border-radius: 16px; padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  h2 { font-size: 22px; color: #333; text-align: center; }
}
.auth-sub { text-align: center; color: #999; margin: 8px 0 24px; font-size: 14px; }
.submit-btn { width: 100%; margin-top: 8px; }
.auth-switch { text-align: center; margin-top: 20px; font-size: 14px; color: #999; a { color: #409eff; text-decoration: none; } }
.verify-step { text-align: center; }
.verify-hint { margin: 16px 0; font-size: 15px; color: #333; }
.code-input { margin-bottom: 12px; width: 200px; }
.code-input :deep(input) { text-align: center; font-size: 24px; letter-spacing: 8px; }
</style>
