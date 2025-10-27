FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY wallet_service.py .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8085/health').raise_for_status()" || exit 1

# Expose port
EXPOSE 8085

# Security: Run as non-root user
RUN groupadd -r ifp && useradd -r -g ifp ifp
RUN chown -R ifp:ifp /app
USER ifp

# Run application
CMD ["uvicorn", "wallet_service:app", "--host", "0.0.0.0", "--port", "8085"]
