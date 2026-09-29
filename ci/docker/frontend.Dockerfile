FROM node:16-alpine AS build

WORKDIR /workspace
COPY system-under-test/ruoyi-ui/package*.json ./
RUN npm install --no-audit --no-fund
COPY system-under-test/ruoyi-ui/ ./
RUN npm run build:prod

FROM nginx:1.27-alpine

COPY ci/docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/dist/ /usr/share/nginx/html/
EXPOSE 80
