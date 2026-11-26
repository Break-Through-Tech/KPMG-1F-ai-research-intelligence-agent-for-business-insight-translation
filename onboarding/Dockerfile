FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    TOKENIZERS_PARALLELISM=false HF_HUB_DISABLE_PROGRESS_BARS=1 OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu --no-deps torch==2.15.0+cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip check
COPY src src
COPY prompts prompts
COPY experiments experiments
COPY snapshot snapshot
CMD ["python", "-B", "experiments/render-staging/server.py"]
