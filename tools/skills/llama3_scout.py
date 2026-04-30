import sqlite3
import random
import json
import os
import requests
import time

# Dinamikus RAG váltó - mind a 3 RAG DB elérési útja és rövid neve a csoportosításhoz
DB_PATHS = {
    "Chatbot": {
        "path": os.path.expanduser("~/Rag_epites, chatbot_csv_data_llm_RAG/RAG_CHATBOT_CSV_DATA_LLM_github.db"),
        "prompt_goal": "A Fő Agent környezetem fejlesztése, autonóm működés optimalizálása, memóriakezelés, kontextus-sűrítés és tehermentesítés. Keresd az agent loop, memória (short/long term), retry policy és tool routing megoldásokat."
    },
    "Gerilla": {
        "path": os.path.expanduser("~/Gerilla_RAG/Gerilla_RAG.db"),
        "prompt_goal": "Hálózat, proxy (stealth, evasion), API integráció, VPS hardver maximális de törvényes kihasználása, OOM elkerülése, mini LLM-ek hatékony alkalmazása, folyamatautomatizálás."
    },
    "MX_Linux": {
        "path": os.path.expanduser("~/MX_LINUX_RAG/mx_linux_knowledge.db"),
        "prompt_goal": "Kifejezetten az MX Linux OS operációs rendszer szintű fejlesztése, optimalizálása, bash scriptek és kernel tuning."
    }
}

OLLAMA_URL = "http://localhost:11434/api/generate"
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
        "model": "llama3",
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 150, "temperature": 0.1}
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        return resp.json().get("response", "")
    except Exception as e:
        return f"Error: {e}"

def scout_loop():
    print("🤖 Llama3 Scout elindult... (Multi-RAG Dinamikus Váltással, PADLÓGÁZON)")
    init_scanned_db()

    while True:
        all_dbs_done = True

        for rag_name, config in DB_PATHS.items():
            db_path = config["path"]
            prompt_goal = config["prompt_goal"]

            if not os.path.exists(db_path):
                print(f"⚠️ Nem található adatbázis: {db_path}")
                continue

            print(f"\\n📂 RAG Adatbázis elemzése: {db_path} (Csoport: {rag_name})")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                # Szigorúan csak kód fájlok (no bloat)
                cursor.execute("SELECT filepath, content FROM rag_data WHERE filepath LIKE '%.py' OR filepath LIKE '%.sh' OR filepath LIKE '%.asm' OR filepath LIKE '%.c' OR filepath LIKE '%.cpp' OR filepath LIKE '%.js' OR filepath LIKE '%.ts'")
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
            while unscanned_files and batch_count < 2000:
                filepath, content = random.choice(unscanned_files)
                unscanned_files.remove((filepath, content))
                batch_count += 1

                mark_scanned(filepath)

                if not content or len(content) < 50 or len(content) > 3000:
                    continue

                print(f"🔍 Elemzem ({rag_name}): {filepath} ...")
                prompt = f"""Te egy AI architecture és Python szakértő asszisztens vagy.
A fő kutatási fókusz/kritérium ehhez az adatbázishoz: {prompt_goal}

Ez a fájl ({filepath}) tartalmazza a fent felsorolt kritériumoknak megfelelő hasznos kódot vagy logikát, amit átvehetünk egy saját Autonóm Agent be?
Ha IGEN, válaszolj 'YES:' kezdetű sorral, majd 1-2 mondatban magyarázd el magyarul, miért hasznos a fájl.
Ha NEM releváns (pl. GUI, adatbázis séma, teszt dummy data, frontend HTML), válaszolj 'NO'-val.

CODE:
{content}
"""
                response = ask_llama3(prompt)

                if response.startswith("YES:"):
                    print(f"🚨 ÉRDEKES LELET a {rag_name} adatbázisban! Mentés a dedikált mappába...")
                    alert = {
                        "timestamp": time.time(),
                        "rag_source": rag_name,
                        "file": filepath,
                        "llama3_analysis": response
                    }
                    safe_name = filepath.replace("/", "_").replace("\\\\", "_")

                    rag_alert_dir = os.path.join(BASE_ALERTS_DIR, rag_name)
                    with open(os.path.join(rag_alert_dir, f"{safe_name}.json"), "w", encoding="utf-8") as f:
                        json.dump(alert, f, ensure_ascii=False)

        if all_dbs_done:
            print("🏁 Minden adatbázis minden kódját feldolgoztam! Várakozás új RAG frissítésre...")
            time.sleep(180) # 3 percet alszik, hátha jön új fájl

if __name__ == "__main__":
    scout_loop()
