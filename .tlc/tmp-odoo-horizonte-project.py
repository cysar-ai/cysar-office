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
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.load(response)
    if "error" in data:
        error = data["error"]
        message = (error.get("data") or {}).get("message") or error.get("message")
        debug = (error.get("data") or {}).get("debug") or ""
        raise SystemExit(f"{message}\n{debug[-1600:]}")
    return data["result"]


uid = rpc("common", "authenticate", [env["ODOO_DB"], env["ODOO_USER"], env["ODOO_PASSWORD"], {}])


def kw(model, method, args, kwargs=None):
    return rpc(
        "object",
        "execute_kw",
        [env["ODOO_DB"], uid, env["ODOO_PASSWORD"], model, method, args, kwargs or {}],
    )


existing = kw(
    "project.project",
    "search_read",
    [[["partner_id", "=", 22]]],
    {"fields": ["name"]},
)
if existing:
    raise SystemExit("ABORT project already exists " + json.dumps(existing, ensure_ascii=False))

description = """<p>Projeto do contrato HP-2026-09-17, assinado em 17/09/2026.</p>
<p>Objeto: agente de IA SDR, Ciclo Júnior, para a Horizonte Piscinas Ltda.</p>
<ul>
<li>Implantação de R$ 2.400,00, em duas parcelas de R$ 1.200,00 (17/09/2026 e 17/10/2026).</li>
<li>Recorrência, manutenção e sustentação de R$ 600,00 por mês, a partir de 17/11/2026, com vencimento todo dia 17.</li>
<li>Vigência inicial de 12 meses, até 16/09/2027, com renovação automática e aviso prévio de 30 dias.</li>
<li>Reajuste anual pelo IPCA.</li>
</ul>"""

project_id = kw(
    "project.project",
    "create",
    [
        {
            "name": "Horizonte Piscinas — Agente SDR",
            "partner_id": 22,
            "user_id": 2,
            "company_id": 1,
            "date_start": "2026-09-17",
            "allow_milestones": True,
            "allow_recurring_tasks": True,
            "allow_billable": True,
            "privacy_visibility": "employees",
            "last_update_status": "on_track",
            "lead_id": 1,
            "label_tasks": "Tarefas",
            "description": description,
        }
    ],
)

stages = []
for name, sequence, fold in (
    ("A fazer", 1, False),
    ("Em andamento", 2, False),
    ("Concluído", 3, True),
    ("Cancelado", 4, True),
):
    stages.append(
        kw(
            "project.task.type",
            "create",
            [{"name": name, "sequence": sequence, "fold": fold, "project_ids": [(4, project_id)]}],
        )
    )
todo, doing, done, cancelled = stages

setup_milestone = kw(
    "project.milestone",
    "create",
    [
        {
            "name": "Implantação",
            "project_id": project_id,
            "deadline": "2026-10-17",
            "sequence": 10,
        }
    ],
)
sustain_milestone = kw(
    "project.milestone",
    "create",
    [
        {
            "name": "Início da sustentação",
            "project_id": project_id,
            "deadline": "2026-11-17",
            "sequence": 20,
        }
    ],
)

setup_task = kw(
    "project.task",
    "create",
    [
        {
            "name": "Implantação do agente SDR — Ciclo Júnior",
            "project_id": project_id,
            "partner_id": 22,
            "user_ids": [(6, 0, [2])],
            "stage_id": doing,
            "milestone_id": setup_milestone,
            "date_deadline": "2026-10-17",
            "company_id": 1,
            "description": "<p>Implantar o agente de IA SDR, Ciclo Júnior. Prazo alinhado ao fim da implantação contratual, em 17/10/2026. Contrato HP-2026-09-17.</p>",
        }
    ],
)
sustain_task = kw(
    "project.task",
    "create",
    [
        {
            "name": "Recorrência, manutenção e sustentação",
            "project_id": project_id,
            "partner_id": 22,
            "user_ids": [(6, 0, [2])],
            "stage_id": todo,
            "milestone_id": sustain_milestone,
            "date_deadline": "2026-11-17",
            "recurring_task": True,
            "repeat_interval": 1,
            "repeat_unit": "month",
            "repeat_type": "forever",
            "company_id": 1,
            "description": "<p>Operar a recorrência mensal de manutenção e sustentação do agente, a partir de 17/11/2026, no valor de R$ 600,00 com vencimento todo dia 17. Renovação automática e reajuste anual pelo IPCA. Contrato HP-2026-09-17.</p>",
        }
    ],
)

project = kw(
    "project.project",
    "read",
    [[project_id]],
    {"fields": ["name", "partner_id", "date_start", "task_count", "milestone_count"]},
)
print("PROJECT", json.dumps(project, ensure_ascii=False))
print("STAGES", stages)
print("TASKS", setup_task, sustain_task)
