import sqlite3
import random
import json
import os
import requests
import time

# Dinamikus RAG váltó
DB_PATHS = [
    os.path.expanduser("~/Gerilla_RAG/Gerilla_RAG.db"),
    os.path.expanduser("~/Rag_epites, chatbot_csv_data_llm_RAG/RAG_CHATBOT_CSV_DATA_LLM_github.db"),
    os.path.expanduser("~/MX_LINUX_RAG/mx_linux_knowledge.db")
]

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
    print("🤖 Qwen Scout elindult... (Multi-RAG Dinamikus Váltással!)")
    init_scanned_db()

    while True:
        # Végigmegyünk az adatbázisokon
        all_dbs_done = True

        for db_path in DB_PATHS:
            if not os.path.exists(db_path):
                print(f"⚠️ Nem található adatbázis: {db_path}")
                continue

            print(f"\n📂 RAG Adatbázis elemzése: {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT filepath, content FROM rag_data WHERE filepath LIKE '%.py' OR filepath LIKE '%.sh' OR filepath LIKE '%.asm'")
                files = cursor.fetchall()
            except sqlite3.Error:
                print(f"❌ Sémahiba a(z) {db_path} adatbázisban.")
                conn.close()
                continue

            conn.close()

            unscanned_files = [f for f in files if not is_scanned(f[0])]

            if not unscanned_files:
                print(f"✅ Adatbázis feldolgozva: {db_path}")
                continue

            all_dbs_done = False
            print(f"Összes fájl: {len(files)}, Ebből még nem vizsgált: {len(unscanned_files)}")

            # Csináljunk meg egy adatbázisból 500 fájlt, majd lépjünk a következőre, hogy ne ragadjunk le egy helyen (Round Robin)
            batch_count = 0
            while unscanned_files and batch_count < 500:
                filepath, content = random.choice(unscanned_files)
                unscanned_files.remove((filepath, content))
                batch_count += 1

                mark_scanned(filepath)

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
                    safe_name = filepath.replace("/", "_").replace("\\", "_")
                    with open(os.path.join(ALERTS_DIR, f"{safe_name}.json"), "w") as f:
                        json.dump(alert, f)

        if all_dbs_done:
            print("🏁 Minden adatbázis minden kódját feldolgoztam! Várakozás új RAG frissítésre...")
            time.sleep(3600) # 1 órát alszik, hátha jön új fájl

if __name__ == "__main__":
    scout_loop()