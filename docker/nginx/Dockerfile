FROM node:alpine
ADD DemocrApp-UI/. /srv/ui
WORKDIR /srv/ui
RUN npm install yarn
RUN yarn install
RUN yarn build

FROM nginx:latest
WORKDIR /usr/share/nginx/html
COPY --from=0 /srv/ui/node_modules node_modules/.
COPY --from=0 /srv/ui/src src/.
COPY --from=0 /srv/ui/public public/.

