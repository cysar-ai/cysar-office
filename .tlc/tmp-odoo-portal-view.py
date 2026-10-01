import json
import urllib.request
from pathlib import Path

env = {}
for line in Path("/Users/dp/code/cysar/github/cysar-office/.env").read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    env[key.strip()] = value.strip().strip('"').strip("'")


def rpc(service, method, args):
    body = json.dumps({"jsonrpc": "2.0", "method": "call", "params": {"service": service, "method": method, "args": args}, "id": 1}).encode()
    request = urllib.request.Request("https://crm-office.cysar.ai/jsonrpc", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)
    if "error" in data:
        raise SystemExit((data["error"].get("data") or {}).get("message") or data["error"])
    return data["result"]


uid = rpc("common", "authenticate", [env["ODOO_DB"], env["ODOO_USER"], env["ODOO_PASSWORD"], {}])
rows = rpc(
    "object",
    "execute_kw",
    [env["ODOO_DB"], uid, env["ODOO_PASSWORD"], "ir.ui.view", "read", [[573]], {"fields": ["name", "key", "arch_db"]}],
)
row = rows[0]
arch = row["arch_db"]
print(row["name"], row["key"])
print(arch)
