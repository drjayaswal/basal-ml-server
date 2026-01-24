# --- Builder Stage ---
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .

# Install dependencies into a specific prefix to make copying easier
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Aggressively remove unneeded files from the installation prefix
RUN find /install -name "*.pyc" -delete && \
    find /install -name "__pycache__" -delete


# --- Runner Stage ---
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy the installed packages from the builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Ensure Python doesn't write bytecode (.pyc)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

# Using 'python -m uvicorn' is safer as it bypasses PATH issues with binaries
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]