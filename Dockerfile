FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib

WORKDIR /app
RUN useradd --create-home --uid 10001 aurelia

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY data ./data
COPY artifacts ./artifacts
RUN python -m pip install --no-cache-dir .

USER aurelia
EXPOSE 8000
CMD ["uvicorn", "aurelia_alm.api:app", "--host", "0.0.0.0", "--port", "8000"]

