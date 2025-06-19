# Stage 1: Builder stage with build dependencies
FROM python:3.9-slim-buster AS builder

WORKDIR /usr/src/app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install build dependencies (if any, e.g., for compiling certain Python packages)
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev

# Install poetry (or pip if using requirements.txt directly for production)
# For this example, we'll stick to pip and requirements.txt as per current setup
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt


# Stage 2: Final stage with runtime dependencies
FROM python:3.9-slim-buster

WORKDIR /usr/src/app

# Create a non-root user and group
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Copy Python path from builder (if needed for specific compiled packages)
# COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy built wheels from builder stage
COPY --from=builder /usr/src/app/wheels /wheels
COPY requirements.txt .

# Install runtime dependencies from wheels (faster and avoids recompilation)
RUN pip install --no-cache /wheels/*

# Copy application code
COPY ./app ./app
COPY ./alembic ./alembic
COPY alembic.ini .
# Ensure main.py and other necessary root files are copied if they exist (currently main.py is in app/)

# Set permissions for the app user
# RUN chown -R appuser:appuser /usr/src/app
# USER appuser # Run as non-root user - good practice, but ensure file permissions allow it

# Expose port (FastAPI default is 8000)
EXPOSE 8000

# Healthcheck (optional but recommended)
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#   CMD curl -f http://localhost:8000/ || exit 1
# Note: For healthcheck on root path, ensure root path returns 200 OK.
# The current root path returns a JSON message with 200 OK.

# Command to run the application
# Use Gunicorn for production, Uvicorn for development/simplicity here
# For Gunicorn: CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "gunicorn_conf.py", "app.main:app"]
# For Uvicorn:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
