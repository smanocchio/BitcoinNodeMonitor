FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY collector ./collector
RUN pip install --upgrade pip && pip install .

ENTRYPOINT ["python", "-m", "collector"]
