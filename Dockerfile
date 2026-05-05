FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY services ./services
COPY scripts ./scripts
COPY data ./data

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH
ENV HOST=0.0.0.0
ENV PORT=5000

EXPOSE 5000

CMD ["python", "./backend/run_waitress.py"]
