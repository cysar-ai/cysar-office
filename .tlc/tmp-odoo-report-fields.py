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
        raise SystemExit((data["error"].get("data") or {}).get("message") or data["error"].get("message"))
    return data["result"]


uid = rpc("common", "authenticate", [env["ODOO_DB"], env["ODOO_USER"], env["ODOO_PASSWORD"], {}])


def kw(model, method, args, kwargs=None):
    return rpc("object", "execute_kw", [env["ODOO_DB"], uid, env["ODOO_PASSWORD"], model, method, args, kwargs or {}])


rows = kw("ir.module.module", "search_read", [[["name", "=", "contract"]]], {"fields": ["state", "latest_version"]})
print("MODULE", json.dumps(rows))
fields = kw("ir.actions.report", "fields_get", [], {"attributes": ["type", "string"]})
interesting = [name for name in sorted(fields) if "bind" in name or "report" in name or name in {"model", "report_type", "report_name", "report_file"}]
print("FIELDS", ", ".join(interesting))
