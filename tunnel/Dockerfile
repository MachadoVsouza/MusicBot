# Cloudflare Tunnel — Container para link público temporário
# 
# Uso:
#   docker compose --profile tunnel up tunnel -d     → Sobe o túnel
#   docker compose --profile tunnel down tunnel       → Derruba o túnel
#   docker compose logs tunnel -f                     → Ver link gerado
#
# O link público aparece nos logs: "https://xxxx-xxxx-xxxx.trycloudflare.com"
#
# O container se conecta ao frontend via Docker DNS (frontend:80)

FROM alpine:latest

# Instala cloudflared via binário oficial
RUN wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/local/bin/cloudflared \
    && chmod +x /usr/local/bin/cloudflared

# Aponta para o serviço frontend do docker compose
ENTRYPOINT ["cloudflared", "tunnel", "--no-autoupdate", "--url", "http://frontend:80"]
