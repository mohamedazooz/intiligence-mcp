FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends squid squidclient ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /run/squid /var/log/squid /var/cache/squid \
    && chown -R proxy:proxy /run/squid /var/log/squid /var/cache/squid

COPY squid.conf /etc/squid/squid.conf
USER proxy:proxy
EXPOSE 3128
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD squidclient -h 127.0.0.1 -p 3128 mgr:info >/dev/null 2>&1 || exit 1
CMD ["squid", "-N", "-f", "/etc/squid/squid.conf"]
