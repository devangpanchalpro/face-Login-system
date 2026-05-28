# -------------------------------------
# Stage 1: Builder
# -------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools + runtime libs needed for compiling and running insightface/cv2 during model download
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    libopenblas0-pthread \
    liblapack3 \
    libgl1 \
    libglib2.0-0t64 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# Install dependencies. We use the CPU-only PyTorch index to prevent pip from downloading massive CUDA wheels 
# if any package indirectly depends on torch. This saves gigabytes of space.
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Pre-download InsightFace model during build
RUN python -c "from insightface.app import FaceAnalysis; app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider']); app.prepare(ctx_id=0, det_size=(320, 320)); print('✅ InsightFace model downloaded')"

# Move the downloaded models to a temporary path so we can cleanly copy them to the final stage
RUN mkdir -p /opt/models && mv /root/.insightface /opt/models/

# -------------------------------------
# Stage 2: Final Runtime Image
# -------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Install ONLY the runtime system libraries (no g++)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0t64 \
    libpq5 \
    libopenblas0-pthread \
    liblapack3 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy pre-downloaded insightface models back to /root/
COPY --from=builder /opt/models/.insightface /root/.insightface

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy the actual application files
COPY . .

RUN chmod +x entrypoint.sh
RUN mkdir -p /app/media /app/staticfiles

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
