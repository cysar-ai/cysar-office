import json
import urllib.request
from pathlib import Path

config = json.loads(Path("/Users/dp/code/cysar/github/cysar-office/.cursor/mcp.json").read_text())
url = config["mcpServers"]["easypanel"]["url"]


def post(payload, session=None):
    data = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session:
        headers["Mcp-Session-Id"] = session
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read().decode()
        return response.headers.get("Mcp-Session-Id"), body


session, init_body = post(
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
print("SESSION", bool(session))
print("INIT", init_body[:400])
post({"jsonrpc": "2.0", "method": "notifications/initialized"}, session)


def call(name, arguments):
    _, body = post(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        session,
    )
    return body


query = " ".join(__import__("sys").argv[1:]) or "backup postgres database"
tool = "search_procedures"
arguments = {"query": query, "limit": 5}
if query.startswith("EXEC "):
    tool, raw = query.split(" ", 1)
    name, payload = raw.split(" ", 1)
    tool = name
    arguments = json.loads(payload)
print(call(tool, arguments)[:12000])
