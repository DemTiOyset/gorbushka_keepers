# Двухэтапная сборка фронтенда.
# На первом этапе собираем статические файлы Vite,
# на втором раздаём их через Caddy — он автоматически выпускает и
# обновляет HTTPS-сертификаты Let's Encrypt при указанном домене.

FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=builder /app/dist /srv
EXPOSE 80 443
