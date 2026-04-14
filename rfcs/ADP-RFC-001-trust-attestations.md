# ADP-RFC-001: Trust attestations are pointers, not values

**Status:** Draft
**Author:** Jason Walko (walkojas-boop)
**Created:** 2026-04-14
**Targets:** ADP v0.1 → v0.2

## Summary

Formalize the shape of the `trust` object in `/.well-known/agent-discovery.json` to make explicit a design rule that has been implicit since v0.1: **trust fields in the discovery document are pointers, not values.** A new `trust.attestations` array is added as the canonical place for third-party attestation pointers. Verifiable claims (scores, sample sizes, freshness timestamps, signatures) are explicitly out of scope for the discovery document and live at the attestation URL where they can be verified end-to-end against a trust provider's public key.

This RFC does not deprecate any existing fields. It clarifies the intended use of the `trust` object and rejects a class of proposals that would break the spec's security model.

## Motivation

Multiple proposals across multiple downstream framework integrations have suggested adding fields like:

```json
"trust": {
  "trust_score": 0.94,
  "sample_size": 12400,
  "last_verified": "2026-04-14T00:00:00Z",
  "session_success_rate": 0.91,
  "avg_cost_per_session_usd": 0.012,
  "attestation_provider": "ProviderName",
  "attestation_url": "https://provider.example/verify/agent-xyz"
}
```

This shape is unsafe.

The `agent-discovery.json` file is served by the same domain whose trust is being asserted. Anything in the document is **self-attestation**. A compromised, hostile, or simply dishonest operator can publish `trust_score: 0.99 / sample_size: 9999999` into its own document, and a calling agent has no cryptographic basis to know it is wrong. The signature on the document, if any, only proves that the domain published it — not that the numbers are accurate.

The pattern is especially harmful for monitoring platforms that want to surface real behavioral data, because it collapses their commercial value: if any agent can publish the same `trust_score: 0.99` in its own discovery doc, a calling agent cannot distinguish a real monitored score from a forged one. Whatever signal "this agent is monitored by Provider X" was supposed to carry, it carries equally for the unmonitored agent that copy-pastes the field.

The fix is structural, not numerical: **separate the discovery document from the attestation, and put each thing in the place where it can be verified.**

## Design rule

> The `trust` object in `/.well-known/agent-discovery.json` MUST contain only **pointers** to verification endpoints. It MUST NOT contain verifiable claims (scores, sample sizes, timestamps, methodology, or any field that would have meaning only if the publisher were assumed honest).

Applied:

- **Allowed:** URLs, provider names, key references, policy identifiers — anything whose function is to direct a verifier to a separate document or service.
- **Not allowed:** numeric scores, success rates, sample counts, "last verified" timestamps, signed-by claims, anything where the calling agent would have to trust the discovery document's publisher to trust the value.

A reviewer asking "would a malicious publisher benefit from putting this field in the doc?" should answer "no" for every field in `trust`.

## Schema additions

### `trust.attestations` (new, optional)

An array of objects, each describing one third-party attestation pointer.

| Field      | Type   | Required | Description |
|------------|--------|----------|-------------|
| `provider` | string | Yes      | Human-readable provider name. Treated as opaque by verifiers. |
| `url`      | string | Yes      | URL where the verifier fetches the attestation document. MUST be HTTPS. |

The array is ordered but not ranked. A discovery document MAY surface multiple attestations from different providers. A verifier consumes the list, filters to providers whose public keys it has, fetches each remaining attestation, and decides what to do with the results — that decision is the verifier's, not the discovery document's.

#### Example

```json
{
  "agent_discovery_version": "0.2",
  "domain": "example.com",
  "services": [ ... ],
  "trust": {
    "verification_url": "https://example.com/validate",
    "public_key_url": "https://example.com/.well-known/agent.json",
    "governance_policy_url": "https://example.com/api/policy",
    "attestations": [
      {
        "provider": "AcmeAttestations",
        "url": "https://acmeattestations.example/verify/example.com"
      },
      {
        "provider": "OtherProvider",
        "url": "https://other.example/attestations/example.com"
      }
    ]
  }
}
```

### `trust.verification_url`, `trust.public_key_url`, `trust.governance_policy_url` (existing)

Unchanged. These already conform to the design rule — each is a pointer.

## What does NOT go in the discovery document

The following fields are **explicitly rejected** for inclusion in the `trust` object:

- `trust_score`, `score`, `reputation_score`, `confidence_score`
- `sample_size`, `call_count`, `session_count`
- `last_verified`, `verified_at`, `last_audited`
- `success_rate`, `failure_rate`, `error_rate`, `session_success_rate`
- `avg_latency`, `avg_cost_per_session_usd`, `cost_per_call`
- `signed_by`, `attestation_signature`, `attestation_kid`
- `attestation_provider` as a flat field (use the `attestations` array entry instead — the array form composes; the flat field forces a single provider)
- Any field whose value would change based on the publisher's behavior over time

