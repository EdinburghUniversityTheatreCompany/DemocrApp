FROM node:alpine
ADD DemocrApp-UI/. /srv/ui
WORKDIR /srv/ui
RUN npm install yarn
RUN yarn install
RUN yarn build

FROM python:3
ADD DemocrApp-API/. /srv/api
WORKDIR /srv/ui
COPY --from=0 /srv/ui/node_modules node_modules/.
COPY --from=0 /srv/ui/src src/.
COPY --from=0 /srv/ui/public public/.
WORKDIR /srv/api
RUN pip install -r requirements.txt
RUN python manage.py makemigrations
RUN python manage.py migrate
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

