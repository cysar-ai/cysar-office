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
    with urllib.request.urlopen(request, timeout=180) as response:
        data = json.load(response)
    if "error" in data:
        error = data["error"]
        message = (error.get("data") or {}).get("message") or error.get("message")
        debug = (error.get("data") or {}).get("debug") or ""
        raise SystemExit(f"{message}\n{debug[-1800:]}")
    return data["result"]


uid = rpc("common", "authenticate", [env["ODOO_DB"], env["ODOO_USER"], env["ODOO_PASSWORD"], {}])


def kw(model, method, args, kwargs=None):
    return rpc(
        "object",
        "execute_kw",
        [env["ODOO_DB"], uid, env["ODOO_PASSWORD"], model, method, args, kwargs or {}],
    )


existing = kw(
    "contract.contract",
    "search_read",
    [[["partner_id", "=", 22]]],
    {"fields": ["name", "code"]},
)
if existing:
    raise SystemExit("ABORT contract already exists " + json.dumps(existing, ensure_ascii=False))

currency = kw("res.currency", "search", [[["name", "=", "BRL"]]], {"limit": 1})[0]
setup = kw(
    "product.template",
    "create",
    [
        {
            "name": "Implantação — Agente SDR Ciclo Júnior",
            "type": "service",
            "list_price": 1200.0,
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
monthly = kw(
    "product.template",
    "create",
    [
        {
            "name": "Mensalidade — Agente SDR Ciclo Júnior",
            "type": "service",
            "list_price": 600.0,
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
setup_product = kw("product.template", "read", [[setup]], {"fields": ["product_variant_id"]})[0][
    "product_variant_id"
][0]
monthly_product = kw("product.template", "read", [[monthly]], {"fields": ["product_variant_id"]})[0][
    "product_variant_id"
][0]


def line(name, product, price, start, end, sequence):
    values = {
        "name": name,
        "product_id": product,
        "quantity": 1,
        "automatic_price": False,
        "specific_price": price,
        "date_start": start,
        "recurring_interval": 1,
        "recurring_rule_type": "monthly",
        "recurring_invoicing_type": "pre-paid",
        "uom_id": 1,
        "sequence": sequence,
    }
    if end:
        values["date_end"] = end
    return (0, 0, values)


note = """Contrato Horizonte Piscinas e Cysar, assinado em Palmas em 17/09/2026.
Objeto: agente de IA SDR, Ciclo Júnior.
Vigência inicial de 12 meses, de 17/09/2026 a 16/09/2027, com renovação automática. Encerramento com aviso prévio de 30 dias.
Implantação de R$ 2.400,00 em duas parcelas de R$ 1.200,00, com vencimento em 17/09/2026 e 17/10/2026.
Mensalidade de R$ 600,00 a partir de 17/11/2026, com vencimento todo dia 17.
Reajuste anual pelo IPCA.
Contratante: Horizonte Piscinas Ltda, CNPJ 43.466.881/0001-43, representada por Diego Rodrigues Queirolo."""

contract_id = kw(
    "contract.contract",
    "create",
    [
        {
            "name": "Horizonte Piscinas — Agente SDR",
            "code": "HP-2026-09-17",
            "partner_id": 22,
            "invoice_partner_id": 22,
            "contract_type": "sale",
            "company_id": 1,
            "currency_id": currency,
            "journal_id": 1,
            "user_id": 2,
            "date": "2026-09-17",
            "date_start": "2026-09-17",
            "line_recurrence": True,
            "recurring_interval": 1,
            "recurring_rule_type": "monthly",
            "recurring_invoicing_type": "pre-paid",
            "generation_type": "invoice",
            "note": note,
            "contract_line_ids": [
                line(
                    "Implantação do agente SDR — Ciclo Júnior (parcela 1/2)",
                    setup_product,
                    1200.0,
                    "2026-09-17",
                    "2026-09-17",
                    10,
                ),
                line(
                    "Implantação do agente SDR — Ciclo Júnior (parcela 2/2)",
                    setup_product,
                    1200.0,
                    "2026-10-17",
                    "2026-10-17",
                    20,
                ),
                line(
                    "Mensalidade do agente SDR — Ciclo Júnior",
                    monthly_product,
                    600.0,
                    "2026-11-17",
                    None,
                    30,
                ),
            ],
        }
    ],
)
print("CONTRACT", contract_id)

lines = kw(
    "contract.line",
    "search_read",
    [[["contract_id", "=", contract_id]]],
    {
        "fields": [
            "name",
            "price_unit",
            "date_start",
            "date_end",
            "recurring_next_date",
        ]
    },
)
print("LINES", json.dumps(lines, ensure_ascii=False))

first_ids = kw("contract.contract", "recurring_create_invoice", [[contract_id]])
print("FIRST_INVOICE_IDS", first_ids)
if not first_ids:
    raise SystemExit("ABORT first invoice was not created")

kw("account.move", "action_post", [first_ids])
first = kw(
    "account.move",
    "read",
    [first_ids],
    {"fields": ["name", "invoice_date", "amount_total", "payment_state", "state", "partner_id"]},
)
print("FIRST_POSTED", json.dumps(first, ensure_ascii=False))

wizard_id = kw(
    "account.payment.register",
    "create",
    [{"payment_date": "2026-09-17", "journal_id": 6, "amount": first[0]["amount_total"]}],
    {"context": {"active_model": "account.move", "active_ids": first_ids}},
)
kw("account.payment.register", "action_create_payments", [[wizard_id]])
paid = kw(
    "account.move",
    "read",
    [first_ids],
    {"fields": ["name", "amount_total", "amount_residual", "payment_state", "state", "invoice_date"]},
)
print("FIRST_PAID", json.dumps(paid, ensure_ascii=False))

second_ids = kw("contract.contract", "recurring_create_invoice", [[contract_id]])
print("SECOND_INVOICE_IDS", second_ids)
if second_ids:
    kw("account.move", "action_post", [second_ids])
    second = kw(
        "account.move",
        "read",
        [second_ids],
        {"fields": ["name", "invoice_date", "amount_total", "amount_residual", "payment_state", "state"]},
    )
    print("SECOND_OPEN", json.dumps(second, ensure_ascii=False))

contract = kw(
    "contract.contract",
    "read",
    [[contract_id]],
    {"fields": ["name", "code", "recurring_next_date", "invoice_count"]},
)
print("CONTRACT_STATE", json.dumps(contract, ensure_ascii=False))
