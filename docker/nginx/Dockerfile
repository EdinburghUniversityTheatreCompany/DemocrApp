FROM node:alpine
ADD DemocrApp-UI/. /srv/ui
WORKDIR /srv/ui
RUN npm install yarn
RUN yarn install
RUN yarn build

FROM nginx:latest
WORKDIR /usr/share/nginx/html
COPY --from=0 /srv/ui/node_modules ../node_modules/.
COPY --from=0 /srv/ui/src .
COPY docker/nginx/api-endpoint.conf /etc/nginx/conf.d/.
RUN mkdir -p /srv/api/static
RUN chown -R nginx:www-data /srv/api/static
