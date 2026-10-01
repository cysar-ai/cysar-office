import json
import re
import urllib.request
from pathlib import Path

PANEL = json.loads(Path("/Users/dp/code/cysar/github/cysar-office/.cursor/mcp.json").read_text())["mcpServers"]["easypanel"]["url"]


def panel(payload):
    request = urllib.request.Request(
        PANEL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read().decode()
    if not raw.strip():
        return {}
    return json.loads(raw)


def tool(name, arguments):
    body = panel(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
    )
    return json.loads(body["result"]["content"][0]["text"])


def scrub(value):
    if isinstance(value, dict):
        clean = {}
        for key, item in value.items():
            if key in {"command", "env", "token", "password"}:
                clean[key] = "REDACTED" if not item else f"<set {len(str(item))} chars>"
            else:
                clean[key] = scrub(item)
        return clean
    if isinstance(value, list):
        return [scrub(item) for item in value[:8]]
    if isinstance(value, str) and re.search(r"password|token|secret", value, re.I):
        return "REDACTED"
    return value


panel(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "cysar-office", "version": "1.0"}},
    }
)
panel({"jsonrpc": "2.0", "method": "notifications/initialized"})
inspected = tool(
    "execute_query",
    {"procedure": "inspectAppService", "input": {"projectName": "cysar", "serviceName": "odoo"}},
)["result"]
print("TOP", sorted(inspected.keys()))
print("DEPLOY_KEYS", sorted(inspected.get("deploy", {}).keys()))
print(json.dumps(scrub({key: inspected[key] for key in inspected if key not in {"env", "source"}}), ensure_ascii=False)[:2500])
