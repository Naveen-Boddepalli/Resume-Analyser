FROM python:3.12-slim

WORKDIR /app
ENV HF_HOME=/opt/hf

# CPU-only PyTorch keeps the image far smaller than the default CUDA wheels.
# hadolint ignore=DL3013
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
# The sentence encoder is baked into the image so the service starts offline.
RUN pip install --no-cache-dir -r requirements.txt \
    && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY . .

RUN useradd --create-home --uid 10001 app && chown -R app /app /opt/hf
USER app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
