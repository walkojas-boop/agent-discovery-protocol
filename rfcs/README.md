# ADP RFCs

Design notes that extend or clarify the [ADP specification](../README.md).

RFCs are intended for changes that touch the wire format, the security model, or the verifier contract — anything where downstream implementers need to know what is settled and why. RFCs are versioned, dated, and never rewritten in place; corrections happen as follow-up RFCs that supersede earlier ones.

## Index

| RFC | Status | Title |
|-----|--------|-------|
| [ADP-RFC-001](./ADP-RFC-001-trust-attestations.md) | Draft | Trust attestations are pointers, not values |

## Process

1. Open a PR adding `rfcs/ADP-RFC-NNN-short-title.md` with a Draft status header.
2. Discussion happens on the PR.
3. When the design is settled, the PR is merged with status `Accepted`.
4. Implementations follow.
5. Changes after Accepted go in a new RFC that explicitly supersedes the prior one.
