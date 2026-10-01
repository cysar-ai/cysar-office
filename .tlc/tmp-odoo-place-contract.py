import json
import time
import urllib.request
from pathlib import Path

ROOT = Path("/tmp/oca-contract/contract-19.0/contract")
config = json.loads(Path("/Users/dp/code/cysar/github/cysar-office/.cursor/mcp.json").read_text())
url = config["mcpServers"]["easypanel"]["url"]


def post(payload):
    data = json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        raw = response.read().decode()
    if not raw.strip():
        return {}
    body = json.loads(raw)
    if "error" in body:
        raise SystemExit(json.dumps(body["error"])[:2000])
    return body


def tool(name, arguments):
    body = post(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )
    text = body["result"]["content"][0]["text"]
    parsed = json.loads(text)
    if parsed.get("error"):
        raise SystemExit(str(parsed["error"])[:2000])
    return parsed


post(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "cysar-office", "version": "1.0"},
        },
    }
)
post({"jsonrpc": "2.0", "method": "notifications/initialized"})

inspected = tool(
    "execute_query",
    {
        "procedure": "inspectAppService",
        "input": {"projectName": "cysar", "serviceName": "odoo"},
    },
)["result"]
original = inspected["deploy"]["command"]

files = {
    "security/ir.access.csv": (ROOT / "security/ir.access.csv").read_text(),
    "security/contract_tag.xml": (ROOT / "security/contract_tag.xml").read_text(),
    "security/contract_security.xml": (ROOT / "security/contract_security.xml").read_text(),
}
payload = json.dumps(files)
bootstrap = r"""
import io, json, pathlib, shutil, tarfile, urllib.request
files = json.loads(%s)
root = pathlib.Path("/mnt/extra-addons/contract")
data = urllib.request.urlopen("https://codeload.github.com/OCA/contract/tar.gz/refs/heads/19.0", timeout=120).read()
with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
    archive.extractall("/tmp/oca-contract-src")
src = pathlib.Path("/tmp/oca-contract-src/contract-19.0/contract")
if root.exists():
    shutil.rmtree(root)
shutil.move(str(src), str(root))
for name, content in files.items():
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
old_csv = root / "security/ir.model.access.csv"
if old_csv.exists():
    old_csv.unlink()
manifest = root / "__manifest__.py"
text = manifest.read_text()
text = text.replace("security/ir.model.access.csv", "security/ir.access.csv")
text = text.replace('"version": "19.0.1.0.6"', '"version": "20.0.1.0.6"')
manifest.write_text(text)
print("contract-files-ready")
""" % json.dumps(payload)
command = "sh -c " + json.dumps("python3 -c " + json.dumps(bootstrap) + "\nexec " + original)
print("COMMAND_CHARS", len(command))

tool(
    "execute_destructive",
    {
        "procedure": "updateAppDeploy",
        "input": {
            "projectName": "cysar",
            "serviceName": "odoo",
            "deploy": {"command": command, "replicas": 1, "zeroDowntime": True},
        },
    },
)
print("DEPLOY_SETTINGS_UPDATED")
tool(
    "execute_destructive",
    {
        "procedure": "deployAppService",
        "input": {"projectName": "cysar", "serviceName": "odoo"},
    },
)
print("DEPLOY_STARTED")

deadline = time.time() + 180
ready = False
while time.time() < deadline:
    try:
        request = urllib.request.Request("https://crm-office.cysar.ai/web/login")
        with urllib.request.urlopen(request, timeout=15) as response:
            if response.status == 200:
                ready = True
                break
    except Exception as error:
        print("WAIT", type(error).__name__)
    time.sleep(5)
print("LOGIN", ready)
path = Path("/tmp/odoo-original-command.txt")
path.write_text(original)
print("ORIGINAL_SAVED", path.exists())
