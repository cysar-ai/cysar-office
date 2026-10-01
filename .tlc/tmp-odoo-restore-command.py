import json
import urllib.request
from pathlib import Path

config = json.loads(Path("/Users/dp/code/cysar/github/cysar-office/.cursor/mcp.json").read_text())
url = config["mcpServers"]["easypanel"]["url"]
original = Path("/tmp/odoo-original-command.txt").read_text()


def post(payload):
    data = json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        raw = response.read().decode()
    if not raw.strip():
        return {}
    body = json.loads(raw)
    if "error" in body:
        raise SystemExit(json.dumps(body["error"])[:2000])
    return body


def tool(name, arguments):
    body = post(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )
    parsed = json.loads(body["result"]["content"][0]["text"])
    if parsed.get("error"):
        raise SystemExit(str(parsed["error"])[:2000])
    return parsed


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
post({"jsonrpc": "2.0", "method": "notifications/initialized"})
tool(
    "execute_destructive",
    {
        "procedure": "updateAppDeploy",
        "input": {
            "projectName": "cysar",
            "serviceName": "odoo",
            "deploy": {"command": original, "replicas": 1, "zeroDowntime": True},
        },
    },
)
tool(
    "execute_destructive",
    {
        "procedure": "deployAppService",
        "input": {"projectName": "cysar", "serviceName": "odoo"},
    },
)
print("COMMAND_RESTORED")
Path("/tmp/odoo-original-command.txt").unlink()
