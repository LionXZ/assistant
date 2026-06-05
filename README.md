# DevAssistant — AI 编程助手

基于 LangChain v1.3 + LangGraph v1.2 构建的 AI Agent，前端 Vue 3 + Element Plus，后端 FastAPI，默认使用 DeepSeek 模型。

---

## 技术栈

| 层 | 技术 | 说明 |
|---|------|------|
| **Agent 框架** | LangChain v1.3 + LangGraph v1.2 | Agent 编排、工具调用、RAG、记忆 |
| **大模型** | DeepSeek Chat (OpenAI 兼容) | 可切换为任何 OpenAI 兼容模型 |
| **嵌入模型** | BAAI/bge-small-zh-v1.5 (本地) / OpenAI | 自动回落，无需额外配置 |
| **向量数据库** | ChromaDB | 嵌入式，零运维 |
| **业务数据库** | MySQL 8.0 | 用户、会话、消息、对话状态 |
| **对话记忆** | MySQL Checkpointer (自实现) | 多轮对话上下文持久化 |
| **长期记忆** | LangGraph InMemoryStore | 用户偏好、跨会话记忆 |
| **邮箱服务** | QQ 邮箱 SMTP | 验证码发送 (免费 500封/天) |
| **搜索 API** | Tavily Search | 联网搜索工具（可选） |
| **后端框架** | FastAPI + Uvicorn | 异步、自动文档 |
| **前端框架** | Vue 3 + Vite | Composition API |
| **UI 库** | Element Plus | 组件丰富 |
| **样式** | SCSS | 嵌套、变量 |
| **路由** | Vue Router 4 | 懒加载 + keep-alive |
| **Markdown** | marked v18 | GFM + 代码高亮 |

---

## 数据库表结构 (MySQL `dev-assistant`)

### users — 用户账号

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INT PK | 自增主键 |
| `username` | VARCHAR(30) UNIQUE | 用户名 |
| `email` | VARCHAR(100) UNIQUE | 邮箱 |
| `password` | VARCHAR(255) | bcrypt 哈希 |
| `is_admin` | TINYINT | 管理员标识 (0/1)，admin 为系统保留账户 |
| `email_verified` | TINYINT | 邮箱验证状态 |
| `verification_code` | VARCHAR(6) | 邮箱验证码 |
| `reset_token` | VARCHAR(6) | 密码重置码 |
| `created_at` | DATETIME | 注册时间 |

### sessions — 会话列表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INT PK | 自增主键 |
| `user_id` | INT FK → users.id | 所属用户 |
| `thread_id` | VARCHAR(100) | 会话 ID (前端 UUID) |
| `title` | VARCHAR(50) | AI 自动生成标题 |
| `updated_at` | DATETIME | 最后活跃时间 |

联合唯一键：`(user_id, thread_id)`

### messages — 对话历史

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INT PK | 自增主键 |
| `user_id` | INT FK → users.id | 所属用户 |
| `thread_id` | VARCHAR(100) | 所属会话 |
| `role` | VARCHAR(20) | `user` / `assistant` |
| `content` | TEXT | 消息内容 |
| `created_at` | DATETIME | 发送时间 |

索引：`(user_id, thread_id)`

### langgraph_checkpoints — Agent 对话状态

| 字段 | 类型 | 说明 |
|------|------|------|
| `thread_id` | VARCHAR(100) | 会话 ID |
| `checkpoint_ns` | VARCHAR(50) | 命名空间 |
| `checkpoint_id` | VARCHAR(50) | 检查点 ID |
| `parent_checkpoint_id` | VARCHAR(50) | 父检查点 |
| `type` | VARCHAR(50) | 序列化格式 |
| `checkpoint` | LONGBLOB | 检查点数据 (二进制) |
| `metadata` | LONGTEXT | 元数据 (JSON) |

主键：`(thread_id, checkpoint_ns, checkpoint_id)`

### langgraph_writes — Agent 暂存写入

