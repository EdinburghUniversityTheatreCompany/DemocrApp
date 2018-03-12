FROM python:3
WORKDIR /srv/api
ADD DemocrApp-API/requirements.txt /srv/api
RUN pip install -r requirements.txt
ADD DemocrApp-API/. /srv/api
ADD docker/django_server/settings.py /srv/api/democrapp_api/.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
