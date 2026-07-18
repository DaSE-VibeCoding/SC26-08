# SC26-08
DaSE 2026 暑期学校 SC26-08 小组项目仓库。
# 📚 Diffusion Papers - ACL Collection

一个用于收集和展示扩散模型相关论文的项目，支持从 arXiv 自动爬取论文数据并在前端页面进行搜索和筛选。

## ✨ 功能特性

- 🔍 **论文搜索**：按标题、作者、关键词搜索论文
- 🏷️ **标签筛选**：按主题标签（diffusion、denoising、generative等）筛选论文
- 📊 **统计信息**：显示论文总数和来源会议数量
- 🔗 **链接跳转**：点击标题跳转到 arXiv 摘要页面

## 📁 项目结构

```
├── scraper.py          # arXiv 论文爬虫脚本
├── analyze_page.py     # ACL 会议页面分析脚本（辅助）
├── index.html          # 前端展示页面
├── papers.json         # 论文数据文件（运行爬虫后生成）
└── .gitignore          # Git 忽略配置
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 现代浏览器（Chrome、Firefox、Edge等）

### 步骤 1：安装依赖

```bash
pip install requests beautifulsoup4
```

### 步骤 2：获取论文数据

运行爬虫脚本从 arXiv 爬取扩散模型相关论文：

```bash
python scraper.py
```

- 如果 `papers.json` 已有 ≥30 篇论文，脚本会自动跳过更新
- 强制更新（重新爬取）：

```bash
python scraper.py --force
```

### 步骤 3：启动前端页面

在项目目录下启动本地 HTTP 服务器：

```bash
python -m http.server 8000
```

然后在浏览器中访问：

```
http://localhost:8000
```

## 📖 使用说明

### 搜索论文

在搜索框中输入关键词，可以搜索论文标题、作者、摘要或标签。

### 标签筛选

点击页面上方的标签按钮（如 diffusion、denoising、generative），可以按主题筛选论文。

### 更新论文数据

定期运行 `python scraper.py` 可以获取最新的论文数据。

## 📝 爬虫脚本参数

| 参数 | 说明 |
|------|------|
| `--force` | 强制更新，忽略已有论文数量检查 |

## 📄 论文数据格式

`papers.json` 文件包含论文列表，每篇论文的结构如下：

```json
{
  "title": "论文标题",
  "authors": ["作者1", "作者2"],
  "conference": "来源会议",
  "pdf_url": "PDF链接",
  "abs_url": "摘要页面链接",
  "abstract": "摘要内容",
  "tags": ["标签1", "标签2"]
}
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
