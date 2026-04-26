import os
import json
from termcolor import colored

# Elérési út a helyi gépen futtatva a VPS bridge-n keresztül, vagy egyenesen a VPS-en
ALERTS_DIR = os.path.expanduser("~/Jules_mx/alerts")

def display_findings():
    print(colored("📊 QWEN SCOUT RAG LELETEK ÁTTEKINTÉSE", "cyan", attrs=["bold"]))
    print(colored("="*60, "cyan"))

    if not os.path.exists(ALERTS_DIR):
        print(colored("A mappa nem létezik. (Biztos a VPS-en futtatod?)", "red"))
        return

    rag_folders = [f for f in os.listdir(ALERTS_DIR) if os.path.isdir(os.path.join(ALERTS_DIR, f))]

    if not rag_folders:
        print(colored("Még nincsenek RAG mappák létrehozva.", "yellow"))
        return

    for rag in rag_folders:
        rag_path = os.path.join(ALERTS_DIR, rag)
        files = [f for f in os.listdir(rag_path) if f.endswith('.json')]

        print(colored(f"\n📂 RAG: {rag} ({len(files)} találat)", "green", attrs=["bold"]))
        print("-" * 60)

        if not files:
            print("  Nincs még lelet ebben a RAG-ban.")
            continue

        for i, f in enumerate(files[:10]): # Csak az első 10-et mutatjuk RAG-onként, hogy ne legyen túl sok
            filepath = os.path.join(rag_path, f)
            try:
                with open(filepath, "r") as jf:
                    data = json.load(jf)
                    source_file = data.get("file", "Ismeretlen fájl")
                    analysis = data.get("qwen_analysis", "").strip()

                    # Csak az első mondatot / összefoglalót írjuk ki
                    short_analysis = analysis.split("\n")[0]
                    if len(short_analysis) > 100:
                        short_analysis = short_analysis[:97] + "..."

                    print(colored(f"  {i+1}. Fájl: {source_file}", "yellow"))
                    print(f"     Értékelés: {short_analysis}\n")
            except Exception as e:
                print(f"  Hiba a fájl olvasásakor: {f}")

        if len(files) > 10:
            print(colored(f"  ... és még {len(files) - 10} további lelet ebben a RAG-ban.", "magenta"))

if __name__ == "__main__":
    display_findings()
