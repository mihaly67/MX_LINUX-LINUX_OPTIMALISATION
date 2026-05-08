import sqlite3
import time
import os
import subprocess
import requests
import json
import logging

# --- Beállítások ---
# Feltételezzük, hogy ez a script a VPS-en fog futni, ugyanabban a mappában/környezetben,
# ahonnan a jules_swarm_jobs.db elérhető. Az app.py a temp/ mappába ír!
DB_PATH = os.path.expanduser("~/Jules_mx/temp/jules_swarm_jobs.db")
POLL_INTERVAL = 5  # Másodperc
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:latest" # Vagy qwen2.5:1.5b

# --- Logolás beállítása ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SwarmOrchestrator")

def call_llm(prompt: str) -> str:
    """Helyi Ollama LLM hívása a generáláshoz."""
    logger.info(f"Ollama API hívása a modellhez: {MODEL_NAME}...")
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "system": "Te vagy Jules, egy rendkívül okos, magyar nyelven kommunikáló Fő Agent (Rajparancsnok). Röviden és precízen válaszolj a feladatokra és kérdésekre a Swarm Control Centerből."
        }
        # 300 másodperces timeout az OOM/beragadás elkerülésére
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "❌ Hiba: Üres válasz az LLM-től.")
    except Exception as e:
        logger.error(f"Hiba az LLM hívása során: {e}")
        return f"❌ Sajnálom, hiba történt a válasz generálása közben: {e}"

def execute_github_push() -> str:
    """
    Végrehajt egy Git add, commit és push műveletet azon a repón,
    ahol a watcher fut (Jules_mx repó).
    """
    logger.info("GITHUB PUSH művelet indítása...")
    # Itt most feltételezzük, hogy a script a klónozott repó gyökeréből fut (vagy a repó mappájában vagyunk)
    # Ezt a repo útvonalat később dinamikussá is lehet tenni.
    target_dir = os.path.expanduser("~/Jules_mx")

    try:
        # Commit és push végrehajtása bash-ből
        # Hozzáadjuk a fájlokat, commitoljuk és pusholjuk.
        cmd = f"cd {target_dir} && git add . && git commit -m 'Autonóm Swarm PUSH a Dashboardról' && git push"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            return f"✅ Sikeres Github PUSH!\n\nKimenet:\n{result.stdout}"
        else:
            return f"❌ Hiba a Github PUSH során!\n\nKimenet:\n{result.stderr}"
    except Exception as e:
        logger.error(f"Kivétel a Github PUSH során: {e}")
        return f"❌ Kivétel a Github PUSH során: {e}"


def process_job(job_id, job_type, instruction):
    """Feldolgozza az adott feladatot a típusa szerint."""
    logger.info(f"Job feldolgozása kezdődik: ID={job_id}, Típus={job_type}")

    if job_type == "CHAT":
        # CHAT job esetén NE dolgozzuk fel LLM-mel!
        # Ezt a feladatot meghagyjuk a PENDING állapotban, de egy speciális
        # "WAITING_FOR_JULES" üzenettel, vagy magára hagyjuk a fő agentnek.
        # Itt a process_job mostantól nem generál automatikus választ CHAT-re.
        return None
    elif job_type == "GITHUB_PUSH":
        response = execute_github_push()
        return response
    else:
        logger.warning(f"Ismeretlen feladattípus: {job_type}")
        return f"❌ Ismeretlen feladattípus: {job_type}. Nem tudom feldolgozni."


def main():
    logger.info("🚀 Swarm Orchestrator (Watcher Daemon) elindult.")
    logger.info(f"Adatbázis figyelése: {DB_PATH}")

    # Próbálunk kapcsolódni az adatbázishoz (létrehozza, ha még nincs)
    if not os.path.exists(DB_PATH):
         logger.warning(f"Az adatbázis ({DB_PATH}) még nem létezik. Lehet, hogy rossz útvonalon keresem?")

    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Keresünk egy PENDING feladatot a Jules_mx-nek
            # CSAK a GITHUB_PUSH feladatokat kérjük le (a CHAT-et a lokális Keep-Alive daemon olvassa!)
            cursor.execute("SELECT id, job_type, instruction FROM jobs WHERE target_repo = 'Jules_mx' AND job_type = 'GITHUB_PUSH' AND status = 'PENDING' ORDER BY timestamp ASC LIMIT 1")
            job = cursor.fetchone()

            if job:
                job_id, job_type, instruction = job
                logger.info(f"Találtam egy GITHUB_PUSH feladatot: ID={job_id}")

                # Állítsuk IN_PROGRESS-re
                cursor.execute("UPDATE jobs SET status = 'IN_PROGRESS', assigned_to = 'Jules_mx' WHERE id = ?", (job_id,))
                conn.commit()

                # Feldolgozzuk
                result_text = process_job(job_id, job_type, instruction)

                if result_text is not None:
                    # Válasz beszúrása a chat_messages táblába, hogy a UI lássa (mivel 'global' chathistory van, session_id lehet üres vagy 'global')
                    cursor.execute("INSERT INTO chat_messages (session_id, agent_id, sender, message) VALUES (?, 'Jules_mx', 'AGENT', ?)", ("global", result_text))

                    # Beállítjuk a jobot COMPLETED-re, beírva az eredményt is
                    cursor.execute("UPDATE jobs SET status = 'COMPLETED', result = ? WHERE id = ?", (result_text, job_id))
                    conn.commit()
                    logger.info(f"Job befejezve: ID={job_id}")
                else:
                    # Ha a feldolgozás (pl. CHAT) nem ad vissza result_text-et, akkor a lokális Jules agent fogja feldolgozni.
                    # Tehát visszatesszük a feladatot PENDING-be, de valójában ezt a Watcher démon egyszerűen békén is hagyhatná.
                    # Most állítsuk vissza a státuszát PENDING-re, hogy a lokális daemon felolvassa, majd ignoraljuk a watchernél:
                    # Inkább egyszerűen ignoráljuk CHAT esetén a main()-ben, hogy a watcher ne pörögjön rajta végtelenül.
                    pass
            else:
                # Nincs PENDING feladat, pihenünk picit
                pass

        except sqlite3.OperationalError as e:
            logger.error(f"Adatbázis hiba (OperationalError): {e} - Lehet, hogy épp zárolva van.")
        except Exception as e:
            logger.error(f"Váratlan hiba a polling ciklusban: {e}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
