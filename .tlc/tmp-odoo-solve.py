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
        raise SystemExit(f"{message}\n{debug[-1500:]}")
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
    [[["name", "=", "Solve Gestão e Negócios"], ["is_company", "=", True]]],
    {"fields": ["id"]},
)
if already:
    raise SystemExit("ABORT company exists " + json.dumps(already))

company_id = kw(
    "res.partner",
    "create",
    [
        {
            "name": "Solve Gestão e Negócios",
            "is_company": True,
            "customer_rank": 1,
            "website": "https://solvegestao.com.br",
            "phone": "+55 63 98459-9181",
            "country_id": 31,
            "lang": "pt_BR",
            "comment": "Cliente cadastrado a partir da reunião de 23/09/2026. Atua com financiamento empresarial e rural, consórcios, capital de giro e serviços complementares.",
        }
    ],
)
kw(
    "res.partner",
    "write",
    [
        [20],
        {
            "name": "Francieli Bernardi",
            "parent_id": company_id,
            "phone": "+55 63 98459-9181",
            "lang": "pt_BR",
            "customer_rank": 1,
        },
    ],
)

description = """<p>Propostas apresentadas em 28/09/2026, depois da reunião de 23/09/2026.</p>
<ul>
<li>Agenda MVP: a equipe da Solve constrói e a Cysar conduz. 10 encontros em 5 semanas. R$ 3.000,00 por ciclo, ou 2x de R$ 1.500,00.</li>
<li>Projeto MVP: a Cysar constrói. Capacidade mínima de 160 horas, em 6 a 8 semanas, a partir de R$ 16.000,00, ou 2x de R$ 8.000,00. O valor final fica para depois da análise de requisitos.</li>
</ul>
<p>A Solve ainda escolhe o caminho. Contato: Francieli Bernardi.</p>"""

lead_id = kw(
    "crm.lead",
    "create",
    [
        {
            "name": "Proposta MVP — Solve Gestão e Negócios",
            "type": "opportunity",
            "partner_id": 20,
            "stage_id": 3,
            "user_id": 2,
            "team_id": 1,
            "phone": "+55 63 98459-9181",
            "email_from": "francieli@solvegestao.com",
            "website": "https://solvegestao.com.br",
            "description": description,
            "date_open": "2026-09-28 15:00:00",
        }
    ],
)
activity_id = kw(
    "mail.activity",
    "create",
    [
        {
            "res_model_id": 1301,
            "res_id": lead_id,
            "activity_type_id": 4,
            "summary": "Retorno da proposta",
            "date_deadline": "2026-09-30",
            "user_id": 2,
            "note": "<p>Retornar o contato da Francieli sobre as propostas Agenda MVP e Projeto MVP apresentadas em 28/09/2026.</p>",
        }
    ],
)
lead = kw(
    "crm.lead",
    "read",
    [[lead_id]],
    {"fields": ["name", "partner_id", "stage_id", "email_from", "date_open"]},
)
company_email = kw("res.partner", "read", [[company_id]], {"fields": ["name", "email", "phone"]})
contact = kw("res.partner", "read", [[20]], {"fields": ["name", "parent_id", "email", "phone"]})
activity = kw("mail.activity", "read", [[activity_id]], {"fields": ["summary", "date_deadline", "user_id"]})
print("COMPANY", json.dumps(company_email, ensure_ascii=False))
print("CONTACT", json.dumps(contact, ensure_ascii=False))
print("LEAD", json.dumps(lead, ensure_ascii=False))
print("ACTIVITY", json.dumps(activity, ensure_ascii=False))
