FROM python:3.11-slim

RUN addgroup --system collector \
    && adduser --system --ingroup collector --home /home/collector --disabled-login collector

WORKDIR /app

COPY pyproject.toml ./
COPY collector ./collector
RUN pip install --upgrade pip && pip install . \
    && chown -R collector:collector /app

USER collector

ENV PATH="/home/collector/.local/bin:${PATH}"

ENTRYPOINT ["python", "-m", "collector"]
