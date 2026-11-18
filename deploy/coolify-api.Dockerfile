FROM caddy:2-alpine
COPY deploy/Caddyfile.coolify /etc/caddy/Caddyfile
EXPOSE 8080
