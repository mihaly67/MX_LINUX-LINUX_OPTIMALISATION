import os
import sys
import json
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(script_dir)
sys.path.append(tools_dir)
import vps_bridge

MEMORY_FILE = os.path.join(os.path.dirname(tools_dir), "Knowledge_Base", "agent_memory.jsonl")
REMOTE_MEMORY_FILE = "/home/misi/Jules_mx/memory_offload/backup.jsonl"
SERVER_URL = "http://localhost:8000/summarize_memory"

def upload_memory():
    print("📤 Lokális memória szinkronizálása a VPS-re...")
    vps_bridge.upload_to_vps(MEMORY_FILE, REMOTE_MEMORY_FILE)

def ask_secretary():
    print("🧠 A VPS Titkár olvassa a memóriát...")
    # Használjuk a frissített FastAPI micro-server végpontját!
    command = f"curl -s -X POST -H 'Content-Type: application/json' -d '{{\"limit_lines\": 10}}' {SERVER_URL}"
    success, out = vps_bridge.run_on_vps(command)

    if success:
        try:
            resp = json.loads(out)
            summary = resp.get("summary", "Üres vagy hibás JSON válasz.")
            print("\n" + "="*50)
            print("📝 VPS TITKÁR JELENTÉSE (Utolsó események összefoglalója):")
            print("="*50)
            print(summary.strip())
            print("="*50 + "\n")
        except json.JSONDecodeError:
            print(f"❌ JSON parse hiba a titkár válaszában: {out}")
    else:
        print(f"❌ Titkár lekérdezése sikertelen: {out}")

def get_last_n_turns(n=5):
    """Fallback funkció, ha a VPS nem elérhető: csak az utolsó N turn olvasása fájlból (0 overhead)."""
    if not os.path.exists(MEMORY_FILE):
         return "A memória üres."

    entries = []
    with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except:
                    pass

    recent = entries[-n:]
    output = f"🧠 LOKÁLIS TITKÁR (Utolsó {n} bejegyzés, OOM-safe mód):\n"
    for e in recent:
        output += f"[{e.get('timestamp', '')[:16]}] {e.get('category', '')}: {e.get('content', '')}\n"
    print(output)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true", help="Csak a lokális tail olvasás (gyors, nincs hálózat)")
    parser.add_argument("--limit", type=int, default=5, help="Hány sort olvasson (csak --local esetén)")
    args = parser.parse_args()

    if args.local:
        get_last_n_turns(args.limit)
    else:
        upload_memory()
        ask_secretary()
