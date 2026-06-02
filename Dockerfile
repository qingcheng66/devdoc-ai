FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install mermaid-cli for diagram rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm \
    && npm install -g @mermaid-js/mermaid-cli \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN mkdir -p data/uploads data/outputs data/chroma_db

EXPOSE 7860

ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860

CMD ["python", "app.py"]
