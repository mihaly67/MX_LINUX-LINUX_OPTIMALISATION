from fastapi import FastAPI, BackgroundTasks, Request
from pydantic import BaseModel
import subprocess
import os
import sqlite3
import json

app = FastAPI(title="Jules MX - VPS Micro Brain")

class CommandRequest(BaseModel):
    command: str

def execute_bash(command: str):
    """Háttérben lefutó bash parancs (pl. RAG kicsomagolás, hosszas scraping)."""
    try:
        # A Jules_mx mappában futtatjuk a parancsokat
        work_dir = os.path.expanduser("~/Jules_mx")
        os.makedirs(work_dir, exist_ok=True)

        result = subprocess.run(
            command, shell=True, cwd=work_dir,
            capture_output=True, text=True, timeout=3600 # 1 óra max
        )

        # Eredmény kimentése a VPS SSD-re (Mivel aszinkron, a hívó nem várja meg az eredményt!)
        log_file = os.path.join(work_dir, "temp", "last_task.log")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"COMMAND: {command}\n")
            f.write(f"STDOUT:\n{result.stdout}\n")
            f.write(f"STDERR:\n{result.stderr}\n")

    except Exception as e:
        log_file = os.path.join(os.path.expanduser("~/Jules_mx/temp"), "error.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"Hiba a {command} futtatása közben: {str(e)}\n")

@app.post("/execute_async")
async def execute_async(req: CommandRequest, background_tasks: BackgroundTasks):
    """Azonnal visszaad egy 200 OK-t (nincs timeout!), de a VPS háttérben dolgozik."""
    background_tasks.add_task(execute_bash, req.command)
    return {"status": "Task started in background", "command": req.command}

@app.post("/rag_search")
async def rag_search_sqlite(query: str, db_name: str, limit: int = 5):
    """
    OOM Safe (8GB RAM barát) RAG Kereső.
    Nem tölti be a 3GB-os FAISS indexet a RAM-ba!
    Helyette SQLite Full Text Search (vagy LIKE) lekérdezést csinál egyenesen a 300GB-os SSD-ről.
    """
    db_path = os.path.expanduser(f"~/Jules_mx/RAG_DB/{db_name}")
    if not os.path.exists(db_path):
        return {"error": f"Adatbázis nem található a VPS-en: {db_path}"}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # OOM-Safe lekérdezés: csak a content LIKE-ra szűrünk, limitálva
        cursor.execute("""
            SELECT source_repo, filepath, substr(content, 1, 500) as snippet
            FROM rag_data
            WHERE content LIKE ? LIMIT ?
        """, (f"%{query}%", limit))

        results = [{"repo": r[0], "file": r[1], "snippet": r[2]} for r in cursor.fetchall()]
        conn.close()
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health_check():
    return {"status": "Alive", "system": "VPS Second Brain"}

if __name__ == "__main__":
    import uvicorn
    # A 8000-es porton fut, de biztonsági okokból érdemes csak localhoston (127.0.0.1) hallgatni,
    # és SSH port forwarddal elérni, de egyelőre kinyitjuk a teszthez.
    uvicorn.run(app, host="0.0.0.0", port=8000)
