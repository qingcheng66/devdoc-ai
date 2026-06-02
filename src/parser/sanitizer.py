import re


def sanitize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"​", "", text)
    text = re.sub(r"﻿", "", text)
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = re.sub(r" {3,}", "  ", text)
    text = re.sub(r"\t{2,}", "\t", text)
    return text
