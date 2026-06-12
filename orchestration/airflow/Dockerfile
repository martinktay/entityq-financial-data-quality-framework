FROM apache/airflow:2.9.3-python3.11

USER root

COPY --chown=airflow:0 orchestration/airflow/requirements-airflow.txt /tmp/entityq-airflow-requirements.txt

RUN mkdir -p /opt/airflow/dags /opt/airflow/logs /opt/airflow/entityq && \
    chown -R airflow:0 /opt/airflow

USER airflow

RUN pip install --no-cache-dir -r /tmp/entityq-airflow-requirements.txt && \
    rm -f /tmp/entityq-airflow-requirements.txt

ENV PYTHONPATH=/opt/airflow/entityq/src
WORKDIR /opt/airflow/entityq
