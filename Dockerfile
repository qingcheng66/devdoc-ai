FROM python:3.11-slim

WORKDIR /app

# Install Node.js + npm (for mermaid-cli) + pandoc (optional doc converter)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg pandoc \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @mermaid-js/mermaid-cli \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Ensure data directories exist (HF Spaces /data is persistent)
RUN mkdir -p /tmp/uploads /tmp/outputs /data/chroma_db data/uploads data/outputs data/chroma_db

EXPOSE 7860

ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860
ENV CHROMA_PERSIST_DIR=/data/chroma_db
ENV UPLOAD_DIR=/tmp/uploads
ENV OUTPUT_DIR=/tmp/outputs

CMD ["python", "app.py"]
