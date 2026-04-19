# Build stage
FROM node:20-alpine AS builder
WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

ARG VITE_API_URL=http://localhost:8000
ARG VITE_API_KEY=
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_API_KEY=$VITE_API_KEY

RUN npm run build

# Serve stage
FROM nginx:alpine

ARG APP_USERNAME=admin
ARG APP_PASSWORD

RUN apk add --no-cache apache2-utils && \
    htpasswd -bc /etc/nginx/.htpasswd "$APP_USERNAME" "$APP_PASSWORD"

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
