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
        raise SystemExit(str(data["error"])[:1500])
    return data["result"]


uid = rpc("common", "authenticate", [env["ODOO_DB"], env["ODOO_USER"], env["ODOO_PASSWORD"], {}])


def kw(model, method, args, kwargs=None):
    return rpc("object", "execute_kw", [env["ODOO_DB"], uid, env["ODOO_PASSWORD"], model, method, args, kwargs or {}])


for xmlid in [
    "account.model_account_move",
    "crm.model_crm_lead",
    "account.group_account_invoice",
    "account.group_account_manager",
]:
    found = kw("ir.model.data", "search_read", [[["module", "=", xmlid.split(".")[0]], ["name", "=", xmlid.split(".", 1)[1]]]], {"fields": ["module", "name", "model", "res_id"], "limit": 1})
    print(xmlid, json.dumps(found, ensure_ascii=False))
