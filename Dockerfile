# --- Builder Stage ---
FROM python:3.11-bookworm AS builder
WORKDIR /app
COPY requirements.txt .

# Install system-level build tools needed for libraries like psycopg2 or chromadb
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Runner Stage ---
FROM python:3.11-slim-bookworm AS runner

# libpq5 is needed for the database, libgomp1 for ML models
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libpq5 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a non-root user (Required for Hugging Face)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    NLTK_DATA=/home/user/app/nltk_data \
    HF_HOME=/home/user/app/.cache

WORKDIR $HOME/app

# Copy installed packages from builder
COPY --from=builder /install /usr/local
# Copy your application code
COPY --chown=user . .

# PRE-DOWNLOAD ALL NLTK DATA & SPACY MODELS
# We use the 'local' python to ensure paths are correct
RUN python -m nltk.downloader -d $HOME/app/nltk_data \
    punkt punkt_tab averaged_perceptron_tagger_eng wordnet omw-1.4 stopwords && \
    python -m spacy download en_core_web_md

# Hugging Face Spaces must use port 7860
EXPOSE 7860

# Adjust app.main:app if your entry point file name is different
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]