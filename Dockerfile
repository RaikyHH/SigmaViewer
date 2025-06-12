# Dockerfile for Sigma Rule Viewer Web Application

# --- Base Stage ---
# Use the same lightweight Python base image for consistency.
FROM python:3.11-slim AS base

# Set environment variables for Python in containers.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --- Builder Stage ---
# This stage installs dependencies, including any build-time tools.
FROM base AS builder

WORKDIR /app

# Install build-essentials like gcc in case any Python package needs to compile C extensions.
# These tools will not be in the final, lean image.
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker's layer caching.
COPY requirements.txt .

# Install Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# --- Final Stage ---
# This is the final, production-ready image. It's minimal and secure.
FROM base

# Create a non-root user and group for running the application.
RUN adduser --system --group appuser

# Set the working directory for the application code.
WORKDIR /usr/src/app

# Copy installed packages from the builder stage.
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy the application source code.
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Ensure the appuser owns the application files.
RUN chown -R appuser:appuser /usr/src/app

# Create and set permissions for the data volume mount point.
# This allows the non-root user to read/write to the mounted host directory.
RUN mkdir /data && chown appuser:appuser /data

# Switch the working directory to the data directory.
# The app will run from here, so it finds 'sigma_rules.db' in its current path.
WORKDIR /data

# Switch to the non-root user for enhanced security.
USER appuser

# Expose the port the application will run on.
EXPOSE 5000

# Add OCI labels for image metadata.
LABEL org.opencontainers.image.source="https://github.com/RaikyHH/SigmaViewer"
LABEL org.opencontainers.image.description="A web viewer for Sigma rules."
LABEL org.opencontainers.image.licenses="MIT"

# Define the command to run the application using a production-grade WSGI server.
# Gunicorn is a standard for running Flask apps in production.
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "app:app"]
