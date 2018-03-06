FROM python:3
ADD DemocrApp-API/. /srv/api
WORKDIR /srv/api
RUN pip install -r requirements.txt
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
