<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2>重置密码</h2>
      <p class="auth-sub">通过邮箱验证重置密码</p>

      <!-- 步骤1: 输入邮箱 -->
      <el-form v-if="step === 1" @submit.prevent="sendCode" label-position="top" size="large">
        <el-form-item label="注册邮箱">
          <el-input v-model="email" placeholder="your@email.com" :prefix-icon="Message" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" class="submit-btn">
          发送验证码
        </el-button>
      </el-form>

      <!-- 步骤2: 验证码 + 新密码 -->
      <div v-else>
        <el-form @submit.prevent="doReset" label-position="top" size="large">
          <el-form-item label="验证码">
            <el-input v-model="code" placeholder="6 位验证码" maxlength="6" class="code-input" />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="password" type="password" show-password placeholder="至少 6 位" :prefix-icon="Lock" />
          </el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="submit-btn">
            重置密码
          </el-button>
        </el-form>
        <p class="auth-switch">
          <el-button link type="primary" @click="sendCode" :disabled="countdown > 0">
            {{ countdown > 0 ? `重发 (${countdown}s)` : '重新发送验证码' }}
          </el-button>
        </p>
      </div>

      <p class="auth-switch">
        <router-link to="/login">返回登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Message, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const BASE = (window.electronAPI?.isElectron) ? 'http://127.0.0.1:19876/api/v1' : '/api/v1'

const email = ref('')
const code = ref('')
const password = ref('')
const loading = ref(false)
const step = ref(1)
const countdown = ref(0)

async function sendCode() {
  if (!email.value) return
  loading.value = true
  try {
    const res = await fetch(`${BASE}/auth/forgot-password?email=${encodeURIComponent(email.value)}`, { method: 'POST' })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '发送失败')
    }
    step.value = 2
    startCountdown()
  } catch (e) {
    ElMessage.error(e.message)
  } finally { loading.value = false }
}

async function doReset() {
  if (!code.value || !password.value || password.value.length < 6) return
  loading.value = true
  try {
    const params = new URLSearchParams({ email: email.value, code: code.value, new_password: password.value })
    const res = await fetch(`${BASE}/auth/reset-password?${params}`, { method: 'POST' })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '重置失败')
    }
    ElMessage.success('密码重置成功，请登录')
    router.push('/login')
  } catch (e) {
    ElMessage.error(e.message)
  } finally { loading.value = false }
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
.auth-page { height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.auth-card { width: 400px; background: #fff; border-radius: 16px; padding: 40px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12); h2 { font-size: 22px; color: #333; text-align: center; } }
.auth-sub { text-align: center; color: #999; margin: 8px 0 24px; font-size: 14px; }
.submit-btn { width: 100%; margin-top: 8px; }
.auth-switch { text-align: center; margin-top: 20px; font-size: 14px; color: #999; a { color: #409eff; text-decoration: none; } }
.code-input :deep(input) { text-align: center; font-size: 24px; letter-spacing: 8px; }
</style>
