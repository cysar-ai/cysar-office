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
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)
    if "error" in data:
        raise SystemExit(str(data["error"])[:2000])
    return data["result"]


uid = rpc("common", "authenticate", [env["ODOO_DB"], env["ODOO_USER"], env["ODOO_PASSWORD"], {}])
fields = rpc(
    "object",
    "execute_kw",
    [
        env["ODOO_DB"],
        uid,
        env["ODOO_PASSWORD"],
        "ir.access",
        "fields_get",
        [],
        {"attributes": ["string", "type", "required", "relation"]},
    ],
)
for name, field in sorted(fields.items()):
    if name in {"id", "name", "model_id", "group_id", "operation", "domain", "perm_read", "perm_write", "perm_create", "perm_unlink", "active", "global"} or "perm" in name or "group" in name or "domain" in name or "model" in name or "oper" in name:
        print(f"{name}: {field['type']} req={field.get('required')} rel={field.get('relation')} {field.get('string')}")
