# Awake

AI 生涯成长产品。AI 教练「小海」通过苏格拉底式对话帮助高中生探索兴趣与职业方向，并把对话沉淀为「今天就能完成」的微行动任务打卡。

## 快速开始

### 前置依赖

- Docker & Docker Compose
- 一个 LLM API Key（默认 DeepSeek，可通过 `DEEPSEEK_API_KEY` 传入）

### 一键启动

```bash
git clone --recurse-submodules https://github.com/caorantaoyao/Awake.git
cd Awake
DEEPSEEK_API_KEY=sk-xxx docker compose up --build
```

启动后访问：

- 前端：http://localhost:7777
- 后端 API 文档：http://localhost:8000/docs

停止：

```bash
docker compose down
```

### 本地开发（不使用 Docker）

```bash
# 后端
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端（另开终端）
cd frontend
npm install
npm run dev  # http://localhost:7777

# DeerFlow（另开终端，对话必须）
cd deer-flow
# 参考 deer-flow 自身文档启动 Gateway 在 :8001
```

## 架构

```
React SPA (Nginx/Vite :7777) → FastAPI (:8000) → DeerFlow 2.0 (:8001) → LLM API
                                       ↓
                                   SQLite
```

- `backend/` — FastAPI 单体后端（鉴权、任务、对话代理、打卡、成长记录）
- `frontend/` — React/Vite SPA（零 UI 库依赖，手写 CSS）
- `deer-flow/` — Git submodule，AI Agent 引擎（LangGraph），独立仓库
