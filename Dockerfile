FROM python:3.11-slim

WORKDIR /app

# requirements-dev.txt (pytest) se incluye para poder ejecutar los tests dentro del contenedor
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY backend ./backend
COPY services ./services
COPY scripts ./scripts
COPY data ./data
COPY tests ./tests

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH
ENV HOST=0.0.0.0
ENV PORT=5000

EXPOSE 5000

CMD ["python", "./backend/run_waitress.py"]
