# ── Stage 1: Build frontend ──────────────────────────────
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python backend ─────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Install Python deps (CPU-only PyTorch)
COPY requirements-cloud.txt ./
RUN pip install --no-cache-dir -r requirements-cloud.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Expose port (Render sets PORT env var)
EXPOSE 8000

# Start the server
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
