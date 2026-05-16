FROM python:3.11-slim

# Install only runtime libraries (no compilation needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas0-pthread \
    liblapack3 \
    libgl1 \
    libglib2.0-0t64 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Step 1: Install pre-compiled dlib (no cmake/build needed!)
RUN pip install --no-cache-dir dlib-bin

# Step 2: Install face_recognition WITHOUT re-installing dlib
#         (it sees dlib already installed from dlib-bin)
RUN pip install --no-cache-dir --no-deps face_recognition
RUN pip install --no-cache-dir face_recognition_models Click

# Step 3: Install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh
RUN mkdir -p /app/data /app/media /app/staticfiles

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
