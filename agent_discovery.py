"""
Agent Discovery Protocol - Client Library
Discover agent services at any domain implementing ADP v0.1.

Usage:
    from agent_discovery import discover

    services = discover("walkosystems.com")
    memory = services.get_service("memory")
    # {"name": "memory", "endpoint": "https://memory.walkosystems.com/remember", ...}

    all_services = services.list_services()
    # ["identity", "memory", "governance", "affordances", ...]
"""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


WELL_KNOWN_PATH = "/.well-known/agent-discovery.json"
DEFAULT_TIMEOUT = 10
SUPPORTED_VERSION = "0.1"


class DiscoveryError(Exception):
    """Raised when discovery fails."""


@dataclass
class DiscoveryResult:
    """Parsed agent discovery document."""

    version: str
    domain: str
    services: list = field(default_factory=list)
    trust: dict = field(default_factory=dict)
    contact: str = ""
    _raw: dict = field(default_factory=dict, repr=False)

    def get_service(self, name: str) -> Optional[dict]:
        """Get a service by name. Returns None if not found."""
        for svc in self.services:
            if svc.get("name") == name:
                return dict(svc)
        return None

    def list_services(self) -> list:
        """Return list of available service names."""
        return [svc["name"] for svc in self.services if "name" in svc]

    def get_endpoint(self, name: str) -> Optional[str]:
        """Get just the endpoint URL for a service."""
        svc = self.get_service(name)
        return svc["endpoint"] if svc else None

    def get_free_services(self) -> list:
        """Return services that have a free tier."""
        return [dict(svc) for svc in self.services if svc.get("free_tier")]

    def raw(self) -> dict:
        """Return the raw parsed JSON."""
        return dict(self._raw)


def discover(domain: str, timeout: int = DEFAULT_TIMEOUT) -> DiscoveryResult:
    """
    Fetch and parse the agent discovery document from a domain.

    Args:
        domain: The domain to discover (e.g., "walkosystems.com").
        timeout: Request timeout in seconds.

    Returns:
        DiscoveryResult with parsed services.

    Raises:
        DiscoveryError: If the document cannot be fetched or parsed.
    """
    domain = domain.strip().rstrip("/")
    if domain.startswith("http://") or domain.startswith("https://"):
        url = domain.rstrip("/") + WELL_KNOWN_PATH
    else:
        url = f"https://{domain}{WELL_KNOWN_PATH}"

    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "AgentDiscovery/0.1 (https://walkosystems.com)"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise DiscoveryError(f"HTTP {resp.status} from {url}")
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise DiscoveryError(f"Failed to fetch {url}: {e}") from e
    except json.JSONDecodeError as e:
        raise DiscoveryError(f"Invalid JSON from {url}: {e}") from e

    version = data.get("agent_discovery_version", "")
    if version != SUPPORTED_VERSION:
        raise DiscoveryError(
            f"Unsupported version '{version}' (expected '{SUPPORTED_VERSION}')"
        )

    return DiscoveryResult(
        version=version,
        domain=data.get("domain", domain),
        services=data.get("services", []),
        trust=data.get("trust", {}),
        contact=data.get("contact", ""),
        _raw=data,
    )


def discover_service(domain: str, service_name: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[dict]:
    """
    Convenience: discover a domain and return a single service.

    Args:
        domain: The domain to discover.
        service_name: The service to look up.
        timeout: Request timeout in seconds.

    Returns:
        Service dict or None if not found.
    """
    result = discover(domain, timeout=timeout)
    return result.get_service(service_name)


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "walkosystems.com"
    print(f"Discovering services at {target}...")
    try:
        result = discover(target)
        print(f"Domain: {result.domain}")
        print(f"Version: {result.version}")
        print(f"Services ({len(result.services)}):")
        for svc in result.services:
            auth = svc.get("auth", "none")
            free = "free" if svc.get("free_tier") else "paid"
            print(f"  - {svc['name']}: {svc['endpoint']} [{auth}, {free}]")
        if result.trust:
            print(f"Trust:")
            for k, v in result.trust.items():
                print(f"  {k}: {v}")
        print(f"Contact: {result.contact}")
    except DiscoveryError as e:
        print(f"Discovery failed: {e}", file=sys.stderr)
        sys.exit(1)
