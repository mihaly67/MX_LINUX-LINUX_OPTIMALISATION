import sqlite3
import random
import json
import os
import requests
import time

# Dinamikus RAG váltó - mind a 3 RAG DB elérési útja és rövid neve a csoportosításhoz
DB_PATHS = {
    "BRAIN2_MCP_Focus": {
        "path": os.path.expanduser("/home/misi/BRAIN2_DEV_RAG/brain2_dev_knowledge.db"),
        "prompt_goal": "KERESS MINDENT AMI MCP (Model Context Protocol) KAPCSOLATOS! Keresd az MCP szervereket, klienseket, stdio/websocket kommunikációt, eszközök (tools) és erőforrások (resources) kiajánlását. Bármi, ami MCP-vel kapcsolatos agent-to-agent vagy agent-to-tool kommunikáció."
    }
}

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
BASE_ALERTS_DIR = os.path.expanduser("~/Jules_mx/alerts")
SCANNED_DB = os.path.expanduser("~/Jules_mx/temp/scanned_files.db")

os.makedirs(BASE_ALERTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SCANNED_DB), exist_ok=True)

# Létrehozzuk a RAG-onkénti alkönyvtárakat az alert mappában
for rag_name in DB_PATHS.keys():
    os.makedirs(os.path.join(BASE_ALERTS_DIR, rag_name), exist_ok=True)

def init_scanned_db():
    conn = sqlite3.connect(SCANNED_DB)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scanned (filepath TEXT PRIMARY KEY)''')
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

def ask_llama3(prompt):
    payload = {
        "model": "qwen2.5:1.5b",
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 150, "temperature": 0.1}
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
        return resp.json().get("response", "")
    except Exception as e:
        return f"Error: {e}"

def scout_loop():
    print("🤖 Llama3/Qwen Scout elindult... (Multi-RAG Dinamikus Váltással, PADLÓGÁZON)")
    init_scanned_db()

    while True:
        all_dbs_done = True

        for rag_name, config in DB_PATHS.items():
            db_path = config["path"]
            prompt_goal = config["prompt_goal"]
            rag_alert_dir = os.path.join(BASE_ALERTS_DIR, rag_name)
            os.makedirs(rag_alert_dir, exist_ok=True) # Ensure it exists during runtime

            if not os.path.exists(db_path):
                print(f"⚠️ Nem található adatbázis: {db_path}")
                continue

            print(f"\n📂 RAG Adatbázis elemzése: {db_path} (Csoport: {rag_name})")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                # Szigorúan csak kód fájlok (no bloat) - TypeScript/React gyakori MCP rendszereknél
                cursor.execute("SELECT filepath, content FROM rag_data WHERE filepath LIKE '%.py' OR filepath LIKE '%.js' OR filepath LIKE '%.ts' OR filepath LIKE '%.jsx' OR filepath LIKE '%.tsx'")
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

            batch_count = 0
            while unscanned_files:
                filepath, content = random.choice(unscanned_files)
                unscanned_files.remove((filepath, content))
                batch_count += 1

                mark_scanned(filepath)

                if not content or len(content) < 50 or len(content) > 3000:
                    continue

                print(f"🔍 Elemzem ({rag_name}): {filepath} ...")
                prompt = f"""You are a strict AI architecture expert.
Your research focus is EXCLUSIVELY: Model Context Protocol (MCP) implementations, clients, servers, stdio/websocket transports, or tool/resource exposure via MCP.

Read the following file ({filepath}).
STRICT RULE: You must ONLY answer with a line starting with 'YES:' if the code ACTUALLY contains MCP specific logic (e.g. MCP server setup, MCP tool calls).
If the code is a standard API wrapper, a UI component, a database script, or DOES NOT mention MCP explicitly, YOU MUST answer with 'NO'.
If it is MCP specific, answer 'YES:' and explain what it does in 1 sentence in Hungarian.

CODE:
{content}
"""
                response = ask_llama3(prompt)

                print(f"Qwen2.5 Válasz: {response[:50]}...")
                if response.startswith("YES:") or response.startswith("YES"):
                    print(f"🚨 ÉRDEKES LELET a {rag_name} adatbázisban! Mentés a dedikált mappába...")
                    alert = {
                        "timestamp": time.time(),
                        "rag_source": rag_name,
                        "file": filepath,
                        "llama3_analysis": response
                    }
                    safe_name = filepath.replace("/", "_").replace("\\\\", "_") + ".json"

                    with open(os.path.join(rag_alert_dir, safe_name), "w", encoding="utf-8") as f:
                        json.dump(alert, f, ensure_ascii=False)

        if all_dbs_done:
            print("🏁 Minden adatbázis minden kódját feldolgoztam! Várakozás új RAG frissítésre...")
            time.sleep(10) # 10 másodpercet alszik, ha a DB kiürült

if __name__ == "__main__":
    scout_loop()
