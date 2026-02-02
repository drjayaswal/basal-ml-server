# --- Builder Stage (Use the full image to avoid 'apt-get' download issues) ---
FROM python:3.11-bookworm AS builder

WORKDIR /app

# Copy requirements from the main folder
COPY requirements.txt .

# Install dependencies into the /root/.local folder
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Runner Stage (Keep the final image small) ---
FROM python:3.11-slim-bookworm AS runner

# Install only the necessary runtime library for ML (libgomp1)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the installed packages from the builder stage
COPY --from=builder /root/.local /root/.local
# Copy all your code (including the /app folder)
COPY . .

# Ensure the app can find the installed packages
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Render's default port is 10000
EXPOSE 10000

# Start Uvicorn pointing to app/main.py
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]