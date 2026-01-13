web: gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
worker: celery -A app.tasks worker --loglevel=info
beat: celery -A app.tasks beat --loglevel=info
