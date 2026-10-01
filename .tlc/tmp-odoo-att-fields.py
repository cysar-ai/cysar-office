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
        message = data["error"].get("data", {}).get("message") or data["error"].get("message")
        raise SystemExit(message)
    return data["result"]


uid = rpc("common", "authenticate", [env["ODOO_DB"], env["ODOO_USER"], env["ODOO_PASSWORD"], {}])


def kw(model, method, args, kwargs=None):
    return rpc(
        "object",
        "execute_kw",
        [env["ODOO_DB"], uid, env["ODOO_PASSWORD"], model, method, args, kwargs or {}],
    )


fields = kw(
    "ir.model.fields",
    "search_read",
    [[["model", "=", "ir.attachment"], ["name", "ilike", "store"]]],
    {"fields": ["name", "ttype", "store"]},
)
print("STORE_FIELDS", json.dumps(fields))
names = kw(
    "ir.model.fields",
    "search_read",
    [[["model", "=", "ir.attachment"], ["name", "in", ["datas", "raw", "db_datas", "file_size", "checksum", "store_fname"]]]],
    {"fields": ["name", "ttype"]},
)
print("BIN_FIELDS", json.dumps(names))
datas = kw("ir.attachment", "read", [[116]], {"fields": ["datas"]})[0]["datas"]
print("ZIP_DATAS_LEN", 0 if not datas else len(datas))
pdf = kw("ir.attachment", "read", [[107]], {"fields": ["datas"]})[0]["datas"]
print("PDF_DATAS_LEN", 0 if not pdf else len(pdf))
