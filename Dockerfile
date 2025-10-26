FROM python:3.12-slim

WORKDIR /app

# Устанавливаем зависимости без кеша
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Создаём непривилегированного пользователя и передаём ему права на /app
RUN groupadd --system app && useradd --system --create-home --gid app --uid 1000 --shell /usr/sbin/nologin appuser \
    && chown -R appuser:app /app

# Запуск от non-root
USER 1000

EXPOSE 8080

# Healthcheck по существующему эндпоинту /healthz
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python - <<'PY' || exit 1
import sys,urllib.request
try:
    urllib.request.urlopen("http://127.0.0.1:8080/healthz", timeout=2).read()
except Exception:
    sys.exit(1)
PY

# Запуск uvicorn (порт/хост уже используются в compose/k8s)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "5"]
