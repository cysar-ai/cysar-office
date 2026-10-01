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
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.load(response)
    if "error" in data:
        error = data["error"]
        message = (error.get("data") or {}).get("message") or error.get("message")
        debug = (error.get("data") or {}).get("debug") or ""
        raise SystemExit(f"{message}\n{debug[-1200:]}")
    return data["result"]


uid = rpc("common", "authenticate", [env["ODOO_DB"], env["ODOO_USER"], env["ODOO_PASSWORD"], {}])


def kw(model, method, args, kwargs=None):
    return rpc(
        "object",
        "execute_kw",
        [env["ODOO_DB"], uid, env["ODOO_PASSWORD"], model, method, args, kwargs or {}],
    )


already = kw(
    "res.partner",
    "search_read",
    [[["email", "=", "marinhocreativehub@gmail.com"]]],
    {"fields": ["name", "email"]},
)
if already:
    raise SystemExit("ABORT partner exists " + json.dumps(already, ensure_ascii=False))

company_id = kw(
    "res.partner",
    "create",
    [
        {
            "name": "Marinho Creative Hub",
            "supplier_rank": 1,
            "customer_rank": 0,
            "email": "marinhocreativehub@gmail.com",
            "website": "https://www.marinhocreativehub.tech/",
            "country_id": 31,
            "lang": "pt_BR",
            "comment": "Fornecedor/parceiro.",
        }
    ],
)
kw("res.partner", "write", [[company_id], {"is_company": True}])
contact_id = kw(
    "res.partner",
    "create",
    [
        {
            "name": "Nicollas Marinho",
            "parent_id": company_id,
            "email": "marinhocreativehub@gmail.com",
            "phone": "+55 63 99278-2591",
            "customer_rank": 0,
            "supplier_rank": 0,
            "lang": "pt_BR",
        }
    ],
)
kw("res.partner", "write", [[company_id], {"email": "marinhocreativehub@gmail.com", "customer_rank": 0, "supplier_rank": 1}])
kw("res.partner", "write", [[contact_id], {"customer_rank": 0, "supplier_rank": 0}])

darley = kw("res.users", "read", [[2]], {"fields": ["partner_id", "tz"]})[0]
event_id = kw(
    "calendar.event",
    "create",
    [
        {
            "name": "Reunião com Nicollas Marinho — Marinho Creative Hub",
            "start": "2026-09-30 22:00:00",
            "stop": "2026-09-30 23:00:00",
            "user_id": 2,
            "partner_ids": [(6, 0, [contact_id, darley["partner_id"][0]])],
            "description": "Reunião com Nicollas Marinho, fornecedor/parceiro da Marinho Creative Hub. Telefone +55 63 99278-2591.",
        }
    ],
    {"context": {"tz": "America/Fortaleza"}},
)

company = kw(
    "res.partner",
    "read",
    [[company_id]],
    {"fields": ["name", "is_company", "email", "website", "supplier_rank", "customer_rank"]},
)
contact = kw(
    "res.partner",
    "read",
    [[contact_id]],
    {"fields": ["name", "parent_id", "email", "phone", "supplier_rank", "customer_rank"]},
)
event = kw(
    "calendar.event",
    "read",
    [[event_id]],
    {"fields": ["name", "start", "stop", "partner_ids", "user_id"]},
)
print("USER", json.dumps(darley, ensure_ascii=False))
print("COMPANY", json.dumps(company, ensure_ascii=False))
print("CONTACT", json.dumps(contact, ensure_ascii=False))
print("EVENT", json.dumps(event, ensure_ascii=False))
