from dataclasses import dataclass
import gradio as gr


@dataclass
class UIComponents:
    file_input: gr.File
    text_input: gr.Textbox
    instructions_input: gr.Textbox
    gen_report: gr.Checkbox
    gen_ppt: gr.Checkbox
    gen_diagram: gr.Checkbox
    generate_btn: gr.Button
    status_text: gr.Textbox
    preview_md: gr.Markdown
    error_display: gr.Textbox
    download_report: gr.File
    download_ppt: gr.File
    download_diagram: gr.File


CSS = """
/* ===== Reset & Base ===== */
* { box-sizing: border-box; }
:root {
    --primary: #4f46e5;
    --primary-hover: #4338ca;
    --primary-light: #eef2ff;
    --success: #059669;
    --warning: #d97706;
    --danger: #dc2626;
    --gray-50: #f9fafb;
    --gray-100: #f3f4f6;
    --gray-200: #e5e7eb;
    --gray-300: #d1d5db;
    --gray-500: #6b7280;
    --gray-700: #374151;
    --gray-900: #111827;
    --radius: 12px;
    --radius-sm: 8px;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
    --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06);
    --shadow-lg: 0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05);
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, "Noto Sans SC", sans-serif;
    background: #f1f5f9;
    margin: 0;
    padding: 0;
}

.gradio-container {
    max-width: 960px !important;
    margin: 0 auto !important;
    padding: 0 16px !important;
}

/* ===== Header ===== */
.devdoc-header {
    text-align: center;
    padding: 40px 20px 32px;
}
.devdoc-header .logo {
    display: inline-block;
    width: 64px; height: 64px;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    border-radius: 16px;
    margin-bottom: 16px;
    line-height: 64px; font-size: 28px;
    box-shadow: 0 4px 16px rgba(79,70,229,0.3);
}
.devdoc-header h1 {
    font-size: 28px; font-weight: 700;
    color: var(--gray-900); margin: 0 0 6px;
    letter-spacing: -0.5px;
}
.devdoc-header p {
    font-size: 15px; color: var(--gray-500); margin: 0;
}

/* ===== Step Cards ===== */
.step-section {
    background: #fff;
    border-radius: var(--radius);
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--gray-200);
}
.step-label {
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 13px; font-weight: 600; color: var(--primary);
    text-transform: uppercase; letter-spacing: 0.5px;
    margin-bottom: 16px;
}
.step-badge {
    display: inline-flex; align-items: center; justify-content: center;
    width: 24px; height: 24px; border-radius: 50%;
    background: var(--primary); color: #fff;
    font-size: 12px; font-weight: 700;
}

/* ===== Output Toggle Cards ===== */
.output-toggles {
    display: flex; gap: 12px; flex-wrap: wrap;
}
.output-toggle-card {
    flex: 1; min-width: 140px;
    border: 2px solid var(--gray-200); border-radius: var(--radius);
    padding: 16px; text-align: center; cursor: pointer;
    transition: all 0.2s;
}
.output-toggle-card:hover {
    border-color: var(--primary); background: var(--primary-light);
}
.output-toggle-card.selected {
    border-color: var(--primary); background: var(--primary-light);
    box-shadow: 0 0 0 3px rgba(79,70,229,0.15);
}
.output-toggle-card .icon { font-size: 28px; margin-bottom: 6px; }
.output-toggle-card .label { font-size: 13px; font-weight: 600; color: var(--gray-700); }
.output-toggle-card .ext  { font-size: 11px; color: var(--gray-500); }

/* ===== Generate Button ===== */
.generate-btn-wrap { margin: 8px 0 20px; }
.generate-btn-wrap button {
    width: 100% !important; height: 52px !important;
    font-size: 16px !important; font-weight: 600 !important;
    border-radius: var(--radius) !important;
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    border: none !important; color: #fff !important;
    cursor: pointer; transition: all 0.2s;
    box-shadow: 0 4px 14px rgba(79,70,229,0.35);
}
.generate-btn-wrap button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(79,70,229,0.45);
}
.generate-btn-wrap button:active { transform: translateY(0); }

/* ===== Status Bar ===== */
.status-bar {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 16px; border-radius: var(--radius-sm);
    font-size: 14px; font-weight: 500;
}
.status-idle { background: var(--gray-100); color: var(--gray-500); }
.status-running { background: #fef3c7; color: #92400e; }
.status-done { background: #d1fae5; color: #065f46; }
.status-error { background: #fee2e2; color: #991b1b; }

/* ===== Results Area ===== */
.results-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
}
.result-card {
    background: #fff; border-radius: var(--radius);
    padding: 20px; text-align: center;
    border: 1px solid var(--gray-200);
    box-shadow: var(--shadow-sm);
    transition: all 0.2s;
}
.result-card:hover { box-shadow: var(--shadow-md); }
.result-card .icon  { font-size: 32px; margin-bottom: 8px; }
.result-card .title { font-size: 14px; font-weight: 600; color: var(--gray-700); margin-bottom: 4px; }
.result-card .meta  { font-size: 12px; color: var(--gray-500); margin-bottom: 12px; }
.result-card .download-btn {
    display: inline-block; padding: 6px 18px;
    background: var(--primary); color: #fff;
    border-radius: 20px; font-size: 13px; font-weight: 500;
    text-decoration: none; transition: all 0.2s;
}
.result-card .download-btn:hover { background: var(--primary-hover); }

/* ===== Preview Panel ===== */
.preview-panel {
    background: #fff; border-radius: var(--radius);
    padding: 20px; margin-bottom: 16px;
    border: 1px solid var(--gray-200);
    box-shadow: var(--shadow-sm);
}

/* ===== Footer ===== */
.devdoc-footer {
    text-align: center; padding: 32px 20px;
    color: var(--gray-500); font-size: 13px;
}

/* ===== Mobile (screen < 640px) ===== */
@media (max-width: 640px) {
    .gradio-container { padding: 0 10px !important; }
    .devdoc-header { padding: 28px 12px 24px; }
    .devdoc-header h1 { font-size: 22px; }
    .devdoc-header p { font-size: 14px; }
    .step-section { padding: 16px; border-radius: var(--radius-sm); }
    .results-grid { grid-template-columns: 1fr; }
    .output-toggles { flex-direction: column; }
    .output-toggle-card { min-width: 100%; }
    .generate-btn-wrap button {
        height: 48px !important; font-size: 15px !important;
        border-radius: var(--radius-sm) !important;
    }
}

/* ===== Tablet (640px - 1024px) ===== */
@media (min-width: 641px) and (max-width: 1024px) {
    .results-grid { grid-template-columns: repeat(2, 1fr); }
    .results-grid .result-card:last-child:nth-child(3) { grid-column: 1 / -1; }
}

/* ===== Gradio Overrides ===== */
.gradio-container .tabs > .tab-nav { border-bottom: 2px solid var(--gray-200); }
.gradio-container .tabs > .tab-nav button {
    font-size: 14px; font-weight: 500; padding: 10px 20px;
    border: none; background: transparent; color: var(--gray-500);
}
.gradio-container .tabs > .tab-nav button.selected {
    color: var(--primary); border-bottom: 2px solid var(--primary);
    margin-bottom: -2px;
}
footer { display: none !important; }
"""


