import sqlite3
import random
import json
import os
import requests
import time

DB_PATH = os.path.expanduser("~/Gerilla_RAG/Gerilla_RAG.db")
OLLAMA_URL = "http://localhost:11434/api/generate"
ALERTS_DIR = os.path.expanduser("~/Jules_mx/alerts")
SCANNED_DB = os.path.expanduser("~/Jules_mx/temp/scanned_files.db")

os.makedirs(ALERTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SCANNED_DB), exist_ok=True)

def init_scanned_db():
    conn = sqlite3.connect(SCANNED_DB)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scanned
                      (filepath TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

def is_scanned(filepath):
    conn = sqlite3.connect(SCANNED_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM scanned WHERE filepath=?", (filepath,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def mark_scanned(filepath):
    conn = sqlite3.connect(SCANNED_DB)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO scanned (filepath) VALUES (?)", (filepath,))
    conn.commit()
    conn.close()

def ask_qwen(prompt):
    payload = {
        "model": "qwen2.5:1.5b",
        "prompt": prompt,
        "stream": False
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        return resp.json().get("response", "")
    except Exception as e:
        return f"Error: {e}"

def scout_loop():
    print("🤖 Qwen Scout elindult... (Folyamatos háttérkutatás felgyorsítva és OKOSÍTVA!)")
    init_scanned_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Csak izgalmas kiterjesztések
    cursor.execute("SELECT filepath, content FROM rag_data WHERE filepath LIKE '%.py' OR filepath LIKE '%.sh' OR filepath LIKE '%.asm'")
    files = cursor.fetchall()

    # Kiszűrjük, amit már láttunk memóriában
    unscanned_files = [f for f in files if not is_scanned(f[0])]
    print(f"Összes fájl: {len(files)}, Ebből még nem vizsgált: {len(unscanned_files)}")

    while unscanned_files:
        filepath, content = random.choice(unscanned_files)
        unscanned_files.remove((filepath, content))

        # Rögtön be is jelöljük, hogy OOM esetén se kezdjük elölről
        mark_scanned(filepath)

        # OOM és token limit védelem
        if not content or len(content) < 50 or len(content) > 3000:
            continue

        print(f"🔍 Elemzem: {filepath} ...")
        prompt = f"""You are a cybersecurity, AI architecture and Python expert assistant.
Review the following code file named '{filepath}'.
Is this code useful for an AI agent infrastructure (e.g., automation, process management, API wrapping, code generation, testing automation, stealth operation)?
Answer with a short summary of what it does, and start your answer with 'YES:' if it is highly relevant and useful, or 'NO:' if it is just a standard/boring file.

CODE:
{content}
"""
        response = ask_qwen(prompt)

        if response.startswith("YES:"):
            print("🚨 ÉRDEKES LELET! Mentés a postaládába...")
            alert = {
                "timestamp": time.time(),
                "file": filepath,
                "qwen_analysis": response
            }
            safe_name = filepath.replace("/", "_").replace("\\\\", "_")
            with open(os.path.join(ALERTS_DIR, f"{safe_name}.json"), "w") as f:
                json.dump(alert, f)

    print("🏁 Minden fájlt átvizsgáltunk a célcsoportból!")

if __name__ == "__main__":
    scout_loop()