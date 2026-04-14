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
| `attestations` | array | No | Third-party attestation pointers. Each entry: `{provider, url}`. See [ADP-RFC-001](./rfcs/ADP-RFC-001-trust-attestations.md). |

> **Design rule:** the `trust` object contains only **pointers**. Verifiable claims (scores, sample sizes, freshness timestamps, signatures) live at the attestation URL where they can be verified end-to-end against a trust provider's public key. Embedding verifiable claims directly in the discovery document is self-attestation and is explicitly out of scope for this spec. See [ADP-RFC-001](./rfcs/ADP-RFC-001-trust-attestations.md) for the rationale and the rejected fields list.

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

| Name | Purpose | Protocol |
|------|---------|----------|
| `identity` | Agent identity verification and registration | agent.json/0.1 |
| `memory` | Persistent memory storage and recall | — |
| `governance` | Action governance and receipt generation | sift/1.0 |
| `affordances` | Structured action extraction from URLs | — |
| `debate` | Multi-agent adversarial reasoning | debate-wire-format/0.2 |
| `work` | Task marketplace for agent bounties | — |
| `content_verification` | AI content detection and certification | — |
| `regulations` | AI regulatory change tracking | — |
| `reputation` | Hash-chained, Ed25519-signed agent reputation ledger | arls/0.1 |
| `sessions` | Governed agent-to-agent session management | asp/0.1 |
| `capabilities` | Signed capability manifest registry with proof invocations | acm/0.1 |
| `preflight` | Policy preflight for agent web actions | apps/0.1 |
| `verdicts` | Debate verdict storage with precedent chains | dvf/0.1 |
| `bootstrap` | Debate session initialization with roster lock | dsb/0.1 |

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

---

## Implementations & Discussions

### Pull Requests (ADP client implementations)

| Framework | PR | Status |
|-----------|-----|--------|
| LangChain | [#36688](https://github.com/langchain-ai/langchain/pull/36688) | Open |
| Microsoft AutoGen | [#7575](https://github.com/microsoft/autogen/pull/7575) | Open |
| CrewAI | [#5425](https://github.com/crewAIInc/crewAI/pull/5425) | Open |
| AutoGPT | [#12756](https://github.com/Significant-Gravitas/AutoGPT/pull/12756) | Open |
| LlamaIndex | [#21368](https://github.com/run-llama/llama_index/pull/21368) | Open |
| Composio | [#3192](https://github.com/ComposioHQ/composio/pull/3192) | Open |
| MetaGPT | [#2006](https://github.com/FoundationAgents/MetaGPT/pull/2006) | Open |

### Feature Requests

| Project | Issue |
|---------|-------|
| AgentOps | [#1334](https://github.com/AgentOps-AI/agentops/issues/1334) |
| E2B | [#1265](https://github.com/e2b-dev/E2B/issues/1265) |
| Browser Use | [#4666](https://github.com/browser-use/browser-use/issues/4666) |
| Scrapegraph | [#1064](https://github.com/ScrapeGraphAI/Scrapegraph-ai/issues/1064) |
| Pydantic AI | [#5058](https://github.com/pydantic/pydantic-ai/issues/5058) |
| LiteLLM | [#25615](https://github.com/BerriAI/litellm/issues/25615) |
| Smolagents (HuggingFace) | [#2190](https://github.com/huggingface/smolagents/issues/2190) |
| Haystack | [#11081](https://github.com/deepset-ai/haystack/issues/11081) |
| Mem0 | [#4802](https://github.com/mem0ai/mem0/issues/4802) |
| Julep | [#1601](https://github.com/julep-ai/julep/issues/1601) |
| GPT Researcher | [#1735](https://github.com/assafelovic/gpt-researcher/issues/1735) |
| Letta | [#3305](https://github.com/letta-ai/letta/issues/3305) |
| ChatDev | [#609](https://github.com/OpenBMB/ChatDev/issues/609) |
| CAMEL | [#4002](https://github.com/camel-ai/camel/issues/4002) |

### Live Deployments

| Domain | Discovery URL | Services |
|--------|--------------|----------|
| walkosystems.com | [agent-discovery.json](https://walkosystems.com/.well-known/agent-discovery.json) | 14 |
| agents.walkosystems.com | [agent-discovery.json](https://agents.walkosystems.com/.well-known/agent-discovery.json) | 14 |
| reputation.walkosystems.com | [/v1/stats](https://reputation.walkosystems.com/v1/stats) | ARLS |
| sessions.walkosystems.com | [/v1/stats](https://sessions.walkosystems.com/v1/stats) | ASP |
| capabilities.walkosystems.com | [/v1/stats](https://capabilities.walkosystems.com/v1/stats) | ACM |
| preflight.walkosystems.com | [/v1/stats](https://preflight.walkosystems.com/v1/stats) | APPS |
| verdicts.walkosystems.com | [/v1/stats](https://verdicts.walkosystems.com/v1/stats) | DVF+DQP |
| bootstrap.walkosystems.com | [/v1/stats](https://bootstrap.walkosystems.com/v1/stats) | DSB |

### MCP Server

| Name | Repository |
|------|-----------|
| sift-agent-discovery | [GitHub](https://github.com/walkojas-boop/sift-mcp-server) |
