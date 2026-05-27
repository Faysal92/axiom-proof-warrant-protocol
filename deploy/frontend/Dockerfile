FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_AXIOM_API_BASE=/api
ENV VITE_AXIOM_API_BASE=${VITE_AXIOM_API_BASE}

COPY demo-ui/package*.json ./
RUN npm install

COPY demo-ui/ ./
RUN npm run build

FROM nginx:1.27-alpine

COPY deploy/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
