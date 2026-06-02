---
title: DevDoc AI
emoji: 📄
colorFrom: indigo
colorTo: purple
sdk: docker
app_file: app.py
pinned: false
---

# DevDoc AI — 文档自动生成助手

上传 docx/pdf/txt 项目文档 → AI 自动生成实验报告(.docx)、汇报PPT(.pptx)、项目图表(PNG)

## 功能

- **实验报告** — 根据项目文档自动编写结构化报告
- **汇报 PPT** — 内容驱动的演示文稿生成
- **项目图表** — Mermaid 流程图/ER图/架构图自动渲染

## 技术栈

Gradio 6.x + LangGraph + DeepSeek API + ChromaDB + Mermaid CLI

## 使用方式

1. 上传项目文件（pdf/docx/txt/zip）
2. 勾选需要生成的输出类型
3. （可选）输入自定义指令，如"重点分析数据库设计"
4. 点击生成，等待结果下载

## 环境变量

在 Hugging Face Space Settings → Secrets 中配置：

| 变量 | 说明 | 必填 |
|------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 是 |
| `DEEPSEEK_MODEL` | 模型名称，默认 `deepseek-chat` | 否 |
| `DEEPSEEK_BASE_URL` | API 地址，默认 `https://api.deepseek.com` | 否 |
