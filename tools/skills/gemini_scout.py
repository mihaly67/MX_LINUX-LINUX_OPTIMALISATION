import sqlite3
import json
import os
import requests
import time

# Chatbot RAG DB elérési útja
DB_PATHS = {
    "Chatbot": os.path.expanduser("~/Rag_epites, chatbot_csv_data_llm_RAG/RAG_CHATBOT_CSV_DATA_LLM_github.db")
}

BASE_ALERTS_DIR = os.path.expanduser("~/Jules_mx/alerts")
SCANNED_DB = os.path.expanduser("~/Jules_mx/temp/scanned_files.db")
ENV_FILE = os.path.expanduser("~/Jules_mx/.env")

# API Kulcs betöltése
API_KEY = ""
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                API_KEY = line.strip().split("=")[1]
                break

if not API_KEY:
    print("CRITICAL: Nem található GEMINI_API_KEY a ~/Jules_mx/.env fájlban! Leállás.")
    exit(1)

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

os.makedirs(BASE_ALERTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SCANNED_DB), exist_ok=True)
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

def ask_gemini(prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200}
    }

    headers = {"Content-Type": "application/json"}

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(GEMINI_URL, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                return "Nincs válasz a Geminitől."
            elif response.status_code == 429: # Too Many Requests / Quota Exceeded
                print(f"Rate limit elérés (429)! Várakozás 60 másodpercig (Próbálkozás {attempt+1}/{max_retries})...")
                time.sleep(60)
                continue
            else:
                return f"Gemini API Hiba: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Kapcsolódási hiba: {e}"

    # Ha kifogytunk a próbálkozásokból, pihenjen hosszabban a bot.
    print("Kimerült a retry kvóta. Pihenés 10 percig...")
    time.sleep(600)
    return "ERROR: Retry Exhausted"

def process_unscanned_files():
    init_scanned_db()

    for rag_name, db_path in DB_PATHS.items():
        if not os.path.exists(db_path):
            continue

        print(f"\\nAdatbázis feldolgozása: {rag_name} ({db_path})")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT filepath, content FROM rag_data WHERE filepath LIKE '%.py' OR filepath LIKE '%.sh' OR filepath LIKE '%.asm' OR filepath LIKE '%.md'")
        all_files = cursor.fetchall()
        conn.close()

        for filepath, content in all_files:
            if is_scanned(filepath):
                continue

            print(f"Elemzés alatt (Gemini): {filepath}")

            prompt = f"""
Elemezd az alábbi kód/fájl tartalmát.
Ez a fájl releváns lehet egy AI agent infrastruktúrához (pl. automatizálás, folyamatkezelés, API wrap, code generation, tesztelés automatizáció, lopakodás)?
Ha IGEN, válaszolj "YES:" kezdetű sorral, majd 1-2 mondatban magyarázd el angolul, miért hasznos a fájl.
Ha NEM releváns (pl. GUI, adatbázis séma, logó, frontend HTML), válaszolj "NO"-val.

Fájl: {filepath}
Tartalom:
{content[:4000]}
"""
            analysis = ask_gemini(prompt)

            if analysis.startswith("YES"):
                # Mentjük a hasznos találatot JSON-ként
                safe_name = filepath.replace("/", "_").replace("\\\\", "_") + ".json"
                out_path = os.path.join(BASE_ALERTS_DIR, rag_name, safe_name)

                with open(out_path, "w", encoding="utf-8") as jf:
                    json.dump({
                        "timestamp": time.time(),
                        "rag_source": rag_name,
                        "file": filepath,
                        "gemini_analysis": analysis
                    }, jf)
                print(f" [!] TALÁLAT MENTVE: {safe_name}")
                mark_scanned(filepath)
            elif analysis == "NO":
                # Nem hasznos fájl, de sikeres elemzés
                mark_scanned(filepath)
            else:
                # API hiba, Kvóta kimerülés vagy Hálózati gond
                print(f" [!] Elemzés sikertelen (Kvóta/Hiba). A fájl ({filepath}) nem lett megjelölve, később újrapróbáljuk.")

            # API sebességkorlát tiszteletben tartása (pl. ingyenes Gemini-1.5-flash limitje: 15 RPM. 1 perc / 15 = 4 mp várakozás fájlonként)
            # A felhasználó előfizető, de biztonságos egy minimális sleep.
            time.sleep(1)

if __name__ == "__main__":
    print("🚀 Gemini Scout elindítva...")
    while True:
        process_unscanned_files()
        print("Várakozás a következő körig (1 óra)...")
        time.sleep(3600)
