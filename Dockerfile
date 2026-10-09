# Multi-stage production container for DarkSky Whisper
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final production stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install curl for container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
ENV APP_ENV=production

# Copy application artifacts
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY data/ ./data/
COPY skills/ ./skills/
COPY benchmarks/ ./benchmarks/
COPY pyproject.toml ./pyproject.toml
COPY LICENSE ./LICENSE

# Download and cache NASA JPL DE421 ephemeris kernel
RUN mkdir -p data/ephemeris && \
    curl -fsSL https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp -o data/ephemeris/de421.bsp && \
    cp data/ephemeris/de421.bsp ./de421.bsp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
