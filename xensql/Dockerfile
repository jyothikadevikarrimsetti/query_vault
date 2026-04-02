# XenSQL - NL-to-SQL Pipeline Engine
# Multi-stage build | Python 3.11-slim

# -- Stage 1: Dependencies ----------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# -- Stage 2: Runtime ----------------------------------------------------------
FROM python:3.11-slim

LABEL maintainer="xensql"
LABEL description="XenSQL - NL-to-SQL Pipeline Engine"

WORKDIR /srv

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code into xensql/ package directory
COPY app/ ./xensql/app/
COPY config/ ./xensql/config/

# Create non-root user
RUN groupadd -r xensql && useradd -r -g xensql xensql
USER xensql

EXPOSE 8900

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "xensql.app.main:app", "--host", "0.0.0.0", "--port", "8900", "--workers", "1"]
