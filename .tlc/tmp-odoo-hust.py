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

PDF = Path(
    "/Users/dp/.cursor/projects/Users-dp-code-cysar-github-cysar-office/attachments/7e767eb0-2b5d-4f0e-ad04-f89c12b90b6a/Proposta_Executiva_HUST_Darley_Passarin_Cysar.pdf"
)


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
    with urllib.request.urlopen(request, timeout=180) as response:
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
    [[["vat", "ilike", "42784960"]]],
    {"fields": ["name", "vat"]},
)
if already:
    raise SystemExit("ABORT partner exists " + json.dumps(already, ensure_ascii=False))

company_id = kw(
    "res.partner",
    "create",
    [
        {
            "name": "Hust",
            "customer_rank": 1,
            "vat": "42784960000130",
            "website": "https://hustapp.com",
            "country_id": 31,
            "lang": "pt_BR",
            "comment": "Proposta de 01/09/2026. Posicionamento citado: atendimento multicanal, CRM e automação. Nome no WhatsApp: Hust App — Chatbot e IA.",
        }
    ],
)
kw("res.partner", "write", [[company_id], {"is_company": True}])
contact_id = kw(
    "res.partner",
    "create",
    [
        {
            "name": "Italo Tavares Lima",
            "parent_id": company_id,
            "function": "Sócio",
            "phone": "+55 63 98457-0884",
            "customer_rank": 0,
            "lang": "pt_BR",
            "comment": "Nome no WhatsApp: Italo Hust. Italo Lima — Hust App — Chatbot e IA.",
        }
    ],
)

description = """<p>Proposta executiva de 01/09/2026. Darley Passarin como CEO da Hust, pela Cysar Tecnologia Ltda.</p>
<ul>
<li>Honorários: R$ 15.000,00 por mês.</li>
<li>Faturamento mensal, com vencimento a definir em contrato.</li>
<li>Contratação mensal continuada, revisão inicial aos 90 dias e aviso prévio de 30 dias.</li>
<li>Equipe, ferramentas, mídia, projetos específicos e viagens ficam fora dos honorários.</li>
</ul>"""
lead_id = kw(
    "crm.lead",
    "create",
    [
        {
            "name": "Direção executiva — Hust",
            "type": "opportunity",
            "partner_id": contact_id,
            "stage_id": 3,
            "user_id": 2,
            "team_id": 1,
            "phone": "+55 63 98457-0884",
            "website": "https://hustapp.com",
            "expected_revenue": 0.0,
            "recurring_revenue": 15000.0,
            "recurring_plan": 1,
            "description": description,
            "date_open": "2026-09-01 15:00:00",
        }
    ],
)
kw("res.partner", "write", [[company_id], {"email": False}])
kw("res.partner", "write", [[contact_id], {"email": False, "customer_rank": 0}])

found = kw(
    "product.product",
    "search",
    [[["name", "=", "Direção executiva"]]],
    {"limit": 1},
)
if found:
    product_id = found[0]
else:
    template = kw(
        "product.template",
        "create",
        [
            {
                "name": "Direção executiva",
                "type": "service",
                "list_price": 15000.0,
                "sale_ok": True,
                "purchase_ok": False,
                "uom_id": 1,
                "taxes_id": [(6, 0, [])],
                "supplier_taxes_id": [(6, 0, [])],
                "invoice_policy": "order",
                "service_tracking": "no",
            }
        ],
    )
    product_id = kw("product.template", "read", [[template]], {"fields": ["product_variant_id"]})[0][
        "product_variant_id"
    ][0]

order_id = kw(
    "sale.order",
    "create",
    [
        {
            "partner_id": company_id,
            "opportunity_id": lead_id,
            "user_id": 2,
            "team_id": 1,
            "company_id": 1,
            "date_order": "2026-09-01 15:00:00",
            "note": "Proposta de 01/09/2026. Honorários de R$ 15.000,00 por mês. Faturamento mensal, vencimento a definir em contrato. Vigência mensal continuada, revisão inicial aos 90 dias e aviso prévio de 30 dias. Equipe, ferramentas, mídia, projetos específicos e viagens não estão inclusos.",
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": product_id,
                        "name": "Direção executiva da Hust, exercida por Darley Passarin. Honorários mensais.",
                        "product_uom_qty": 1,
                        "product_uom_id": 1,
                        "price_unit": 15000.0,
                        "tax_ids": [(6, 0, [])],
                    },
                )
            ],
        }
    ],
)
kw("sale.order", "write", [[order_id], {"state": "sent"}])
source_size = PDF.stat().st_size
attachment_id = kw(
    "ir.attachment",
    "create",
    [
        {
            "name": "Proposta Executiva HUST.pdf",
            "res_model": "sale.order",
            "res_id": order_id,
            "mimetype": "application/pdf",
            "raw": base64.b64encode(PDF.read_bytes()).decode(),
        }
    ],
)

company = kw(
    "res.partner",
    "read",
    [[company_id]],
    {"fields": ["name", "is_company", "vat", "website", "email", "customer_rank"]},
)
contact = kw(
    "res.partner",
    "read",
    [[contact_id]],
    {"fields": ["name", "function", "parent_id", "phone", "email", "customer_rank"]},
)
lead = kw(
    "crm.lead",
    "read",
    [[lead_id]],
    {"fields": ["name", "partner_id", "stage_id", "recurring_revenue", "date_open"]},
)
order = kw(
    "sale.order",
    "read",
    [[order_id]],
    {"fields": ["name", "state", "partner_id", "opportunity_id", "date_order", "amount_tax", "amount_total"]},
)
attachment = kw(
    "ir.attachment",
    "read",
    [[attachment_id]],
    {"fields": ["name", "res_id", "file_size"]},
)
print("COMPANY", json.dumps(company, ensure_ascii=False))
print("CONTACT", json.dumps(contact, ensure_ascii=False))
print("LEAD", json.dumps(lead, ensure_ascii=False))
print("ORDER", json.dumps(order, ensure_ascii=False))
print("FILE", json.dumps(attachment, ensure_ascii=False), "SOURCE", source_size)
