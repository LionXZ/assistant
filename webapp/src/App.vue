<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-left">
        <el-icon :size="24"><Monitor /></el-icon>
        <span class="title">DevAssistant</span>
        <el-tag size="small" type="info">AI 编程助手</el-tag>
      </div>
      <div class="header-right">
        <el-menu
          mode="horizontal"
          :default-active="route.path"
          router
          class="header-menu"
        >
          <el-menu-item index="/">
            <el-icon><ChatDotRound /></el-icon>
            <span>对话</span>
          </el-menu-item>
          <el-menu-item index="/search">
            <el-icon><Search /></el-icon>
            <span>检索</span>
          </el-menu-item>
          <el-menu-item index="/docs">
            <el-icon><FolderOpened /></el-icon>
            <span>文档</span>
          </el-menu-item>
        </el-menu>
        <el-tag v-if="health" type="success" size="small" effect="dark">
          {{ health.status }}
        </el-tag>
        <el-tag v-else type="danger" size="small" effect="dark">
          离线
        </el-tag>

        <el-dropdown v-if="auth.isLoggedIn" trigger="click">
          <span class="user-btn">
            <el-icon><User /></el-icon>
            {{ auth.user?.username }}
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>
                {{ auth.user?.email }}
              </el-dropdown-item>
              <el-dropdown-item divided @click="doLogout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-main class="app-main">
      <keep-alive> 
      <router-view />
      </keep-alive>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { healthCheck } from './api/chat'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const health = ref(null)

function doLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(async () => {
  try {
    health.value = await healthCheck()
  } catch {
    health.value = null
  }
})
</script>

<style lang="scss">
$bg-dark: #1a1a2e;
$primary: #409eff;
$text-dim: #ccc;
$text-white: #fff;

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: $bg-dark;
  padding: 0 24px;
  height: 56px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  color: $text-white;

  .title {
    font-size: 18px;
    font-weight: 700;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  color: $text-dim;
  cursor: pointer;
  font-size: 14px;

  &:hover { color: $text-white; }
}

.header-menu {
  background: transparent !important;
  border-bottom: none !important;

  .el-menu-item {
    color: $text-dim !important;
    border-bottom: 2px solid transparent !important;

    &:hover,
    &.is-active {
      color: $text-white !important;
      border-bottom-color: $primary !important;
    }
  }
}

.app-main {
  flex: 1;
  overflow: hidden;
  padding: 0;
}
</style>
