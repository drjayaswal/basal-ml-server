# --- Builder Stage ---
FROM python:3.11-bookworm AS builder
WORKDIR /app
COPY requirements.txt .
# Install dependencies into a temporary location
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Runner Stage ---
FROM python:3.11-slim-bookworm AS runner

# Install necessary system libraries for ML (like libgomp for scikit-learn)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a non-root user (Required for Hugging Face)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    NLTK_DATA=/home/user/app/nltk_data

WORKDIR $HOME/app

# Copy installed packages from builder
COPY --from=builder /install /usr/local
# Copy your application code
COPY --chown=user . .

# PRE-DOWNLOAD ALL NLTK DATA
# Doing this here prevents runtime errors and timeouts
RUN python -m nltk.downloader -d $HOME/app/nltk_data \
    punkt punkt_tab averaged_perceptron_tagger_eng wordnet omw-1.4 stopwords

# Hugging Face Spaces must use port 7860
EXPOSE 7860

# IMPORTANT: If your main.py is inside the 'app' folder, use app.main:app
# If main.py is in the root directory, use main:app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]