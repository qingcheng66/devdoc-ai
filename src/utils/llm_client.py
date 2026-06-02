from openai import OpenAI

from config.settings import settings
from src.utils.logger import logger


class DeepSeekClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        self.model = settings.deepseek_model
        self.max_tokens = settings.deepseek_max_tokens
        self.temperature = settings.deepseek_temperature
        self._initialized = True

    def chat(self, system_prompt: str, user_message: str,
             max_tokens: int | None = None) -> str:
        logger.info("Calling DeepSeek API for chat completion")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens or self.max_tokens,
            temperature=self.temperature,
        )
        content = response.choices[0].message.content or ""
        logger.info(f"DeepSeek response length: {len(content)} chars")
        return content

