FROM node:24.18.1-bookworm-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

ARG VITE_API_BASE_URL=/api/producer
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM nginx:1.28-alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