| 字段 | 类型 | 说明 |
|------|------|------|
| `thread_id` | VARCHAR(100) | 会话 ID |
| `checkpoint_ns` | VARCHAR(50) | 命名空间 |
| `checkpoint_id` | VARCHAR(50) | 关联检查点 |
| `task_id` | VARCHAR(50) | 任务 ID |
| `idx` | INT | 写入序号 |
| `channel` | VARCHAR(100) | 通道名 |
| `type` | VARCHAR(50) | 序列化格式 |
| `value` | LONGBLOB | 值 (二进制) |

主键：`(thread_id, checkpoint_ns, checkpoint_id, task_id, idx)`

## 目录结构

```
dev-assistant/
├── .gitignore
├── README.md
│
├── backend/                      # Python FastAPI 后端
│   ├── venv/                     # Python 虚拟环境
│   ├── .env / .env.example
│   ├── requirements.txt
│   ├── src/
│   │   ├── app.py                # 启动入口
│   │   ├── config/settings.py    # 全局配置
│   │   ├── models/chat_model.py  # DeepSeek/OpenAI 模型封装
│   │   ├── agent/assistant.py    # Agent 组装 + 对话 + 流式
│   │   ├── auth/                 # 用户认证
│   │   │   ├── auth.py           # JWT 签发/验证
│   │   │   ├── email.py          # QQ 邮箱 SMTP
│   │   │   └── models.py         # MySQL 用户/会话/消息/验证码
│   │   ├── api/                  # FastAPI 路由
│   │   │   ├── server.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── tools/                # Agent 工具
│   │   │   ├── code_tools.py
│   │   │   ├── web_tools.py
│   │   │   ├── rag_tool.py
│   │   │   ├── registry.py
│   │   │   └── mcp_tools.py
│   │   ├── rag/                  # RAG 检索
│   │   │   ├── loader.py
│   │   │   ├── splitter.py
│   │   │   ├── embedder.py
│   │   │   └── retriever.py
│   │   ├── memory/               # 记忆系统
│   │   │   ├── checkpointer.py
│   │   │   ├── mysql_saver.py    # MySQL Checkpointer
│   │   │   └── store.py
│   │   ├── middleware/custom.py
│   │   └── utils/logger.py
│   ├── tests/
│   └── evaluations/
│
├── frontend/                     # Vue 3 + Vite 前端
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/index.js
│       ├── stores/auth.js        # Pinia 认证
│       ├── api/chat.js
│       └── views/
│           ├── ChatView.vue
│           ├── SearchView.vue
│           ├── DocsView.vue
│           ├── LoginView.vue
│           ├── RegisterView.vue
│           └── ForgotPasswordView.vue
│
├── desktop/                      # Electron 桌面端 (macOS)
│   ├── main.js                   # 主进程
│   ├── preload.js                # 安全桥接
│   ├── package.json
│   └── icons/
│
├── data/
│   ├── documents/                # RAG 知识库
│   └── chroma/                   # 向量索引
```

---

## 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 18+
- DeepSeek API Key (或任意 OpenAI 兼容 Key)

### 2. 后端

```bash
cd dev-assistant

# 创建虚拟环境
python3 -m venv backend/venv

# 安装依赖
backend/venv/bin/pip install -r backend/requirements.txt

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入所有必填项
```

**.env 关键配置：**

```bash
# 大模型 (必填)
LLM_API_KEY=sk-your-deepseek-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 嵌入模型 (可选，不填自动用本地 bge-small-zh ~100MB)
OPENAI_API_KEY=

# MySQL (必填)
DB_NAME=dev-assistant
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306

# QQ 邮箱 SMTP (必填, 注册/重置密码用)
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your-qq@qq.com
SMTP_PASSWORD=授权码

# 搜索 API (可选)
TAVILY_API_KEY=

DEBUG=true
```

### 3. 启动

```bash
# 终端1: 后端 (端口 8000)
# 方式1: 启动脚本
sh backend/run.sh

# 方式2: 手动
backend/venv/bin/python -m backend.src.app

# 终端2: 前端 (端口 3000)
cd frontend && npm install && npm run dev
```

打开 `http://localhost:3000`：

