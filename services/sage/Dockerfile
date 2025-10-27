FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


# Security: Run as non-root user
RUN groupadd -r ifp && useradd -r -g ifp ifp
RUN chown -R ifp:ifp /app
USER ifp

CMD ["python", "sage_core.py", "--interval=60"]
