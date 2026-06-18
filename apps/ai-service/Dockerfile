FROM python:3.12-slim

WORKDIR /app
COPY apps/ai-service/pyproject.toml .
RUN pip install --no-cache-dir -e .
COPY apps/ai-service .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
