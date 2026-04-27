import time
import sys
import os
import re
from termcolor import colored

# Elérjük a vps_bridge.py-t
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vps_bridge import run_on_vps

KNOWLEDGE_BASE_FILE = os.path.join("Knowledge_Base", "rag_findings_summary.md")
SYNC_INTERVAL = 300 # 5 perc

def extract_and_print_progress(report_content):
    """Kiolvassa a markdownból a %-os állásokat és kiírja színesen a konzolra."""
    print(colored("\n📈 Jelenlegi RAG Feldolgozottság:", "magenta", attrs=["bold"]))
    # Továbbfejlesztett regex, mert a markdown generáló frissítve lett a VPS-en
    pattern = r"- \*\*([^*]+)\*\*: (\d+) / (\d+) fájl feldolgozva"
    matches = re.findall(pattern, report_content)

    if not matches:
        print("  (Nem található folyamatjelző a jelentésben, vagy hibás a formátum)")
        return

    for match in matches:
        rag_name, scanned, total = match
        percent = (int(scanned) / int(total)) * 100 if int(total) > 0 else 0
        percent_str = f"{percent:.1f}"

        filled = int(30 * percent / 100)
        bar = "█" * filled + "░" * (30 - filled)

        print(f"  {colored(rag_name.ljust(10), 'cyan')} |{bar}| {colored(percent_str + '%', 'yellow', attrs=['bold'])} ({scanned}/{total})")
    print()

def sync_report():
    print(colored(f"[{time.strftime('%H:%M:%S')}] 🔄 Qwen RAG Jelentés szinkronizálása a VPS-ről...", "cyan"))
    try:
        run_on_vps("python3 /home/misi/Jules_mx/scripts/generate_markdown_report.py")
        success, report_content = run_on_vps("cat /home/misi/Jules_mx/alerts/alerts_summary.md")

        if success and report_content:
            os.makedirs(os.path.dirname(KNOWLEDGE_BASE_FILE), exist_ok=True)
            with open(KNOWLEDGE_BASE_FILE, "w", encoding="utf-8") as f:
                f.write(report_content)

            print(colored(f"[{time.strftime('%H:%M:%S')}] ✅ Szinkronizálás sikeres! ({len(report_content)} byte)", "green"))
            print(colored(f"A fájl megtekinthető itt: {KNOWLEDGE_BASE_FILE}", "yellow"))

            extract_and_print_progress(report_content)
        else:
            print(colored(f"⚠️ Hiba a fájl lekérésekor a VPS-ről.", "yellow"))

    except Exception as e:
        print(colored(f"❌ Kapcsolódási hiba a VPS-hez: {e}", "red"))

def start_bot():
    print(colored("🤖 Helyi RAG Szinkronizáló Bot elindítva!", "cyan", attrs=["bold"]))
    print(colored(f"Frissítési intervallum: {SYNC_INTERVAL} másodperc.", "cyan"))

    sync_report()

    while True:
        time.sleep(SYNC_INTERVAL)
        sync_report()

if __name__ == "__main__":
    start_bot()
