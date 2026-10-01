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
    "/Users/dp/.cursor/projects/Users-dp-code-cysar-github-cysar-office/attachments/7e767eb0-2b5d-4f0e-ad04-f89c12b90b6a/Proposta_Executiva_IVM_OS.pdf"
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
    [[["vat", "ilike", "38069702"]]],
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
            "name": "IVM Engenharia Ltda",
            "customer_rank": 1,
            "vat": "38069702000102",
            "website": "https://ivmtech.com.br/",
            "street": "Orla 14, Al 12, QI 23, Lt 06",
            "city": "Palmas",
            "zip": "77023-615",
            "state_id": state_id,
            "country_id": 31,
            "lang": "pt_BR",
            "comment": "Nome fantasia: IVM TECH. Instagram: https://www.instagram.com/ivm.tech/",
        }
    ],
)
kw("res.partner", "write", [[company_id], {"is_company": True}])
contact_id = kw(
    "res.partner",
    "create",
    [
        {
            "name": "Marcelo Sábia",
            "parent_id": company_id,
            "email": "marcelo@ivmtech.com.br",
            "phone": "+55 63 98429-5541",
            "customer_rank": 0,
            "lang": "pt_BR",
        }
    ],
)

description = """<p>Proposta executiva enviada em 18/08/2026 para o Marcelo Sábia, IVM TECH.</p>
<ul>
<li>Escopo: requisitos do software IVM OS. Entender, organizar e priorizar o que o sistema precisa fazer.</li>
<li>Investimento: R$ 15.000,00 em 3 parcelas mensais de R$ 5.000,00.</li>
<li>Prazo: 3 meses, com uma entrega por mês.</li>
<li>Esta etapa não inclui a programação. O desenvolvimento será orçado depois da aprovação dos requisitos.</li>
</ul>"""
lead_id = kw(
    "crm.lead",
    "create",
    [
        {
            "name": "Requisitos do IVM OS",
            "type": "opportunity",
            "partner_id": contact_id,
            "stage_id": 3,
            "user_id": 2,
            "team_id": 1,
            "phone": "+55 63 98429-5541",
            "email_from": "marcelo@ivmtech.com.br",
            "website": "https://ivmtech.com.br/",
            "expected_revenue": 15000.0,
            "description": description,
            "date_open": "2026-08-18 15:00:00",
        }
    ],
)
kw("res.partner", "write", [[company_id], {"email": False}])

found = kw("product.product", "search", [[["name", "=", "Requisitos do IVM OS"]]], {"limit": 1})
if found:
    product_id = found[0]
else:
    template = kw(
        "product.template",
        "create",
        [
            {
                "name": "Requisitos do IVM OS",
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
            "date_order": "2026-08-18 15:00:00",
            "note": "Proposta enviada em 18/08/2026. Total de R$ 15.000,00 em 3 parcelas mensais de R$ 5.000,00. Esta etapa não inclui a programação do sistema.",
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": product_id,
                        "name": "Requisitos do software IVM OS. Entendimento do negócio, definição de módulos, fluxos, regras e prioridades, e entrega do documento de requisitos em 3 meses.",
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
            "name": "Proposta Executiva IVM OS.pdf",
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
    {"fields": ["name", "is_company", "vat", "email", "customer_rank", "city", "zip"]},
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
    {"fields": ["name", "partner_id", "stage_id", "expected_revenue", "date_open"]},
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
    {"fields": ["name", "res_id", "file_size", "mimetype"]},
)
print("COMPANY", json.dumps(company, ensure_ascii=False))
print("CONTACT", json.dumps(contact, ensure_ascii=False))
print("LEAD", json.dumps(lead, ensure_ascii=False))
print("ORDER", json.dumps(order, ensure_ascii=False))
print("FILE", json.dumps(attachment, ensure_ascii=False), "SOURCE", source_size)
