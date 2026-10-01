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

URL = "https://crm-office.cysar.ai/jsonrpc"


def rpc(service, method, args):
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"service": service, "method": method, "args": args},
            "id": 1,
        }
    ).encode()
    request = urllib.request.Request(URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)
    if "error" in data:
        error = data["error"]
        raise SystemExit(error.get("data", {}).get("message") or error.get("message"))
    return data["result"]


uid = rpc("common", "authenticate", [env["ODOO_DB"], env["ODOO_USER"], env["ODOO_PASSWORD"], {}])


def kw(model, method, args, kwargs=None):
    return rpc("object", "execute_kw", [env["ODOO_DB"], uid, env["ODOO_PASSWORD"], model, method, args, kwargs or {}])


names = ["portal", "base_import_module", "account", "product", "contract"]
rows = kw(
    "ir.module.module",
    "search_read",
    [[["name", "in", names]]],
    {"fields": ["name", "state"]},
)
print(json.dumps(rows, ensure_ascii=False))
