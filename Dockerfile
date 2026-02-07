# --- Builder Stage ---
FROM python:3.11-bookworm AS builder
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 1. Install Torch CPU first to avoid heavy GPU binaries
# 2. Install the rest of the requirements
RUN pip install --no-cache-dir --prefix=/install torch==2.5.1+cpu --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Runner Stage ---
FROM python:3.11-slim-bookworm AS runner

# Essential runtime libs: libpq5 (Postgres), libgomp1 (Parallel computing for ML)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 libgomp1 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces requires user 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    # Ensure NLTK and HF models save to the user's home (writable)
    NLTK_DATA=/home/user/app/nltk_data \
    HF_HOME=/home/user/app/.cache

WORKDIR $HOME/app

# Copy installed libraries from builder
COPY --from=builder /install /usr/local
COPY --chown=user . .

# Pre-download NLTK data to avoid runtime errors
RUN python -m nltk.downloader -d $HOME/app/nltk_data punkt punkt_tab averaged_perceptron_tagger_eng wordnet omw-1.1 stopwords

# Hugging Face standard port
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]