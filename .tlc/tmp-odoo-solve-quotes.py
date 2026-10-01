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

PDF_DIR = Path(
    "/Users/dp/.cursor/projects/Users-dp-code-cysar-github-cysar-office/attachments/7e767eb0-2b5d-4f0e-ad04-f89c12b90b6a"
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


existing = kw(
    "sale.order",
    "search_read",
    [[["partner_id", "child_of", 24]]],
    {"fields": ["name", "state", "amount_total"]},
)
if existing:
    raise SystemExit("ABORT quotes exist " + json.dumps(existing, ensure_ascii=False))

line_meta = kw(
    "sale.order.line",
    "fields_get",
    [["tax_id", "tax_ids", "product_uom", "product_uom_id"]],
    {"attributes": ["type"]},
)
tax_field = "tax_ids" if "tax_ids" in line_meta else "tax_id" if "tax_id" in line_meta else None
uom_field = "product_uom_id" if "product_uom_id" in line_meta else "product_uom" if "product_uom" in line_meta else None
if not tax_field or not uom_field:
    raise SystemExit("ABORT line fields " + json.dumps(list(line_meta)))


def product_variant(name, price):
    found = kw("product.product", "search", [[["name", "=", name]]], {"limit": 1})
    if found:
        return found[0]
    template = kw(
        "product.template",
        "create",
        [
            {
                "name": name,
                "type": "service",
                "list_price": price,
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
    return kw("product.template", "read", [[template]], {"fields": ["product_variant_id"]})[0][
        "product_variant_id"
    ][0]


agenda_product = product_variant("Agenda MVP", 3000.0)
projeto_product = product_variant("Projeto MVP", 16000.0)

quotes = [
    {
        "product": agenda_product,
        "price": 3000.0,
        "line": "Agenda MVP — ciclo de mentoria técnica. 10 encontros de 60 minutos em 5 semanas. A equipe da Solve constrói e a Cysar conduz. Assinaturas de ferramentas não inclusas.",
        "note": "Condição apresentada em 28/09/2026: R$ 3.000,00 por ciclo, ou 2x de R$ 1.500,00 (entrada + 30 dias). O ciclo pode ser contratado novamente se o projeto pedir mais.",
        "pdf": PDF_DIR / "Cysar_-_Agenda_MVP.pdf",
        "filename": "Cysar - Agenda MVP.pdf",
    },
    {
        "product": projeto_product,
        "price": 16000.0,
        "line": "Projeto MVP — capacidade mínima de 160 horas, em 6 a 8 semanas. A Cysar constrói, da análise de requisitos ao piloto. Estimativa inicial; o valor final é confirmado ao fim da análise, antes da construção.",
        "note": "Condição apresentada em 28/09/2026: a partir de R$ 16.000,00, ou 2x de R$ 8.000,00 (entrada + 30 dias). Suporte e evolução após o piloto ficam fora do escopo.",
        "pdf": PDF_DIR / "Cysar_-_Projeto_MVP.pdf",
        "filename": "Cysar - Projeto MVP.pdf",
    },
]

created = []
for quote in quotes:
    order_id = kw(
        "sale.order",
        "create",
        [
            {
                "partner_id": 24,
                "opportunity_id": 2,
                "user_id": 2,
                "team_id": 1,
                "company_id": 1,
                "date_order": "2026-09-28 15:00:00",
                "note": quote["note"],
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": quote["product"],
                            "name": quote["line"],
                            "product_uom_qty": 1,
                            uom_field: 1,
                            "price_unit": quote["price"],
                            tax_field: [(6, 0, [])],
                        },
                    )
                ],
            }
        ],
    )
    kw("sale.order", "write", [[order_id], {"state": "sent"}])
    payload = base64.b64encode(quote["pdf"].read_bytes()).decode()
    attachment_id = kw(
        "ir.attachment",
        "create",
        [
            {
                "name": quote["filename"],
                "res_model": "sale.order",
                "res_id": order_id,
                "mimetype": "application/pdf",
                "raw": payload,
            }
        ],
    )
    created.append((order_id, attachment_id, quote["pdf"].stat().st_size))

orders = kw(
    "sale.order",
    "read",
    [[item[0] for item in created]],
    {
        "fields": [
            "name",
            "state",
            "partner_id",
            "opportunity_id",
            "date_order",
            "amount_untaxed",
            "amount_tax",
            "amount_total",
        ]
    },
)
attachments = kw(
    "ir.attachment",
    "read",
    [[item[1] for item in created]],
    {"fields": ["name", "res_id", "file_size", "mimetype", "store_fname"]},
)
print("ORDERS", json.dumps(orders, ensure_ascii=False))
print("FILES", json.dumps(attachments, ensure_ascii=False))
print("SOURCE_SIZES", [item[2] for item in created])
