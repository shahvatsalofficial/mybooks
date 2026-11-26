# Launch Gunicorn with 4 Uvicorn ASGI workers and extended keepalive
gunicorn server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 3600 \
  --keep-alive 65 \
  --access-logfile - \
  --error-logfile -
