import gradio as gr
from ui.layout import create_ui, CSS
from ui.handlers import handle_generate


def main():
    app, c = create_ui(on_generate=handle_generate)

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        css=CSS,
        theme=gr.themes.Soft(primary_hue="indigo"),
        show_error=True,
    )


if __name__ == "__main__":
    main()
