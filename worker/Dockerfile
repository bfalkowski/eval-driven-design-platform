FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

COPY --chown=app:app pyproject.toml ./
COPY --chown=app:app app ./app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

USER app

CMD ["python", "-m", "app.main"]
