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
    [[["vat", "ilike", "66621086"]]],
    {"fields": ["name", "vat"]},
)
if already:
    raise SystemExit("ABORT partner exists " + json.dumps(already, ensure_ascii=False))

state_id = kw(
    "res.country.state",
    "search",
    [[["code", "=", "TO"], ["country_id", "=", 31]]],
    {"limit": 1},
)[0]

company_id = kw(
    "res.partner",
    "create",
    [
        {
            "name": "Pousada Alphaville",
            "customer_rank": 1,
            "vat": "66621086000188",
            "email": "pousadaalphavile@gmail.com",
            "phone": "+55 63 99111-4440",
            "website": "https://www.pousadaalphavillepalmas.com.br/",
            "street": "Quadra 207 Sul, Alameda 06",
            "street2": "Plano Diretor Sul",
            "city": "Palmas",
            "zip": "77015-302",
            "state_id": state_id,
            "country_id": 31,
            "lang": "pt_BR",
            "comment": "WhatsApp comercial: +55 63 99111-4440. Instagram: https://www.instagram.com/pousadaalphavillepalmasto/",
        }
    ],
)
kw("res.partner", "write", [[company_id], {"is_company": True}])
contact_id = kw(
    "res.partner",
    "create",
    [
        {
            "name": "Fernando Macedo Carvalho",
            "parent_id": company_id,
            "phone": "+55 63 99216-7613",
            "customer_rank": 0,
            "lang": "pt_BR",
            "comment": "Instagram: https://www.instagram.com/fernandomacedooficial/",
        }
    ],
)
lead_id = kw(
    "crm.lead",
    "create",
    [
        {
            "name": "Agente SDR — Pousada Alphaville",
            "type": "opportunity",
            "partner_id": contact_id,
            "stage_id": 1,
            "user_id": 2,
            "team_id": 1,
            "phone": "+55 63 99216-7613",
            "website": "https://www.pousadaalphavillepalmas.com.br/",
            "description": "<p>Oportunidade nova. A proposta ainda será criada, para um agente SDR.</p>",
        }
    ],
)
kw("res.partner", "write", [[company_id], {"email": "pousadaalphavile@gmail.com"}])
kw("res.partner", "write", [[contact_id], {"email": False, "customer_rank": 0}])

company = kw(
    "res.partner",
    "read",
    [[company_id]],
    {"fields": ["name", "is_company", "vat", "email", "phone", "customer_rank", "city"]},
)
contact = kw(
    "res.partner",
    "read",
    [[contact_id]],
    {"fields": ["name", "parent_id", "email", "phone", "customer_rank"]},
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
