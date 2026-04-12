# Agent Discovery Protocol v0.1

**Status:** Draft
**Author:** Jason Walko, Walko Systems
**Date:** 2026-04-12

## Abstract

The Agent Discovery Protocol (ADP) defines a standard mechanism for domains to advertise AI agent services via a well-known JSON document. Any agent visiting any domain can immediately discover what services are available, how to authenticate, and what governance applies -- without prior knowledge of the domain's offerings.

## Motivation

AI agents currently lack a universal way to discover infrastructure services at a domain. Agents must be pre-configured with endpoints, or rely on human-provided URLs. ADP solves this by establishing a convention analogous to `robots.txt` for crawlers or `/.well-known/openid-configuration` for OAuth: a single, predictable location where agents find everything they need.

## Specification

### 1. Discovery Document Location

Every domain implementing ADP MUST serve a JSON document at:

```
https://{domain}/.well-known/agent-discovery.json
```

The document MUST be served with `Content-Type: application/json` and MUST be publicly accessible without authentication.

### 2. Document Schema

```json
{
  "agent_discovery_version": "0.1",
  "domain": "example.com",
  "services": [ ... ],
  "trust": { ... },
  "contact": "admin@example.com"
}
```

#### 2.1 Root Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_discovery_version` | string | Yes | Protocol version. Currently `"0.1"`. |
| `domain` | string | Yes | The canonical domain for this service provider. |
| `services` | array | Yes | List of available agent services. |
| `trust` | object | No | Trust and verification endpoints. |
| `contact` | string | No | Contact email for the service operator. |

#### 2.2 Service Object

Each entry in the `services` array describes one available service:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Machine-readable service identifier (e.g., `"memory"`, `"identity"`). |
| `description` | string | Yes | Human-readable description of the service. |
| `endpoint` | string | Yes | Full URL for the service API. |
| `protocol` | string | No | Wire protocol identifier if applicable. |
| `auth` | string | Yes | Authentication method: `"none"`, `"bearer"`, `"x-memory-key"`, `"optional"`. |
| `governance` | string | Yes | Governance model: `"none"`, `"sift_lite"`, `"self"`, `"signed_response"`, `"signed_certificate"`. |
| `free_tier` | boolean | Yes | Whether the service has a free usage tier. |

#### 2.3 Trust Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verification_url` | string | No | URL to validate agent identity. |
| `public_key_url` | string | No | URL to retrieve the domain's public signing key. |
| `governance_policy_url` | string | No | URL to retrieve the governance policy document. |

### 3. Cross-Domain Consistency

When a service operator runs multiple subdomains, each subdomain SHOULD serve the same discovery document. This ensures an agent that discovers any one subdomain immediately learns about all services across the operator's infrastructure.

### 4. Agent Client Behavior

An agent implementing ADP discovery SHOULD:

1. Before taking action at a domain, fetch `/.well-known/agent-discovery.json`.
2. Cache the result for a reasonable TTL (recommended: 1 hour).
3. Use discovered endpoints rather than hardcoded URLs.
4. Respect the `auth` field to determine what credentials are needed.
5. Respect the `governance` field to understand what action oversight applies.

### 5. Service Name Registry

The following service names are defined by this specification:

| Name | Purpose |
|------|---------|
| `identity` | Agent identity verification and registration |
| `memory` | Persistent memory storage and recall |
| `governance` | Action governance and receipt generation |
| `affordances` | Structured action extraction from URLs |
| `debate` | Multi-agent adversarial reasoning |
| `work` | Task marketplace for agent bounties |
| `content_verification` | AI content detection and certification |
| `regulations` | AI regulatory change tracking |

Implementations MAY define additional service names.

### 6. CORS

Discovery documents SHOULD include `Access-Control-Allow-Origin: *` to permit cross-origin agent access from browser-based environments.

## Security Considerations

- Discovery documents MUST be served over HTTPS in production.
- Agents SHOULD verify TLS certificates when fetching discovery documents.
- The discovery document itself does not grant access; agents must still authenticate per the `auth` field of each service.
- Operators SHOULD monitor discovery endpoint access for abuse patterns.

## Reference Implementation

A Python client library is available at:
```
/root/emerald/workspace/src/agent_discovery.py
```

## Walko Systems Implementation

Walko Systems serves the discovery document at:
- `walkosystems.com/.well-known/agent-discovery.json`
- `agents.walkosystems.com/.well-known/agent-discovery.json`
- `memory.walkosystems.com/.well-known/agent-discovery.json`
- `slop.walkosystems.com/.well-known/agent-discovery.json`
- `regs.walkosystems.com/.well-known/agent-discovery.json`

All endpoints return the identical document, ensuring any entry point leads to full service discovery.
