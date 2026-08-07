# Minimal image -- only what's needed to run the API.
FROM python:3.11-slim

WORKDIR /app

# Install deps first so Docker caches this layer across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the actual app code + data (ingest.py needs data/policies/
# to self-heal the Qdrant collection on first run, same as it does
# for the Streamlit app on ephemeral filesystems).
COPY . .

# Cloud Run / App Runner both inject PORT at runtime; default to
# 8080 for local `docker run`.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]