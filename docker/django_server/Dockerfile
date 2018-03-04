FROM python:3
ADD DemocrApp-API/. /srv/api
WORKDIR /srv/api
RUN pip install -r requirements.txt
RUN python manage.py makemigrations
RUN python manage.py migrate
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
