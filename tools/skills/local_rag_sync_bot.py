import time
import requests
import os
from termcolor import colored

VPS_URL = "http://5.189.163.88:8000"
KNOWLEDGE_BASE_FILE = os.path.join("Knowledge_Base", "rag_findings_summary.md")
SYNC_INTERVAL = 300 # 5 perc

def sync_report():
    print(colored(f"[{time.strftime('%H:%M:%S')}] 🔄 Qwen RAG Jelentés szinkronizálása a VPS-ről...", "cyan"))
    try:
        # A Micro-server helyett most már vps_bridge-n keresztül SSH-zunk be lekérni a fájlt
        import sys
        import os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from vps_bridge import run_remote_command

        # Generáljuk a riportot
        run_remote_command("python3 /home/misi/Jules_mx/scripts/generate_markdown_report.py")
        # Lekérjük a riportot
        success, report_content = run_remote_command("cat /home/misi/Jules_mx/alerts/alerts_summary.md")

        if success and report_content:
            os.makedirs(os.path.dirname(KNOWLEDGE_BASE_FILE), exist_ok=True)
            with open(KNOWLEDGE_BASE_FILE, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(colored(f"[{time.strftime('%H:%M:%S')}] ✅ Szinkronizálás sikeres! ({len(report_content)} byte)", "green"))
            print(colored(f"A fájl megtekinthető itt: {KNOWLEDGE_BASE_FILE}", "yellow"))
        else:
            print(colored(f"⚠️ Hiba a fájl lekérésekor a VPS-ről.", "yellow"))

    except Exception as e:
        print(colored(f"❌ Kapcsolódási hiba a VPS-hez: {e}", "red"))

def start_bot():
    print(colored("🤖 Helyi RAG Szinkronizáló Bot elindítva!", "cyan", attrs=["bold"]))
    print(colored(f"Frissítési intervallum: {SYNC_INTERVAL} másodperc.", "cyan"))

    # Próbáljuk meg azonnal
    sync_report()

    while True:
        time.sleep(SYNC_INTERVAL)
        sync_report()

if __name__ == "__main__":
    start_bot()
