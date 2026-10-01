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
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"service": service, "method": method, "args": args},
            "id": 1,
        }
    ).encode()
    request = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.load(response)
    if "error" in data:
        error = data["error"]
        message = error.get("data", {}).get("message") or error.get("message")
        debug = (error.get("data", {}) or {}).get("debug") or ""
        raise SystemExit(f"{message}\n{debug[-1500:]}")
    return data["result"]


uid = rpc("common", "authenticate", [env["ODOO_DB"], env["ODOO_USER"], env["ODOO_PASSWORD"], {}])
print("UID", uid)


def kw(model, method, args, kwargs=None):
    return rpc("object", "execute_kw", [env["ODOO_DB"], uid, env["ODOO_PASSWORD"], model, method, args, kwargs or {}])


kw("ir.module.module", "update_list", [])
rows = kw(
    "ir.module.module",
    "search_read",
    [[["name", "=", "contract"]]],
    {"fields": ["name", "state", "shortdesc"]},
)
print("MODULE", json.dumps(rows, ensure_ascii=False))
