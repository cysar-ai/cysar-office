import json
import sys
import urllib.request
from pathlib import Path

config = json.loads(Path("/Users/dp/code/cysar/github/cysar-office/.cursor/mcp.json").read_text())
url = config["mcpServers"]["easypanel"]["url"]


def post(payload):
    data = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read().decode()


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
tool = sys.argv[1]
arguments = json.loads(sys.argv[2])
body = post(
    {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
)
print(body[:20000])
