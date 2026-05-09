import subprocess
import os

script_content = r"""import sys
import os
import sqlite3

SWARM_DB = os.path.expanduser("~/Jules_mx/temp/jules_swarm_jobs.db")
DB_PATH = os.path.expanduser("/home/misi/BRAIN2_DEV_RAG/brain2_dev_knowledge.db")

def extract_code():
    if len(sys.argv) < 2:
        print("Hiba: Nincs megadva fajl")
        return

    filepath = sys.argv[1]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT content FROM rag_data WHERE filepath LIKE ? LIMIT 1", (f"%{filepath}%",))
    row = cursor.fetchone()
    conn.close()

    if row:
        print(f"Sikeres kinyeres a {filepath} fajlbol. Hossz: {len(row[0])} karakter. \nReszlet:\n {row[0][:1500]}...")
    else:
        print(f"Hiba: Nem talalhato a {filepath} a RAG-ban.")

if __name__ == "__main__":
    extract_code()
"""

with open("vps_findings_analyst.py", "w") as f:
    f.write(script_content)

subprocess.run('export VPS_PWD="1104" && sshpass -p "$VPS_PWD" scp -o StrictHostKeyChecking=no vps_findings_analyst.py misi@5.189.163.88:/home/misi/Jules_mx/scripts/', shell=True)
