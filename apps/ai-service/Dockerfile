FROM python:3.12-slim

WORKDIR /app
RUN addgroup --system progresia && adduser --system --ingroup progresia progresia
COPY apps/ai-service/pyproject.toml .
RUN pip install --no-cache-dir -e .
COPY apps/ai-service .
RUN chown -R progresia:progresia /app
USER progresia
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
