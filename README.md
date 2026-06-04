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
| **向量数据库** | ChromaDB | 嵌入式，零运维 |
| **对话记忆** | MySQL Checkpointer (自实现) | 多轮对话上下文持久化 |
| **长期记忆** | LangGraph InMemoryStore | 用户偏好、跨会话记忆 |
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
├── .env                          # 环境变量 (不提交)
├── .env.example                  # 环境变量模板
├── .gitignore
├── requirements.txt              # Python 依赖
├── README.md
│
├── src/                          # 后端
│   ├── app.py                    # 启动入口
│   ├── config/settings.py        # 全局配置 (加载 .env)
│   ├── models/chat_model.py      # DeepSeek/OpenAI 模型封装
│   ├── agent/assistant.py        # Agent 组装 + 对话 + 流式
│   ├── api/
│   │   ├── server.py             # FastAPI 应用 + 生命周期
│   │   ├── routes.py             # /chat /chat/stream /rag/*
│   │   └── schemas.py            # 请求/响应模型
│   ├── tools/
│   │   ├── code_tools.py         # 读文件、列目录、统计行数
│   │   ├── web_tools.py          # Tavily 联网搜索
│   │   ├── rag_tool.py           # 知识库检索工具
│   │   ├── registry.py           # 工具注册中心（单例）
│   │   └── mcp_tools.py          # MCP 外部工具集成
│   ├── rag/
│   │   ├── loader.py             # txt/md/pdf 文档加载
│   │   ├── splitter.py           # 智能文本切分
│   │   ├── embedder.py           # 嵌入模型 (OpenAI/本地)
│   │   └── retriever.py          # ChromaDB 检索器 + 增量索引
│   ├── memory/
│   │   ├── checkpointer.py       # 短期对话记忆
│   │   └── store.py              # 长期用户偏好记忆
│   ├── middleware/custom.py      # 偏好注入 + 性能监控
│   └── utils/logger.py           # JSON 格式日志
│
├── data/
│   ├── documents/                # RAG 知识库 (支持子目录)
│   │   ├── 01-编程语言/          # Go语言、Python 等
│   │   ├── 02-Web开发框架/       # Django 等
│   │   ├── 03-数据库与缓存/      # MySQL、Redis、向量数据库等
│   │   ├── 04-AI-Agent/         # LangChain、AI Agent 设计
│   │   └── ...                  # 上传时 AI 自动分类
│   ├── chroma/                   # 向量索引 (自动生成)
│   └── checkpoints.db            # 对话检查点 (自动生成)
│
├── tests/                        # 测试
├── evaluations/                  # 评估数据集
│
├── webapp/                       # 前端
│   ├── index.html
│   ├── vite.config.js            # Vite + API 代理
│   ├── package.json
│   └── src/
│       ├── main.js               # Vue 入口
│       ├── App.vue               # 布局 + 导航
│       ├── router/index.js       # 路由 (懒加载)
│       ├── api/chat.js           # 流式/同步 API 封装
│       └── views/
│           ├── ChatView.vue      # 流式对话页
│           ├── SearchView.vue    # 知识库检索页
│           └── DocsView.vue      # 文档管理页 (上传+AI分类)
│
└── venv/                         # Python 虚拟环境 (项目内)
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

# 创建虚拟环境 (如未创建)
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY（DeepSeek API Key）
# OPENAI_API_KEY 可留空，嵌入自动用本地模型
```

**.env 关键配置：**

```bash
# 大模型 (必填)
LLM_API_KEY=sk-your-deepseek-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 嵌入模型 (可选，不填自动用本地 bge-small-zh ~100MB)
OPENAI_API_KEY=

# 搜索 API (可选)
TAVILY_API_KEY=

# 调试模式
DEBUG=true
```

### 3. 启动

```bash
# 终端1: 后端 (端口 8000)
source venv/bin/activate
python -m src.app

# 终端2: 前端 (端口 3000)
cd webapp
npm install
npm run dev
```

打开 `http://localhost:3000`，三个页面：

| 路由 | 页面 | 功能 |
|------|------|------|
| `/` | 对话 | 流式 AI 对话，多会话管理，工具调用展示 |
| `/search` | 检索 | 知识库搜索，Markdown 渲染 |
| `/docs` | 文档 | 上传文件 → AI 自动分类 → 增量索引 |

API 文档：`http://localhost:8000/docs`

---

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/health` | 健康检查 |
| `POST` | `/api/v1/chat` | 同步对话 |
| `POST` | `/api/v1/chat/stream` | SSE 流式对话 |
| `GET` | `/api/v1/rag/documents` | 文档列表 + 索引统计 |
| `POST` | `/api/v1/rag/upload` | 上传文档 (multipart) |
| `POST` | `/api/v1/rag/delete` | 删除文档 |

### curl 示例

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 同步对话
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Python装饰器原理？", "thread_id": "user-001"}'

# 流式对话
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "分析src/tools/code_tools.py", "thread_id": "user-001"}'

# 上传文档
curl -X POST http://localhost:8000/api/v1/rag/upload \
  -F "files=@my-doc.md"
```

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

上传 `.txt` `.md` `.pdf` 文件时：

1. 文件读到临时位置
2. 提取前 800 字，调用 AI 判断分类（如 `Python编程`、`数据库`）
3. 自动创建/匹配目录，移入文件
4. 增量添加到 ChromaDB 索引（不重建）

---

## 配置切换

### 切换到 OpenAI

修改 `.env`：

```bash
LLM_API_KEY=sk-your-openai-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_MODEL_MINI=gpt-4o-mini

OPENAI_API_KEY=sk-your-openai-key     # 用 OpenAI 嵌入
```

### 切换到其他 OpenAI 兼容模型

任何兼容 OpenAI API 的模型（Ollama、vLLM 等）只需改 `LLM_BASE_URL` 和 `LLM_MODEL`。
