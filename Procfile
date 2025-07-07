web: gunicorn main:app --bind 0.0.0.0:$PORT
worker: celery -A worker worker --loglevel=info
