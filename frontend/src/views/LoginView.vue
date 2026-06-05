<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2>
        <el-icon :size="28"><Monitor /></el-icon>
        DevAssistant
      </h2>
      <p class="auth-sub">AI 编程助手</p>

      <el-form @submit.prevent="doLogin" label-position="top" size="large">
        <el-form-item label="用户名">
          <el-input v-model="username" placeholder="请输入用户名" :prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" show-password placeholder="请输入密码" :prefix-icon="Lock" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" class="submit-btn">
          登录
        </el-button>
      </el-form>

      <p class="auth-switch">
        还没有账号？
        <router-link to="/register">立即注册</router-link>
        <span style="margin:0 8px">|</span>
        <router-link to="/forgot-password">忘记密码</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function doLogin() {
  if (!username.value || !password.value) return
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.auth-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.auth-card {
  width: 400px;
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);

  h2 {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 22px;
    color: #333;
  }
}
.auth-sub {
  text-align: center;
  color: #999;
  margin: 8px 0 24px;
  font-size: 14px;
}
.submit-btn {
  width: 100%;
  margin-top: 8px;
}
.auth-switch {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #999;

  a {
    color: #409eff;
    text-decoration: none;
  }
}
</style>
