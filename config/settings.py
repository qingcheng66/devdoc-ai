from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # DeepSeek API
    deepseek_api_key: str = Field(..., env="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field("https://api.deepseek.com", env="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field("deepseek-chat", env="DEEPSEEK_MODEL")
    deepseek_max_tokens: int = Field(4096, env="DEEPSEEK_MAX_TOKENS")
    deepseek_temperature: float = Field(0.3, env="DEEPSEEK_TEMPERATURE")

    # RAG
    chunk_size: int = Field(1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="CHUNK_OVERLAP")
    retrieval_top_k: int = Field(5, env="RETRIEVAL_TOP_K")

    # ChromaDB
    chroma_persist_dir: str = Field("data/chroma_db", env="CHROMA_PERSIST_DIR")

    # Pandoc (optional, install via apt-get install pandoc on Linux)
    pandoc_path: str = Field("pandoc", env="PANDOC_PATH")
    pandoc_output_dir: str = Field("/tmp/pandoc_output", env="PANDOC_OUTPUT_DIR")

    # PPT template (external .pptx template with {{placeholder}} text)
    ppt_template_path: str = Field("", env="PPT_TEMPLATE_PATH")

    # ppt-master (SVG → native PPTX) — fallback when no template
    ppt_master_scripts_dir: str = Field(
        ".agents/skills/ppt-master/scripts", env="PPT_MASTER_SCRIPTS_DIR"
    )

    # Mermaid
    mermaid_cli_path: str = Field("mmdc", env="MERMAID_CLI_PATH")
    mermaid_api_url: str = Field("https://mermaid.ink", env="MERMAID_API_URL")

    # Output
    upload_dir: str = Field("data/uploads", env="UPLOAD_DIR")
    output_dir: str = Field("data/outputs", env="OUTPUT_DIR")
    session_ttl_hours: int = Field(24, env="SESSION_TTL_HOURS")

    # Retry
    max_retries: int = Field(2, env="MAX_RETRIES")

    # Gradio
    gradio_server_name: str = Field("0.0.0.0", env="GRADIO_SERVER_NAME")
    gradio_server_port: int = Field(7860, env="GRADIO_SERVER_PORT")
    gradio_share: bool = Field(False, env="GRADIO_SHARE")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
