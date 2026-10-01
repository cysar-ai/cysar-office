import base64
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


pdf = kw("ir.attachment", "read", [[107]], {"fields": ["raw", "file_size", "store_fname"]})[0]
raw = pdf.get("raw")
print("PDF", "raw_len", 0 if not raw else len(raw), "file_size", pdf["file_size"], "stored", bool(pdf["store_fname"]))
kw(
    "ir.attachment",
    "write",
    [[117], {"raw": base64.b64encode(b"pending").decode()}],
)
row = kw("ir.attachment", "read", [[117]], {"fields": ["raw", "file_size", "store_fname", "checksum"]})[0]
print("LOG_RAW", repr(row["raw"])[:80], "SIZE", row["file_size"], "STORED", bool(row["store_fname"]))
