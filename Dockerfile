FROM python:3.11-slim

# Install runtime libraries + build tools for insightface Cython extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas0-pthread \
    liblapack3 \
    libgl1 \
    libglib2.0-0t64 \
    libpq5 \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (insightface needs g++ for Cython build)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download InsightFace model (buffalo_l) during build so it's cached
RUN python -c "from insightface.app import FaceAnalysis; app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider']); app.prepare(ctx_id=0, det_size=(320, 320)); print('✅ InsightFace model downloaded')"

COPY . .

RUN chmod +x entrypoint.sh
RUN mkdir -p /app/media /app/staticfiles

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
