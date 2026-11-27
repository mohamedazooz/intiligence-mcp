FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends tor ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 tor \
    && useradd --uid 10001 --gid 10001 --home-dir /var/lib/tor \
       --no-create-home --shell /usr/sbin/nologin tor \
    && mkdir -p /var/lib/tor \
    && chown -R tor:tor /var/lib/tor

COPY torrc /etc/tor/torrc

USER 10001:10001
ENTRYPOINT ["tor", "-f", "/etc/tor/torrc"]
