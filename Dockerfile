FROM python:3

EXPOSE 5000

WORKDIR /app

COPY . .

RUN pip install -r /app/requirements.txt

RUN pwd

# CMD ["gunicorn", "app:app", "--config", "/app/gunicorn.config.py"]
ENTRYPOINT FLASK_APP=/app/app.py flask run --host=0.0.0.0