def create_ui(on_generate) -> tuple[gr.Blocks, UIComponents]:
    with gr.Blocks(title="DevDoc AI - 文档自动生成助手") as app:

        # === Header ===
        gr.HTML("""
        <div class="devdoc-header">
            <div class="logo">&#9997;</div>
            <h1>DevDoc AI</h1>
            <p>上传项目文件，AI 自动生成实验报告、汇报 PPT 与项目图表</p>
        </div>
        """)

        # === Step 1: Upload ===
        with gr.Column(elem_classes="step-section"):
            gr.HTML('<div class="step-label"><span class="step-badge">1</span> 上传项目文件</div>')
            with gr.Row():
                with gr.Column(scale=2):
                    file_input = gr.File(
                        label="  上传文件",
                        file_types=[".pdf", ".docx", ".txt", ".zip"],
                        file_count="multiple",
                    )
                with gr.Column(scale=1):
                    text_input = gr.Textbox(
                        label="  或粘贴文本",
                        placeholder="直接粘贴项目描述内容...",
                        lines=5, max_lines=10,
                    )

        # === Step 2: Choose Outputs ===
        with gr.Column(elem_classes="step-section"):
            gr.HTML('<div class="step-label"><span class="step-badge">2</span> 选择生成内容</div>')
            with gr.Row():
                gen_report = gr.Checkbox(label=" 实验报告 (.docx)", value=True)
                gen_ppt = gr.Checkbox(label=" 汇报PPT (.pptx)", value=True)
                gen_diagram = gr.Checkbox(label=" 项目图表 (.png)", value=True)

        # === Step 3: Instructions ===
        with gr.Column(elem_classes="step-section"):
            gr.HTML('<div class="step-label"><span class="step-badge">3</span> 告诉 AI 你的需求（可选）</div>')
            instructions_input = gr.Textbox(
                label="  自定义指令",
                placeholder="例如：重点分析数据库设计部分、用简洁风格、生成英文报告、突出技术亮点...",
                lines=3, max_lines=6,
            )

        # === Step 4: Generate ===
        with gr.Column(elem_classes="step-section"):
            gr.HTML('<div class="step-label"><span class="step-badge">4</span> 开始生成</div>')
            with gr.Column(elem_classes="generate-btn-wrap"):
                generate_btn = gr.Button("  开 始 生 成", variant="primary")
            status_text = gr.Markdown(
                '<div class="status-bar status-idle"> 等待上传文件并点击生成...</div>'
            )

        # === Results ===
        gr.HTML("""
        <div class="results-grid" id="download-grid">
            <div class="result-card">
                <div class="icon">&#128196;</div>
                <div class="title">实验报告</div>
                <div class="meta">生成后将在此显示下载</div>
            </div>
            <div class="result-card">
                <div class="icon">&#128202;</div>
                <div class="title">汇报 PPT</div>
                <div class="meta">生成后将在此显示下载</div>
            </div>
            <div class="result-card">
                <div class="icon">&#128200;</div>
                <div class="title">项目图表</div>
                <div class="meta">生成后将在此显示下载</div>
            </div>
        </div>
        """)

        with gr.Tabs():
            with gr.TabItem("  预览"):
                preview_md = gr.Markdown("", elem_classes="preview-panel")
            with gr.TabItem("  错误信息"):
                error_display = gr.Textbox(
                    label="错误详情", visible=True, interactive=False,
                    placeholder="如无错误则为空",
                )

        gr.Markdown("###  下载文件")
        with gr.Row():
            download_report = gr.File(label="实验报告 (.docx)", visible=True)
            download_ppt = gr.File(label="汇报PPT (.pptx)", visible=True)
            download_diagram = gr.File(label="项目图表", visible=True)

        # === Footer ===
        gr.HTML('<div class="devdoc-footer">DevDoc AI v1.0 &nbsp;|&nbsp; Powered by DeepSeek + LangGraph &nbsp;|&nbsp; 支持手机 & 电脑双端访问</div>')

        # Wire up event handler
        generate_btn.click(
            fn=on_generate,
            inputs=[file_input, text_input, gen_report, gen_ppt, gen_diagram, instructions_input],
            outputs=[preview_md, status_text, download_report, download_ppt,
                     download_diagram, error_display],
        )

    components = UIComponents(
        file_input=file_input,
        text_input=text_input,
        instructions_input=instructions_input,
        gen_report=gen_report,
        gen_ppt=gen_ppt,
        gen_diagram=gen_diagram,
        generate_btn=generate_btn,
        status_text=status_text,
        preview_md=preview_md,
        error_display=error_display,
        download_report=download_report,
        download_ppt=download_ppt,
        download_diagram=download_diagram,
    )
    return app, components
