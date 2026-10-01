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
    [[["name", "=", "Skyller"], ["is_company", "=", True]]],
    {"fields": ["id", "name"]},
)
if already:
    raise SystemExit("ABORT company exists " + json.dumps(already))

company_id = kw(
    "res.partner",
    "create",
    [
        {
            "name": "Skyller",
            "customer_rank": 1,
            "website": "https://skyller.ai/",
            "country_id": 31,
            "lang": "pt_BR",
        }
    ],
)
kw("res.partner", "write", [[company_id], {"is_company": True}])
contact_id = kw(
    "res.partner",
    "create",
    [
        {
            "name": "Adriano Fante",
            "parent_id": company_id,
            "phone": "+55 63 99287-8781",
            "customer_rank": 0,
            "lang": "pt_BR",
        }
    ],
)
lead_id = kw(
    "crm.lead",
    "create",
    [
        {
            "name": "Mentoria — Skyller",
            "type": "opportunity",
            "partner_id": contact_id,
            "stage_id": 1,
            "user_id": 2,
            "team_id": 1,
            "phone": "+55 63 99287-8781",
            "website": "https://skyller.ai/",
            "description": "<p>Oportunidade nova de mentoria.</p>",
        }
    ],
)
kw("res.partner", "write", [[contact_id], {"customer_rank": 0}])

company = kw(
    "res.partner",
    "read",
    [[company_id]],
    {"fields": ["name", "is_company", "website", "email", "customer_rank"]},
)
contact = kw(
    "res.partner",
    "read",
    [[contact_id]],
    {"fields": ["name", "parent_id", "phone", "email", "customer_rank"]},
)
lead = kw(
    "crm.lead",
    "read",
    [[lead_id]],
    {"fields": ["name", "partner_id", "stage_id", "expected_revenue", "type"]},
)
print("COMPANY", json.dumps(company, ensure_ascii=False))
print("CONTACT", json.dumps(contact, ensure_ascii=False))
print("LEAD", json.dumps(lead, ensure_ascii=False))
