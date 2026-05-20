"""
Regression tests for nginx.conf to prevent the stale-DNS 502 bug.

Root cause: nginx resolves upstream hostnames at startup and caches the IP.
When a backend/frontend container restarts it gets a new IP, so all proxied
requests immediately return 502 Bad Gateway — without any code change.

Fix: use Docker's embedded DNS resolver (127.0.0.11) with `set $var` variables
for every proxy_pass so nginx re-resolves hostnames on each request cycle.

These tests enforce that fix so it cannot silently regress.
"""

import os
import re

import pytest

# Path is relative to the repo root, resolved from this file's location.
NGINX_CONF = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "..",
        "services",
        "nginx",
        "nginx.conf",
    )
)


@pytest.fixture(scope="module")
def nginx_conf_text():
    if not os.path.exists(NGINX_CONF):
        pytest.skip(
            f"nginx.conf not found at {NGINX_CONF} — "
            "this is expected when running inside Docker. "
            "Run on the host to validate nginx configuration."
        )
    with open(NGINX_CONF) as f:
        return f.read()


# ── DNS Resolver ──────────────────────────────────────────────────────────────


def test_docker_resolver_is_present(nginx_conf_text):
    """
    Docker's embedded DNS server must be declared as the resolver.
    Without this, proxy_pass variable resolution won't work and nginx
    falls back to compile-time caching — reproducing the 502 bug.
    """
    assert "resolver 127.0.0.11" in nginx_conf_text, (
        "Missing 'resolver 127.0.0.11' in nginx.conf. "
        "Without Docker's DNS resolver, upstream IPs are cached at startup "
        "and stale after container restarts, causing 502 Bad Gateway."
    )


def test_resolver_ttl_is_set(nginx_conf_text):
    """
    The resolver must specify a valid= TTL so nginx periodically re-resolves.
    An absent TTL defaults to the DNS response TTL (often 0), which may
    cause excessive DNS lookups or no re-resolution at all.
    """
    assert re.search(
        r"resolver\s+127\.0\.0\.11\s+valid=\d+s", nginx_conf_text
    ), "resolver directive must include a 'valid=<seconds>s' TTL, e.g. 'valid=30s'."


# ── Static upstream blocks ────────────────────────────────────────────────────


def test_no_static_upstream_backend(nginx_conf_text):
    """
    Static 'upstream backend { server backend:8000; }' blocks lock the IP
    at startup. They must not exist when dynamic resolver variables are used.
    """
    # Match upstream blocks that reference backend or frontend service names
    static_upstream = re.search(r"upstream\s+(backend|frontend)\s*\{", nginx_conf_text)
    assert static_upstream is None, (
        f"Found a static 'upstream {static_upstream.group(1)}' block in nginx.conf. "
        "Static upstreams cache the IP at startup — remove them and use "
        "'set $var http://host:port' with proxy_pass $var$request_uri instead."
    )


# ── Dynamic proxy_pass variables ─────────────────────────────────────────────


def _get_https_server_block(text: str) -> str:
    """Extract the HTTPS (port 443) server block from the config."""
    # Find the block starting at 'listen 443'
    match = re.search(
        r"(server\s*\{[^}]*listen\s+443[^}]*(?:\{[^}]*\}[^}]*)*\})", text, re.DOTALL
    )
    if match:
        return match.group(0)
    # Fallback: return everything after the first 'listen 443' occurrence
    idx = text.find("listen 443")
    return text[idx:] if idx != -1 else text


def test_all_proxy_pass_use_variables(nginx_conf_text):
    """
    Every proxy_pass in the HTTPS server block must use a variable ($var),
    not a hard-coded hostname. Hard-coded hostnames bypass the resolver and
    cache the IP at startup, which is the root cause of the 502 bug.
    """
    https_block = _get_https_server_block(nginx_conf_text)
    proxy_pass_lines = re.findall(r"proxy_pass\s+([^;]+);", https_block)

    assert proxy_pass_lines, "No proxy_pass directives found in HTTPS server block."

    bad_lines = [
        line.strip()
        for line in proxy_pass_lines
        if "$" not in line  # No variable → IP cached at startup
    ]

    assert not bad_lines, (
        f"These proxy_pass directives use hard-coded upstreams (no variable): "
        f"{bad_lines}. "
        "Replace with 'set $var http://host:port;' + 'proxy_pass $var$request_uri;'."
    )


def test_backend_variable_uses_port(nginx_conf_text):
    """
    Backend set variables must include the explicit port (:8000) so Docker DNS
    resolves to the correct container without relying on a named upstream block.
    """
    # Find all set directives that point to the backend service
    backend_sets = re.findall(r"set\s+\$\w+\s+http://backend:(\d+)", nginx_conf_text)
    assert backend_sets, (
        "No 'set $var http://backend:<port>' directives found. "
        "Backend proxy variables must explicitly include the port."
    )
    for port in backend_sets:
        assert (
            port == "8000"
        ), f"Backend set variable uses unexpected port {port} (expected 8000)."


def test_frontend_variable_uses_port(nginx_conf_text):
    """
    Frontend set variables must include the explicit port (:3000).
    """
    frontend_sets = re.findall(r"set\s+\$\w+\s+http://frontend:(\d+)", nginx_conf_text)
    assert frontend_sets, (
        "No 'set $var http://frontend:<port>' directives found. "
        "Frontend proxy variables must explicitly include the port."
    )
    for port in frontend_sets:
        assert (
            port == "3000"
        ), f"Frontend set variable uses unexpected port {port} (expected 3000)."


# ── Timeouts ─────────────────────────────────────────────────────────────────


def test_api_proxy_read_timeout_is_generous(nginx_conf_text):
    """
    The API location block must have a proxy_read_timeout >= 120s.
    Cover letter generation via Temporal can take 30-90s; a 60s timeout
    silently kills in-flight requests.
    """
    # Extract the /api/ location block
    api_block_match = re.search(
        r"location\s+/api/\s*\{(.*?)\}", nginx_conf_text, re.DOTALL
    )
    assert api_block_match, "Could not find 'location /api/' block in nginx.conf."

    api_block = api_block_match.group(1)
    timeout_match = re.search(r"proxy_read_timeout\s+(\d+)s", api_block)
    assert timeout_match, "No proxy_read_timeout set in the /api/ location block."

    timeout_val = int(timeout_match.group(1))
    assert timeout_val >= 120, (
        f"proxy_read_timeout in /api/ is {timeout_val}s — too low. "
        "Must be >= 120s to survive cover letter generation latency."
    )
