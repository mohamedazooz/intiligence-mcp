# Isolated Egress Deployment

## Security objective

Run the MCP process on a Docker network with no direct external route. The only permitted outbound HTTP(S) path is a dedicated Squid proxy attached to both the isolated application network and an external egress network.

The application validates every target URL and redirect hop. The proxy independently rejects non-public destination ranges. This is defense in depth, not a substitute for host/cloud firewall policy.

## Network topology

- `intiligence-mcp` joins only `internal_net` (`172.30.0.0/24`, Docker `internal: true`).
- `egress-proxy` joins `internal_net` and `egress_net`.
- The proxy listens on TCP/3128 only inside the Docker network; no host port is published.
- The MCP container has no direct external route and must use `http://egress-proxy:3128`.
- Squid permits only the app subnet, HTTP/HTTPS safe ports, and public destination IPs. It denies loopback, private, link-local, CGNAT, documentation, benchmark, multicast, reserved, IPv6 ULA, IPv6 link-local, and selected transition ranges.
- The app's `INTILIGENCE_REQUIRE_EGRESS_PROXY=true` makes missing proxy configuration fail closed.

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

Stop the proxy:

```sh
docker compose -f compose.yaml down
```

The named `intiligence_data` volume persists SQLite source/evidence/claim data. Back it up before destructive operations.

## Required production controls

1. Pin both base images by immutable digest after the first trusted build; update them through reviewed dependency-update PRs. The Dockerfiles intentionally use maintained Debian/Python tags as build inputs, not immutable production attestations.
2. Apply host/cloud firewall rules so only required inbound administration and outbound DNS/HTTPS for the proxy are allowed. Docker network isolation does not replace host firewall policy.
3. Do not attach browser workers, parsers, or arbitrary sidecars to `egress_net`. Give each worker its own isolated network and explicit proxy policy.
4. Validate the exact Squid version and ACL behavior in staging, including IPv4, IPv6, redirects, CONNECT, mixed DNS answers, metadata addresses, and attempts to reach the Docker host/gateway.
5. Do not enable `INTILIGENCE_ALLOW_PRIVATE_NETWORKS` in this profile.
6. Use a dedicated production secret/configuration mechanism and image scanning before deployment.
7. This profile is not yet a complete production deployment: no TLS ingress, remote MCP transport, authentication, PostgreSQL, centralized audit, or tested backup/restore is included.

## Limitations

- Squid ACLs are an additional destination filter; app-side DNS validation and pinned resolver remain enabled. Proxy-side DNS resolution and ACL behavior must be integration-tested on the deployed Squid build.
- Docker `internal: true` isolates the app network from external routing, but Docker daemon/host administrators remain trusted.
- This is a reference deployment profile. It has not been deployed to a VPS or verified against a live Docker daemon in this development session.
