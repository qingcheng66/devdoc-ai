# DevDoc AI — 文档自动生成助手

## 项目概述

上传 docx/pdf/txt 项目文档 → AI 自动生成：
- 实验报告 (.docx)
- 汇报 PPT (.pptx)
- 项目图表 (.png, Mermaid 渲染)

## 技术栈

| 层级 | 技术 |
|------|------|
| UI | Gradio 6.x (`gr.Blocks`), 响应式 CSS (手机+电脑) |
| Agent 编排 | **LangGraph** — 顺序执行 5 个节点 |
| LLM | **DeepSeek API** (`deepseek-v4-pro`) |
| RAG | **ChromaDB** + `sentence-transformers` (all-MiniLM-L6-v2) |
| 文档解析 | python-docx, PyMuPDF, python-pptx |
| 图表渲染 | **Mermaid CLI** (mmdc), mermaid.ink API 兜底 |
| 项目配置 | pydantic-settings, .env |

## 架构：LangGraph 5 节点顺序执行

```
用户输入 → Parse → Embed → AnalyzeInstructions → [Skills 依次执行] → Merge
           (解析)   (向量化)   (LLM解析指令)        (Report/PPT/Diagram)   (汇总)
```

关键设计决策：
- **Skills 串行执行**（非并行）— 避免 LangGraph 并行节点合并时的状态丢失问题
- **指令分析节点** (Phase 2 新增) — 用户指令在 Embed 之后、Skill 之前由 LLM 解析为结构化 JSON，驱动后续动态 RAG 检索
- **RAG 动态检索** — 基础 query + 用户指令关键词拼接，确保检索结果与用户需求相关
- **zip 在 skill 内部创建** — diagram_skill._generate_artifact() 渲染完直接打包 diagrams.zip

## 目录结构

```
xiangmu/
├── app.py                      # 入口: Gradio 启动
├── .env                        # API Key 等配置（不提交 git）
├── .env.example                # 配置模板
├── requirements.txt            # Python 依赖
├── package.json                # Node 依赖（仅 mermaid-cli）
├── config/
│   ├── settings.py             # pydantic-settings 配置类
│   └── prompts.py              # 所有 LLM prompt（指令分析+三个skill）
├── src/
│   ├── agent/
│   │   ├── graph.py            # DevDocAgent — LangGraph 编排
│   │   ├── nodes.py            # 5个节点函数 (parse/embed/analyze/skills/merge)
│   │   ├── state.py            # AgentState TypedDict
│   │   └── router.py           # skill 路由选择
│   ├── skills/
│   │   ├── base.py             # BaseSkill 基类 (RAG检索+LLM调用+重试)
│   │   ├── report_skill.py     # 生成 docx 实验报告
│   │   ├── ppt_skill.py        # 生成 pptx 演示文稿
│   │   └── diagram_skill.py    # 生成 Mermaid 图表 → PNG + zip
│   ├── parser/
│   │   ├── loader.py           # UnifiedLoader 统一入口
│   │   ├── docx_loader.py      # DOCX 解析（段落+表格）
│   │   ├── pdf_loader.py       # PDF 解析
│   │   ├── txt_loader.py       # TXT 解析
│   │   ├── zip_loader.py       # ZIP 包解析
│   │   └── sanitizer.py        # 文本清洗
│   ├── rag/
│   │   ├── embedder.py         # sentence-transformers 向量化
│   │   ├── splitter.py         # 文档切分
│   │   ├── vector_store.py     # ChromaDB 存取
│   │   └── retriever.py        # 检索接口
│   └── utils/
│       ├── llm_client.py       # DeepSeek API 客户端
│       ├── mermaid_renderer.py # Mermaid CLI/API 双路渲染
│       ├── file_manager.py     # 上传文件/输出目录管理
│       └── logger.py           # 日志
├── ui/
│   ├── layout.py               # Gradio UI 布局 + CSS
│   └── handlers.py             # generate 按钮事件处理
├── data/
│   ├── uploads/                # 用户上传文件缓存
│   ├── outputs/                # 生成结果（按 session_id 分目录）
│   └── chroma_db/              # ChromaDB 持久化
└── tests/
```

## 开发历程

### Session 1 (05-29 上午) — 项目初始化
- 创建项目骨架、加载 skills (document-skills, architecture, uml, diagram-creator)
- 探索 codebase 结构

### Session 2 (05-29 下午) — Phase 1: 基础功能
- 搭建 Gradio UI (文件上传 + 文本粘贴 + 输出选择)
- 实现 LangGraph agent (Parse → Embed → Skills → Merge)
- 三个 Skill: ReportSkill (docx), PPTSkill (pptx), DiagramSkill (Mermaid PNG)
- ChromaDB RAG 检索 + DeepSeek LLM 调用
- 用户指令输入框 + 透传到 LLM prompt 的基础链路

