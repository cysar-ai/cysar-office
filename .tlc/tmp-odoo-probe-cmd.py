import json
import re
import time
import urllib.request
from pathlib import Path

OFFICE = Path("/Users/dp/code/cysar/github/cysar-office")
PANEL = json.loads((OFFICE / ".cursor/mcp.json").read_text())["mcpServers"]["easypanel"]["url"]
COMMAND_FILE = Path("/tmp/odoo-original-command.txt")


def panel(payload):
    request = urllib.request.Request(
        PANEL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        raw = response.read().decode()
    if not raw.strip():
        return {}
    body = json.loads(raw)
    if "error" in body:
        raise SystemExit(json.dumps(body["error"])[:500])
    return body


def tool(name, arguments):
    body = panel(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )
    parsed = json.loads(body["result"]["content"][0]["text"])
    if parsed.get("error"):
        raise SystemExit(str(parsed["error"])[:500])
    return parsed


def redact(value):
    text = json.dumps(value, ensure_ascii=False)
    text = re.sub(r"--db_password=\S+", "--db_password=REDACTED", text)
    text = re.sub(r"[A-Za-z0-9+/=]{32,}", "REDACTED", text)
    return text[:2000]


panel(
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
panel({"jsonrpc": "2.0", "method": "notifications/initialized"})
current = tool(
    "execute_query",
    {"procedure": "inspectAppService", "input": {"projectName": "cysar", "serviceName": "odoo"}},
)["result"]["deploy"]["command"]
if not current.startswith("odoo "):
    raise SystemExit("ABORT command is not the odoo binary")
COMMAND_FILE.write_text(current)
COMMAND_FILE.chmod(0o600)
try:
    tool(
        "execute_destructive",
        {
            "procedure": "updateAppDeploy",
            "input": {
                "projectName": "cysar",
                "serviceName": "odoo",
                "deploy": {"command": "echo contract-probe", "replicas": 1, "zeroDowntime": True},
            },
        },
    )
    tool(
        "execute_destructive",
        {"procedure": "deployAppService", "input": {"projectName": "cysar", "serviceName": "odoo"}},
    )
    time.sleep(6)
    error = tool(
        "execute_query",
        {"procedure": "getServiceError", "input": {"projectName": "cysar", "serviceName": "odoo"}},
    )
    print(redact(error))
finally:
    tool(
        "execute_destructive",
        {
            "procedure": "updateAppDeploy",
            "input": {
                "projectName": "cysar",
                "serviceName": "odoo",
                "deploy": {"command": COMMAND_FILE.read_text(), "replicas": 1, "zeroDowntime": True},
            },
        },
    )
    tool(
        "execute_destructive",
        {"procedure": "deployAppService", "input": {"projectName": "cysar", "serviceName": "odoo"}},
    )
    COMMAND_FILE.unlink()
    print("RESTORED")
