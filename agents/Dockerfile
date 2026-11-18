# Plen Dev agents: inbound audit server + Alex outbound sales agent, one container.
# Railway: service root directory = /agents, volume mounted at /data.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 TZ=America/New_York
RUN apt-get update && apt-get install -y --no-install-recommends tzdata ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY audit-agent/requirements.txt audit-agent/requirements.txt
COPY alex/requirements.txt alex/requirements.txt
RUN pip install -r audit-agent/requirements.txt -r alex/requirements.txt
COPY . .
ENV OUTBOX_DIR=/data/audit-outbox ALEX_DATA_DIR=/data/alex ALEX_DIR=/app/alex AUDIT_ENGINE_DIR=/app/audit-agent
CMD ["python", "run.py"]
