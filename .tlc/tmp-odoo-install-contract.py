import base64
import io
import json
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path("/tmp/oca-contract/contract-19.0/contract")
OFFICE = Path("/Users/dp/code/cysar/github/cysar-office")
COMMAND_FILE = Path("/tmp/odoo-original-command.txt")
PANEL = json.loads((OFFICE / ".cursor/mcp.json").read_text())["mcpServers"]["easypanel"]["url"]
ODOO = "https://crm-office.cysar.ai/jsonrpc"


def env():
    values = {}
    for line in (OFFICE / ".env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def panel(payload):
    data = json.dumps(payload).encode()
    request = urllib.request.Request(
        PANEL,
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
        raise SystemExit(json.dumps(body["error"])[:1500])
    return body


def panel_tool(name, arguments):
    body = panel(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )
    parsed = json.loads(body["result"]["content"][0]["text"])
    if parsed.get("error"):
        raise SystemExit(str(parsed["error"])[:1500])
    return parsed


def odoo_rpc(service, method, args):
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"service": service, "method": method, "args": args},
            "id": 1,
        }
    ).encode()
    request = urllib.request.Request(ODOO, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        data = json.load(response)
    if "error" in data:
        error = data["error"]
        message = error.get("data", {}).get("message") or error.get("message")
        debug = (error.get("data", {}) or {}).get("debug") or ""
        raise RuntimeError(f"{message}\n{debug[-2000:]}")
    return data["result"]


def login_up():
    try:
        with urllib.request.urlopen("https://crm-office.cysar.ai/web/login", timeout=10) as response:
            return response.status == 200
    except Exception:
        return False


def build_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if relative.parts[0] == "i18n" and path.name != "pt_BR.po":
                continue
            archive.write(path, Path("contract") / relative)
    return buffer.getvalue()


def save_original_command():
    panel(
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
    panel({"jsonrpc": "2.0", "method": "notifications/initialized"})
    inspected = panel_tool(
        "execute_query",
        {
            "procedure": "inspectAppService",
            "input": {"projectName": "cysar", "serviceName": "odoo"},
        },
    )["result"]
    command = inspected["deploy"]["command"]
    if not command.startswith("odoo "):
        raise SystemExit("ABORT unexpected command prefix")
    COMMAND_FILE.write_text(command)
    COMMAND_FILE.chmod(0o600)
    return command


def deploy(command):
    panel_tool(
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
    panel_tool(
        "execute_destructive",
        {
            "procedure": "deployAppService",
            "input": {"projectName": "cysar", "serviceName": "odoo"},
        },
    )


def restore_original():
    if not COMMAND_FILE.exists():
        print("RESTORE_SKIPPED")
        return
    deploy(COMMAND_FILE.read_text())
    COMMAND_FILE.unlink()
    print("COMMAND_RESTORED")


def main():
    values = env()
    payload = build_zip()
    print("ZIP_BYTES", len(payload))
    uid = odoo_rpc(
        "common",
        "authenticate",
        [values["ODOO_DB"], values["ODOO_USER"], values["ODOO_PASSWORD"], {}],
    )

    def kw(model, method, args, kwargs=None):
        return odoo_rpc(
            "object",
            "execute_kw",
            [values["ODOO_DB"], uid, values["ODOO_PASSWORD"], model, method, args, kwargs or {}],
        )

    encoded = base64.b64encode(payload).decode()
    zip_id = kw(
        "ir.attachment",
        "create",
        [
            {
                "name": "oca-contract-module.zip",
                "raw": encoded,
                "mimetype": "application/zip",
            }
        ],
    )
    log_id = kw(
        "ir.attachment",
        "create",
        [{"name": "oca-contract-bootstrap.txt", "raw": base64.b64encode(b"pending").decode(), "mimetype": "text/plain"}],
    )
    rows = kw(
        "ir.attachment",
        "read",
        [[zip_id, log_id]],
        {"fields": ["id", "store_fname", "file_size"]},
    )
    by_id = {row["id"]: row for row in rows}
    zip_store = by_id[zip_id]["store_fname"]
    log_store = by_id[log_id]["store_fname"]
    print("STORED", bool(zip_store), bool(log_store), by_id[zip_id]["file_size"])
    if not zip_store or not log_store:
        raise SystemExit("ABORT attachment not in filestore")

    original = save_original_command()
    zip_hash = zip_store.split("/")[-1]
    script = """
import base64, os, pathlib, shutil, traceback, zipfile
ORIG = base64.b64decode(%r).decode().replace("$(PROJECT_NAME)", "cysar")
ZIP_HASH = %r
LOG_ID = %d

def flag(name):
    key = "--" + name + "="
    start = ORIG.find(key)
    if start < 0:
        return ""
    start += len(key)
    end = ORIG.find(" ", start)
    return ORIG[start:] if end < 0 else ORIG[start:end]

def remember(text):
    try:
        import psycopg2
        conn = psycopg2.connect(host=flag("db_host"), port=flag("db_port") or "5432", dbname="odoo", user=flag("db_user"), password=flag("db_password"))
        cur = conn.cursor()
        cur.execute("update ir_attachment set description=%%s where id=%%s", (text[:2000], LOG_ID))
        conn.commit()
        conn.close()
    except Exception:
        pass

remember("start")
result = "start"
try:
    found = None
    for base in (pathlib.Path("/var/lib/odoo"), pathlib.Path("/home/odoo/.local/share/Odoo"), pathlib.Path("/mnt/extra-addons")):
        if not base.exists():
            continue
        matches = list(base.rglob(ZIP_HASH))
        if matches:
            found = matches[0]
            break
    if found is None:
        result = "zip-not-found"
    else:
        root = pathlib.Path("/mnt/extra-addons/contract")
        if root.exists():
            shutil.rmtree(root)
        with zipfile.ZipFile(found) as archive:
            archive.extractall("/mnt/extra-addons")
        result = "ready" if (root / "__manifest__.py").is_file() else "missing-manifest " + str(found)
except Exception:
    result = traceback.format_exc()[-1500:]
remember(result)
os.execvp("sh", ["sh", "-c", ORIG])
""" % (base64.b64encode(original.encode()).decode(), zip_hash, log_id)
    packed = base64.b64encode(script.encode()).decode()
    argument = "exec(__import__('base64').b64decode('%s').decode())" % packed
    if "'" in packed or " " in argument:
        raise SystemExit("ABORT command argument is not shell-safe")
    command = 'python3 -c "%s"' % argument
    print("COMMAND_CHARS", len(command))
    try:
        deploy(command)
        print("BOOTSTRAP_DEPLOYED")
        message = "pending"
        down = 0
        for _ in range(15):
            time.sleep(3)
            if not login_up():
                down += 1
                print("LOGIN_DOWN", down)
                continue
            down = 0
            try:
                message = kw("ir.attachment", "read", [[log_id]], {"fields": ["description"]})[0]["description"] or ""
            except Exception as error:
                print("READ_FAIL", type(error).__name__)
                continue
            print("LOG", message.splitlines()[0][:160] if message else "empty")
            if message and not message.startswith("pending"):
                break
        print("POLL_DONE", message[:200])
    finally:
        restore_original()
        for _ in range(20):
            if login_up():
                print("LOGIN_OK")
                break
            time.sleep(3)
        else:
            print("LOGIN_STILL_DOWN")
            return
    message = kw("ir.attachment", "read", [[log_id]], {"fields": ["description"]})[0]["description"] or ""
    print("FINAL_LOG", message[:500])
    if not message.startswith("ready"):
        print("BOOTSTRAP_FAILED")
        return
    kw("ir.module.module", "update_list", [])
    found = kw(
        "ir.module.module",
        "search_read",
        [[["name", "=", "contract"]]],
        {"fields": ["id", "state", "latest_version"]},
    )
    print("FOUND", json.dumps(found))
    if not found:
        print("MODULE_NOT_ON_PATH")
        return
    if found[0]["state"] != "installed":
        kw("ir.module.module", "button_immediate_install", [[found[0]["id"]]])
    final = kw(
        "ir.module.module",
        "search_read",
        [[["name", "=", "contract"]]],
        {"fields": ["state", "latest_version", "shortdesc"]},
    )
    print("INSTALLED", json.dumps(final, ensure_ascii=False))


if __name__ == "__main__":
    main()
