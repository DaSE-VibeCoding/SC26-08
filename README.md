# SC26-08 · Diffusion Papers Hub

DaSE 2026 暑期学校 SC26-08 小组项目。

一个面向 **Diffusion（扩散模型）方向** 论文的检索与浏览平台：后端聚合多数据源（arXiv、Papers With Code、Semantic Scholar 会议论文、CVF 会议 proceedings、papernotes.org），统一存储于 SQLite 并提供 REST API；前端以卡片形式展示论文，支持按会议 / 年份 / 标签筛选与全文搜索，并支持**界面中英切换**（摘要保留英文原文，预留可选的人工中文摘要字段）。

> 本期不包含六段式结构化分析，也不调用任何 LLM / 本地模型。

已接通的会议（2021–2025）：**ACL · CVPR · ICLR · AAAI · NeurIPS · ICCV · ICML · ECCV**。

## 架构

```
前端 (React + Vite + TS + Tailwind)
        │  fetch /api/*
        ▼
后端 (FastAPI) ── SQLite (papers.db)
        ▲
        │ 采集/归一化/去重
多数据源:
  · arXiv API（主源，可靠）
  · Semantic Scholar API（按 venue 接入 ACL/CVPR/ICLR/AAAI/NeurIPS/ICCV/ICML/ECCV，需免费 key）
  · CVF Open Access（CVPR/ICCV/ECCV 的会议 proceedings HTML，免 key）
  · Papers With Code API / papernotes.org（best-effort）
```

- 后端在 `/` 托管前端构建产物，API 挂载于 `/api`。
- 开发期由 Vite dev server 代理 `/api` 到后端。

## 目录结构

```
SC26-08/
├── backend/
│   ├── main.py            # FastAPI 应用（API + 静态托管）
│   ├── config.py          # 配置：DB 路径、数据源开关、采集参数
│   ├── database.py        # SQLite 连接与建表
│   ├── models.py          # SQLAlchemy 模型 + Pydantic Schema
│   ├── crud.py            # 查询 / 过滤 / 分页 / upsert / 中文摘要更新
│   ├── import_seed.py     # 将 papers.json 导入 SQLite
│   └── scrapers/          # 多源采集器 + run.py 编排入口
├── frontend/              # React 前端（构建输出到 backend/static）
├── papers.json            # arXiv diffusion 种子数据
├── scraper.py             # (已废弃) 旧独立脚本，逻辑已迁移至 backend/scrapers
└── requirements.txt       # 后端依赖
```

## 快速开始

### 1. 后端

```bash
# 安装依赖
pip install -r requirements.txt

# 导入种子数据（首次）
cd backend
python3 import_seed.py

# 启动服务
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

访问 <http://127.0.0.1:8000/>（若已构建前端则展示 UI），API 文档见 <http://127.0.0.1:8000/docs>。

### 2. 前端

```bash
cd frontend
npm install

# 开发模式（热更新，代理 /api 到 :8000）
npm run dev

# 生产构建（输出到 backend/static，由后端托管）
npm run build
```

## 数据采集

```bash
cd backend
python3 scrapers/run.py --max 100
```

- 数据源开关见 `backend/config.py`（`ENABLE_ARXIV` / `ENABLE_PAPERSWITHCODE` / `ENABLE_PROCEEDINGS` / `ENABLE_PAPERNOTES` / `ENABLE_SEMANTIC_SCHOLAR`）。
- **Semantic Scholar（会议论文主源）** 需要一个 **免费 API key**：
  1. 前往 <https://www.semanticscholar.org/product/api> 注册并创建 key（免费，无需付费）。
  2. 在项目根目录创建 `.env` 文件，写入：
     ```
     SEMANTIC_SCHOLAR_API_KEY=你的key
     ```
     （可参考 `.env.example`。）
  3. 未配置 key 时该源会优雅跳过，不影响其他数据源。
- 会议 / 年份范围在 `config.py` 的 `SEMANTIC_SCHOLAR_CONFERENCES` 与 `CONFERENCE_YEARS` 中配置（默认 ACL/CVPR/ICLR/AAAI/NeurIPS/ICCV/ICML/ECCV，2021–2025）；CVF（CVPR/ICCV/ECCV）通过 `proceedings.py` 的 `DEFAULT_TARGETS` 配置，免 key。
- arXiv 为可靠主源；Papers With Code / proceedings / papernotes 为 best-effort，单源失败不影响其他源。
- 去重：标题归一化（小写去标点）+ 来源 组成唯一键。

## API 概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/meta` | 会议 / 年份 / 标签 / 来源 分布 |
| GET | `/api/papers` | 论文列表，支持 `conference`、`year`、`tag`、`q`、`source`、`limit`、`offset` |
| GET | `/api/papers/{id}` | 单篇详情 |
| PATCH | `/api/papers/{id}/abstract_zh` | 更新人工中文摘要（body: `{"abstract_zh": "..."}`) |

## 中英文与中文摘要

- 界面文案通过前端轻量 i18n（`frontend/src/i18n`）实现中英切换。
- 论文摘要默认展示英文原文；当某篇论文通过 `PATCH /api/papers/{id}/abstract_zh` 补充了中文摘要后，中文界面下会优先展示中文摘要，否则回退英文原文。

## 技术栈

- 后端：FastAPI · SQLAlchemy · SQLite · Pydantic · requests · BeautifulSoup
- 前端：React 18 · TypeScript · Vite · Tailwind CSS · lucide-react
