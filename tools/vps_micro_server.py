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
    """
    # Javított útvonal a három RAG adatbázishoz:
    if "Gerilla_RAG" in db_name:
        db_path = os.path.expanduser("~/Gerilla_RAG/Gerilla_RAG.db")
    elif "mx_linux" in db_name:
        db_path = os.path.expanduser("~/MX_LINUX_RAG/mx_linux_knowledge.db")
    elif "CHATBOT" in db_name or "Rag_epites" in db_name:
        db_path = os.path.expanduser("~/Rag_epites, chatbot_csv_data_llm_RAG/RAG_CHATBOT_CSV_DATA_LLM_github.db")
    else:
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


@app.post("/summarize_memory")
def summarize_memory(limit_lines: int = 10):
    """VPS oldali titkár funkció. Beolvassa a backup.jsonl-t és Qwen-nel összefoglalja."""
    import requests
    OLLAMA_URL = "http://localhost:11434/api/generate"
    MEMORY_PATH = os.path.expanduser("~/Jules_mx/memory_offload/backup.jsonl")

    if not os.path.exists(MEMORY_PATH):
        return {"error": "Nincs szinkronizált memória a VPS-en (backup.jsonl hiányzik)."}

    try:
        with open(MEMORY_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-limit_lines:]

        memory_text = "".join(lines)
        if len(memory_text) > 2000:
            memory_text = memory_text[-2000:]

        prompt = "Foglald össze az alábbi eseménynaplót 3 rövid, tömör pontban magyarul a Fő Agent számára:\n\n" + memory_text

        payload = {
            "model": "qwen2.5:1.5b",
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 150}
        }

        resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
        return {"summary": resp.json().get("response", "Üres válasz.")}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health_check():
    return {"status": "Alive", "system": "VPS Second Brain"}

if __name__ == "__main__":
    import uvicorn
    # A 8000-es porton fut, de biztonsági okokból érdemes csak localhoston (127.0.0.1) hallgatni,
    # és SSH port forwarddal elérni, de egyelőre kinyitjuk a teszthez.
    uvicorn.run(app, host="127.0.0.1", port=8000)