These all describe properties of the agent that an attestation provider can measure. **They belong in the attestation document, not in the discovery document.** This is non-negotiable for the security model to work.

## Attestation document contract (sketch)

This RFC does not normatively specify the attestation document format — that's a separate working document (ADP-RFC-002, forthcoming). It does specify the minimum properties the format must have, so verifiers know what to expect when they fetch an attestation URL:

1. **Signed by the attestation provider's key**, not the discovered domain's key. Signature MUST be verifiable against a public key the verifier obtained out-of-band from the provider (not from the discovered domain).
2. **Identifies a specific subject** (agent, domain, service) using the same identifier the verifier resolved from the discovery document. A verifier MUST reject an attestation whose subject does not match the discovered domain.
3. **Carries an explicit expiry**. Attestations without an expiry MUST be treated as expired immediately by conformant verifiers.
4. **Documents its methodology** (or links to one). A score with no methodology is not actionable; a verifier can reject it without further evaluation.
5. **Distributes its signing key via a well-known JWKS-shaped endpoint** (e.g., `/.well-known/attestation-keys.json`). The discovery document MUST NOT contain the attestation provider's signing key — that key is the attestation provider's property, not the discovered domain's.

A worked example of an attestation document and the JWKS endpoint will land in ADP-RFC-002.

## Verifier behavior

A conformant ADP verifier processing the `trust.attestations` array:

1. **MUST NOT trust any field inside the discovery document as evidence of the agent's behavior.** The discovery document is a capability advertisement and a pointer set, nothing more.
2. **MAY** fetch any attestation URL whose `provider` it recognizes and trusts.
3. **MUST** verify the attestation document's signature against the provider's signing key, obtained out-of-band.
4. **MUST** reject the attestation if the subject does not match the discovered domain, the expiry has passed, or the signature does not verify.
5. **MAY** decide which attestations to weight more heavily based on local policy. The discovery document does not (and cannot) instruct the verifier on how to combine multiple attestations.

## Why a list and not a single field

Some proposals have suggested a single flat `attestation_url` + `attestation_provider` pair instead of a list. The list form is preferred for three reasons:

1. **No provider lock-in.** A flat field forces the discovered domain to pick one provider. The list lets a domain surface attestations from multiple providers, and the verifier picks which to consume.
2. **No ordering implication.** A list with two entries does not say "the first one is more important" — it says "here are two pointers, do what you want." A flat field implicitly says "this is THE attestation," which is a stronger claim than the discovery document is in a position to make.
3. **Forward compatibility.** Adding a second provider to an existing flat-field deployment is a breaking schema change. Adding a second entry to a list is not.

## Backward compatibility

ADP v0.1 documents that contain only `verification_url`, `public_key_url`, and `governance_policy_url` remain valid in v0.2. The `attestations` array is optional.

ADP v0.1 documents that contain rejected fields (`trust_score`, etc.) MUST be ignored by a v0.2-conformant verifier for those fields specifically. The presence of a rejected field MUST NOT cause the document as a whole to fail validation — the rejected fields are just dropped on read. This avoids a flag-day migration while making clear those fields are not part of the spec.

## Out of scope

- The attestation document format (ADP-RFC-002).
- Trust composition: how a verifier combines multiple attestations from multiple providers into a single decision. That is a verifier-side policy question, not a spec question.
- Provider key distribution beyond the requirement that it happen out-of-band relative to the discovery document.
- Any specific provider, including the author's own infrastructure. This RFC is provider-agnostic by design and does not name, recommend, or prefer any particular attestation provider.

## Open questions

1. Should `trust.attestations[].provider` be drawn from a registry, or remain free-form? The current draft says free-form / opaque. A registry adds gatekeeping; the lack of one means two providers could publish the same name. Verifier-side identification by URL host (rather than provider name) sidesteps the issue.
2. Should the spec define a recommended fetch policy for attestation URLs (TTL, retry, failure mode)? Currently left to verifier implementations. ADP-RFC-002 may pin this.

## Acknowledgments

This RFC was written in response to a series of well-intentioned proposals across multiple framework integrations to embed verifiable trust claims directly in the discovery document. Those proposals correctly identified the problem (calling agents need a trust signal) but the solution path — putting the value in the document — would have undermined the security model the spec needs to be useful at all. The right response was a clarifying document, not a rejection of the underlying need.

## References

- [ADP v0.1 README](../README.md)
- [ADP example.json](../example.json)
- microsoft/autogen#7575
- deepset-ai/haystack#11081
- ComposioHQ/composio#3192
- AgentOps-AI/agentops#1334
- openclaw/openclaw#66474
- openclaw/openclaw#66717
