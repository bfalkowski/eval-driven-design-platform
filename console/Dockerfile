FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/edd-api \
    EDD_REFERENCE_SCENARIO_DIR=/app/examples/customer_escalation_triage

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

COPY console/pyproject.toml ./
COPY console/components ./components
COPY console/pages ./pages
COPY console/styles ./styles
COPY console/.streamlit ./.streamlit
COPY console/streamlit_app.py ./
COPY api/app /opt/edd-api/app
COPY examples/customer_escalation_triage ./examples/customer_escalation_triage

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

USER app

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
