# Isolated Egress Deployment

## Security objective

Run the MCP process on a Docker network with no direct external route. The only permitted outbound HTTP(S) path is a dedicated Squid proxy attached to both the isolated application network and an external egress network.

The application validates every target URL and redirect hop. The proxy independently rejects non-public destination ranges. This is defense in depth, not a substitute for host/cloud firewall policy.

## Network topology

- `intiligence-mcp` joins `internal_net` (`172.30.0.0/24`, Docker `internal: true`) and `redis_net` (`172.31.0.0/24`, also internal).
- `egress-proxy` joins `internal_net` and `egress_net`; it cannot access the Redis-only network.
- `redis` joins only `redis_net`; it has no published host port and no external route. It coordinates host pacing and robots-policy caching only; it is not the system of record.
- The proxy listens on TCP/3128 only inside the Docker network; no host port is published.
- The MCP container has no direct external route and must use `http://egress-proxy:3128`.
- Squid permits only the app subnet, HTTP/HTTPS safe ports, and public destination IPs. It denies loopback, private, link-local, CGNAT, documentation, benchmark, multicast, reserved, IPv6 ULA, IPv6 link-local, and selected transition ranges.
- The app's `INTILIGENCE_REQUIRE_EGRESS_PROXY=true` makes missing proxy configuration fail closed.
- `INTILIGENCE_REQUIRE_SHARED_RATE_LIMIT=true` requires `INTILIGENCE_REDIS_URL`; Redis reservations use one atomic Lua script and Redis server time, so multiple app processes share a host pacing schedule. Redis failures do not silently fall back to process-local pacing.
- `INTILIGENCE_REQUIRE_SHARED_ROBOTS_CACHE=true` requires the same Redis endpoint. Robots.txt status/body records are shared by origin, and a bounded Redis lock prevents workers from stampeding the same origin on cache misses. Redis errors fail closed.

## Build and run

Requirements: Docker Engine with Compose v2.

Build images:

```sh
docker compose -f compose.yaml build --pull
```

Run the MCP process interactively over stdio (configure the MCP client to launch this Compose command):

```sh
docker compose -f compose.yaml run --rm intiligence-mcp
```

Inspect proxy logs:

```sh
docker compose -f compose.yaml logs --tail=200 egress-proxy
```

Stop the stack:

```sh
docker compose -f compose.yaml down
```

The named `intiligence_data` volume persists SQLite source/evidence/claim data. `redis_data` persists Redis AOF/RDB state for pacing reservations. Back up the SQLite volume before destructive operations; Redis data is coordination state and can be rebuilt; losing it resets active pacing reservations and may temporarily increase request rate.

## Required production controls

1. Pin all three base images by immutable digest after the first trusted build; update them through reviewed dependency-update PRs. The Dockerfiles and Compose file intentionally use maintained Debian/Python/Redis tags as build inputs, not immutable production attestations.
2. Apply host/cloud firewall rules so only required inbound administration and outbound DNS/HTTPS for the proxy are allowed. Docker network isolation does not replace host firewall policy.
3. Do not attach browser workers, parsers, or arbitrary sidecars to `egress_net`. Give each worker its own isolated network and explicit proxy policy.
4. Validate the exact Squid version and ACL behavior in staging, including IPv4, IPv6, redirects, CONNECT, mixed DNS answers, metadata addresses, and attempts to reach the Docker host/gateway.
5. Do not enable `INTILIGENCE_ALLOW_PRIVATE_NETWORKS` in this profile.
6. Use a dedicated production secret/configuration mechanism and image scanning before deployment. For remote Redis, require TLS and authentication/ACLs; the single-host Compose profile relies on private Docker networking and does not configure a Redis password.
7. This profile is not yet a complete production deployment: no TLS ingress, remote MCP transport, authentication, PostgreSQL, centralized audit, or tested backup/restore is included.

## Limitations

- `internal_net` intentionally has no external route and, on Docker Desktop, does not provide public DNS resolution to the app container. The app still validates URL syntax, scheme, credentials, allow/deny lists, and literal IP addresses. Only a temporary DNS failure (`EAI_AGAIN`) for a hostname may be delegated, and only when `INTILIGENCE_REQUIRE_EGRESS_PROXY=true` and a proxy URL is configured. Squid then performs the hostname resolution and is the authoritative destination-IP filter. NXDOMAIN and other DNS errors remain fail-closed. This means the proxy ACL is a critical security boundary, not merely an optional second check; test it on every deployed Squid build.
- Docker `internal: true` isolates the app network from external routing, but Docker daemon/host administrators remain trusted.
- Local Docker Desktop integration on 2026-11-22 verified Squid config parsing and health (`mgr:info`), public HTTP/HTTPS access, and HTTP 403 denials for loopback, RFC1918, link-local/metadata, Docker internal gateway (`172.30.0.1`), nonstandard ports, IPv6 loopback/ULA/link-local/documentation, and IPv4-mapped private addresses. Static ACL regression tests also cover CGNAT and additional reserved/documentation ranges. Direct app-container connections to public IPs and the metadata IP failed with `ENETUNREACH`. Redis 7.4 connectivity, Redis-backed host pacing, and shared robots-cache write/reuse also passed. The app container fetched `example.com` through Squid; the MCP stdio `initialize`, `tools/list`, and `research_fetch` `tools/call` round-trip returned source/evidence IDs. A startup shim strips the UTF-8 BOM that the Windows Docker Compose stdin path prepended to the first JSON-RPC frame.
- This is a reference deployment profile, not yet VPS production validation. Mixed DNS answers, DNS rebinding, redirect-to-private cases, host-gateway routes beyond `172.30.0.1`, remote Redis auth/TLS, and backup/restore remain unverified.
