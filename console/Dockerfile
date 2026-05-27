FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

COPY --chown=app:app pyproject.toml ./
COPY --chown=app:app components ./components
COPY --chown=app:app pages ./pages
COPY --chown=app:app styles ./styles
COPY --chown=app:app .streamlit ./.streamlit
COPY --chown=app:app streamlit_app.py ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

USER app

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
