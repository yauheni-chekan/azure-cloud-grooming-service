# syntax=docker/dockerfile:1

# ---- Builder stage: install Python deps from uv.lock ----
    FROM python:3.13-slim-bookworm AS builder

    ENV UV_COMPILE_BYTECODE=1 \
        UV_LINK_MODE=copy
    
    WORKDIR /app
    
    # Build deps only needed in the builder (in case wheels are unavailable)
    RUN apt-get update \
        && apt-get install -y --no-install-recommends \
            build-essential \
            curl \
            unixodbc-dev \
        && rm -rf /var/lib/apt/lists/*
    
    # Install uv (no GHCR dependency)
    RUN pip install --no-cache-dir uv
    
    # Install dependencies strictly from the lockfile
    COPY pyproject.toml uv.lock /app/
    RUN uv sync --locked --no-dev --no-install-project
    
    # Copy application code and install the project into the venv
    COPY . /app
    RUN uv sync --locked --no-dev
    
    
    # ---- Runtime stage: minimal image + Azure SQL ODBC driver ----
    FROM python:3.13-slim-bookworm AS runtime
    
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1
    
    WORKDIR /app
    
    # Install Microsoft ODBC Driver 18 for SQL Server + unixODBC runtime
    RUN apt-get update \
        && apt-get install -y --no-install-recommends \
            ca-certificates \
            curl \
            gnupg \
        && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
            | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
        && echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main' \
            > /etc/apt/sources.list.d/microsoft-prod.list \
        && apt-get update \
        && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
            msodbcsql18 \
            unixodbc \
            libgssapi-krb5-2 \
        && apt-get purge -y --auto-remove curl gnupg \
        && rm -rf /var/lib/apt/lists/*
    
    # Non-root user
    RUN groupadd --system --gid 10001 app \
        && useradd --system --uid 10001 --gid 10001 --create-home app
    
    # Copy the fully built app + venv
    COPY --from=builder /app /app
    
    # Ensure venv tools are used
    ENV PATH="/app/.venv/bin:$PATH" \
        PYTHONPATH="/app"
    
    USER app
    
    EXPOSE 8000
    
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    