| 路由 | 页面 | 功能 | 权限 |
|------|------|------|------|
| `/login` | 登录 | 账号登录 | 所有人 |
| `/register` | 注册 | 注册 + 邮箱验证 | 所有人 |
| `/forgot-password` | 忘记密码 | 邮箱验证重置密码 | 所有人 |
| `/` | 对话 | 流式 AI 对话，多会话管理 | 登录用户 |
| `/search` | 检索 | 知识库搜索 | 登录用户 |
| `/docs` | 文档 | 查看文档（上传/删除仅 admin）| 登录用户 |

### 4. 桌面端 (macOS)

```bash
# 1. 构建前端
cd frontend && npm run build

# 2. 启动 Electron (自动拉起 Python 后端)
cd ../desktop && npm start

# 3. 打包 dmg
npm run package:mac
```

API 文档：`http://localhost:8000/docs`

---

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/auth/register` | 注册 (发送验证码到邮箱) |
| `POST` | `/api/v1/auth/verify-email` | 邮箱验证 |
| `POST` | `/api/v1/auth/send-code` | 重发验证码 |
| `POST` | `/api/v1/auth/login` | 登录 (需邮箱已验证) |
| `GET` | `/api/v1/auth/me` | 当前用户 (含 is_admin) |
| `POST` | `/api/v1/auth/forgot-password` | 发送重置密码验证码 |
| `POST` | `/api/v1/auth/reset-password` | 重置密码 (自动激活邮箱) |
| `GET` | `/api/v1/health` | 健康检查 |
| `POST` | `/api/v1/chat` | 同步对话 |
| `POST` | `/api/v1/chat/stream` | SSE 流式对话 |
| `GET` | `/api/v1/sessions` | 会话列表 |
| `DELETE` | `/api/v1/sessions/{id}` | 删除会话 |
| `GET` | `/api/v1/sessions/{id}/messages` | 会话历史消息 |
| `GET` | `/api/v1/rag/documents` | 文档列表 |
| `POST` | `/api/v1/rag/upload` | 上传文档 |
| `POST` | `/api/v1/rag/delete` | 删除文档 |

### curl 示例

```bash
# 注册
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@qq.com","password":"123456"}'

# 登录 (获取 token)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'

# 同步对话 (需 token)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message":"Python装饰器原理？","thread_id":"u-001"}'

# 流式对话
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message":"分析代码工具实现","thread_id":"u-001"}'
```

---
## 权限说明

| 角色 | 权限 |
|------|------|
| **admin** (系统保留) | 登录、对话、检索、上传文档、删除文档 |
| **普通用户** (注册+邮箱验证) | 登录、对话、检索、查看文档 |

admin 账号 `admin` 为系统保留，其他人无法注册该用户名。文档上传/删除仅 admin 可见和可用。

---

## Agent 能力

### 内置工具

| 工具 | 说明 |
|------|------|
| `search_knowledge_base` | RAG 知识库检索 |
| `read_code_file` | 读取代码文件内容 |
| `list_code_files` | 列出项目文件结构 |
| `count_code_lines` | 统计代码行数/注释/空行 |
| `web_search` | Tavily 联网搜索 |

### 工作流程

```
用户提问 → Agent 分析 → 选择工具调用
              ↓
    ┌─────────┼──────────┐
    ↓         ↓          ↓
  RAG检索   代码分析   联网搜索
    ↓         ↓          ↓
    └─────────┼──────────┘
              ↓
          汇总回答 (流式输出)
```

---

## 文档上传与 AI 分类

admin 上传 `.txt` `.md` `.pdf` 文件时：

1. 文件读到临时位置
2. 提取前 800 字，调用 AI 判断分类（如 `Python编程`、`数据库`）
3. 自动创建/匹配目录，移入文件
4. 增量添加到 ChromaDB 索引（不重建）

---

## 配置切换

### 切换到 OpenAI

修改 `backend/.env`：

```bash
LLM_API_KEY=sk-your-openai-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_MODEL_MINI=gpt-4o-mini

OPENAI_API_KEY=sk-your-openai-key     # 用 OpenAI 嵌入
```

### 切换到其他 OpenAI 兼容模型

任何兼容 OpenAI API 的模型（Ollama、vLLM 等）只需改 `LLM_BASE_URL` 和 `LLM_MODEL`。
