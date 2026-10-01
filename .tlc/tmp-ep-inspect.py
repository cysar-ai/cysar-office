import json
import re
import urllib.request
from pathlib import Path

config = json.loads(Path("/Users/dp/code/cysar/github/cysar-office/.cursor/mcp.json").read_text())
url = config["mcpServers"]["easypanel"]["url"]


def post(payload, parse=True):
    data = json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read().decode()
    if not parse:
        return raw
    return json.loads(raw)


post(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "cysar-office", "version": "1.0"},
        },
    }
)
post({"jsonrpc": "2.0", "method": "notifications/initialized"}, parse=False)
body = post(
    {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "execute_query",
            "arguments": {
                "procedure": "inspectAppService",
                "input": {"projectName": "cysar", "serviceName": "odoo"},
            },
        },
    }
)
text = body["result"]["content"][0]["text"]
result = json.loads(text)["result"]


def redact(value, key=""):
    if isinstance(value, dict):
        return {k: redact(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str) and key.lower() in {"env", "password", "token", "secret"}:
        return f"<redacted {len(value)} chars>"
    if isinstance(value, str) and key == "command":
        return re.sub(r"(password|token|secret)=\S+", r"\1=<redacted>", value, flags=re.I)
    return value


print(json.dumps(redact(result), ensure_ascii=False, indent=2)[:8000])
