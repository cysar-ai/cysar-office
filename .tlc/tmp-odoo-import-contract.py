import base64
import io
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

SRC = Path("/tmp/oca-contract/contract-19.0/contract")
STAGE = Path("/tmp/oca-contract/stage/contract")
if STAGE.exists():
    shutil.rmtree(STAGE)
shutil.copytree(SRC, STAGE)
manifest = STAGE / "__manifest__.py"
text = manifest.read_text()
text = text.replace('"version": "19.0.1.0.6"', '"version": "20.0.1.0.6"')
manifest.write_text(text)

buffer = io.BytesIO()
with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in STAGE.rglob("*"):
        if path.is_file():
            archive.write(path, Path("contract") / path.relative_to(STAGE))
payload = base64.b64encode(buffer.getvalue()).decode()

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
    with urllib.request.urlopen(request, timeout=300) as response:
        data = json.load(response)
    if "error" in data:
        error = data["error"]
        message = error.get("data", {}).get("message") or error.get("message")
        debug = error.get("data", {}).get("debug") or ""
        raise SystemExit(f"{message}\n{debug[-2500:]}")
    return data["result"]


uid = rpc("common", "authenticate", [env["ODOO_DB"], env["ODOO_USER"], env["ODOO_PASSWORD"], {}])


def kw(model, method, args, kwargs=None):
    return rpc(
        "object",
        "execute_kw",
        [env["ODOO_DB"], uid, env["ODOO_PASSWORD"], model, method, args, kwargs or {}],
    )


wizard_id = kw("base.import.module", "create", [{"module_file": payload}])
print("WIZARD", wizard_id)
result = kw("base.import.module", "import_module", [[wizard_id]])
print("IMPORT", json.dumps(result, ensure_ascii=False, default=str)[:2000])
rows = kw(
    "ir.module.module",
    "search_read",
    [[["name", "=", "contract"]]],
    {"fields": ["name", "state", "shortdesc", "latest_version"]},
)
print("MODULE", json.dumps(rows, ensure_ascii=False))
