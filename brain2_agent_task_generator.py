import os
import sqlite3
import json
import glob

ALERTS_DIR = os.path.expanduser("~/Jules_mx/alerts/BRAIN2")
SWARM_DB = os.path.expanduser("~/Jules_mx/temp/jules_swarm_jobs.db")

def generate_tasks_from_brain2():
    alert_files = glob.glob(os.path.join(ALERTS_DIR, "*.json"))
    if not alert_files:
        print("Nincsenek feldolgozatlan JSON találatok a BRAIN2 mappában.")
        return

    conn = sqlite3.connect(SWARM_DB)
    cursor = conn.cursor()

    print(f"Összesen {len(alert_files)} leletet találtam.")
    for idx, file_path in enumerate(alert_files, 1):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            target_file = data.get('file', 'Unknown')
            analysis = data.get('gemini_analysis', data.get('llama3_analysis', data.get('qwen_analysis', 'Nincs elemzés')))

            # A swarm rajtag index kiszámítása (raj1-raj8)
            # Körforgásos elosztás
            raj_id = f"raj{(idx % 8) + 1}"

            instruction = f"Kérlek olvasd el és dolgozd fel a BRAIN2 RAG adatbázisból származó találatot! Célpont: {target_file}. Részletek: {analysis}. Fejts vissza belőle minden hasznos architektúra / kód logikát ami a webes chat kiváltására használható!"

            cursor.execute("INSERT INTO jobs (job_type, target_repo, instruction, status) VALUES (?, ?, ?, ?)",
                           ('CHAT', raj_id, instruction, 'PENDING'))
            print(f"Delegálva {raj_id}-nek: {target_file}")

            # Átmozgatás egy feldolgozott mappába, hogy ne kerüljön duplán feldolgozásra
            processed_dir = os.path.join(ALERTS_DIR, "processed")
            os.makedirs(processed_dir, exist_ok=True)
            os.rename(file_path, os.path.join(processed_dir, os.path.basename(file_path)))

        except Exception as e:
            print(f"Hiba a {file_path} feldolgozásakor: {e}")

    conn.commit()
    conn.close()
    print("Minden feladat kiosztva a swarmnak!")

if __name__ == '__main__':
    generate_tasks_from_brain2()
