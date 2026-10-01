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
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"service": service, "method": method, "args": args},
            "id": 1,
        }
    ).encode()
    request = urllib.request.Request(
        "https://crm-office.cysar.ai/jsonrpc",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)
    if "error" in data:
        raise SystemExit(str(data["error"])[:1500])
    return data["result"]


uid = rpc("common", "authenticate", [env["ODOO_DB"], env["ODOO_USER"], env["ODOO_PASSWORD"], {}])


def kw(model, method, args, kwargs=None):
    return rpc(
        "object",
        "execute_kw",
        [env["ODOO_DB"], uid, env["ODOO_PASSWORD"], model, method, args, kwargs or {}],
    )


rows = kw(
    "ir.attachment",
    "search_read",
    [[["name", "ilike", "oca-contract"]]],
    {"fields": ["id", "name", "file_size", "store_fname", "mimetype", "checksum"]},
)
print(json.dumps(rows, ensure_ascii=False))
known = kw(
    "ir.attachment",
    "search_read",
    [[["id", "=", 107]]],
    {"fields": ["id", "name", "file_size", "store_fname", "checksum"]},
)
print("KNOWN", json.dumps(known, ensure_ascii=False)[:500])