### Session 3 (05-29 傍晚) — Phase 2: 指令深度驱动
- **新增 AnalyzeInstructions 节点**: LLM 结构化解析用户指令 → JSON
- **动态 RAG 检索**: base_query + focus_keywords 拼接，替代固定 query
- **结构化指令块**: `_format_instruction_block()` 将解析结果转为 LLM prompt
- 数据流: `用户"重点分析数据库" → 解析→focus_keywords→动态检索→聚焦数据库内容→真正影响输出`
- 改动: prompts.py, state.py, nodes.py, graph.py, base.py, report_skill.py, ppt_skill.py, diagram_skill.py

### Session 4 (06-01) — 图表下载修复
- **问题**: UI 预览能看到多个图表，但只有一个 PNG 可下载，无 zip
- **根因**: zip 创建代码在 handlers.py 中，但服务器运行时用的是旧 bytecode
- **修复**: 将 zip 打包逻辑移入 `diagram_skill._generate_artifact()`，渲染后立即打包
- `handlers.py` 简化为直接透传 zip 路径
- 验证: 2 张图 (flowchart + ER) 正确打包 → `diagrams.zip` (66KB)

### Session 5 (06-01) — Skills 生态探索
- 搜索图片生成类 skill，`npx skills find` 遇 OOM (exit 137)
- 确认 document-skills 套件（docx/pdf/pptx/xlsx）全部可用
- 了解 `find-skills` / `install-skills` 等管理命令

### Session 6 (06-01) — 文档内容读取
- 目标: 读取 `软件工程综合实践实验报告.docx`
- `Skill(docx)` 调用失败（独立 docx skill 通过 Skill 工具无法触发）
- **绕过方案**: `unzip` 解压 + 读取 `word/document.xml` 提取文本
- **识别结果**: 该文档为空白模板，9 章结构（项目背景→完整代码），所有字段为空
- 继续读取了 `DevDoc_AI_需求文档_v1.0.docx`

### Session 7 (06-01) — 项目全量总结
- 用户要求"阅读整个项目做一个总结"
- 完整遍历项目结构，读取所有核心源文件
- **产出**: 创建项目级 [CLAUDE.md](./CLAUDE.md)（架构+开发历程+启动方式）
- 同时建立 Memory 体系：`devdoc-project.md`、`user-preferences.md`、`project-skills.md`

### Session 8 (06-01) — PPT 模板引擎 + Pandoc/Presenton 调研
- **Pandoc**: 调研通用文档转换器（Markdown→DOCX/PPTX），`pandoc_path` 已配置
- **Presenton**: 调研开源 AI PPT 生成器（GitHub 5000+ stars, Apache 2.0, REST API + Docker）
- **PPT 模板引擎实现**（切入代码）:
  - 新建 `src/skills/ppt_template.py` — 外部 PPTX 模板引擎
    - 检测 `{{placeholder}}` 文本替换占位符
    - 识别幻灯片类型（cover/toc/content/section/summary）→ 克隆对应布局
    - 内置模板兜底（无外部模板时自动降级）
  - `config/settings.py` 新增 `PPT_TEMPLATE_PATH`、`pandoc_path`、`ppt_master_scripts_dir`
  - `config/prompts.py` PPT prompt 从"排版驱动"改为"内容驱动"（不再让 LLM 拼 XML）
  - `src/skills/ppt_skill.py` 改为调用 `generate_pptx()` 统一入口
- **状态**: 代码写完、导入验证通过、烟雾测试通过（内置模板 4 页 32KB <1s）
- **卡点**: 用户模板未找好，服务器未重启验证，等待模板就绪

## 当前状态

- ✅ 服务器运行: `python app.py` → `http://localhost:7860`
- ✅ 三个输出类型全部可用
- ✅ 指令驱动生成 (Phase 2) 已验证
- ✅ 多图表 zip 下载已验证
- ⚠️ Windows 下 `taskkill` + 后台任务退出码可能显示 "failed" (实际正常)

## 启动方式

```bash
# 1. 安装依赖
pip install -r requirements.txt
npm install          # 安装 mermaid-cli

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 3. 启动
python app.py
# 访问 http://localhost:7860
```

## 开发注意事项

- 修改代码后需要**重启服务器**才能生效（Kill 旧进程再启动）
- DeepSeek API 返回 JSON 时偶尔会包 markdown code fences，`_clean_json()` / `_parse_json_output()` 有处理
- Mermaid 渲染优先 CLI，失败时自动降级到 mermaid.ink API
- session 目录位于 `data/outputs/<session_id>/`，24小时 TTL
- Gradio File 组件不支持目录路径，只接受文件路径
