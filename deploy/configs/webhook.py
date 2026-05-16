from fastapi import FastAPI, Request
import subprocess
from pathlib import Path

app = FastAPI()

APP_DIR = Path("/home/lina/catty-reminders-app")
DEPLOYREF = Path("/home/lina/catty-reminders-app/deployref")  # исправлено на Path

def deploy(commit_hash: str):
    subprocess.run(["git", "-C", str(APP_DIR), "fetch", "--all"], check=False)
    subprocess.run(["git", "-C", str(APP_DIR), "reset", "--hard", commit_hash], check=True)
    DEPLOYREF.write_text(commit_hash, encoding="utf-8")
    subprocess.run(["sudo", "systemctl", "restart", "catty-reminders"], check=True)

@app.api_route("/", methods=["GET", "POST"])
async def handle_webhook(request: Request):
    if request.method == "GET":
        current_hash = DEPLOYREF.read_text(encoding="utf-8").strip() if DEPLOYREF.exists() else "unknown"
        return {"status": "alive", "deployref": current_hash}
        
    event = request.headers.get("X-GitHub-Event", "")
    if event != "push":
        return {"status": "ignored"}

    payload = await request.json()
    commit_hash = payload.get("after")
    if not commit_hash:
        return {"status": "bad payload"}

    deploy(commit_hash)
    return {"status": "accepted", "deployref": commit_hash}
