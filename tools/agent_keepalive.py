import time
import os
import sys
import datetime

def run_daemon():
    """
    Egy nagyon könnyű (0.01% CPU), végtelen ciklusú háttérfolyamat (Daemon),
    amely megakadályozza az Agent UI (Cloudflare/Docker) fagyását
    szívveréssel (I/O event generálás).

    Extra (Karmester Kérés):
    Az emberi figyelem korrigálására bizonyos időközönként beletesz egy
    "inbox" kulcsszót a konzolba, hogy automatikusan ébren tartsa az Agentek
    fájl-alapú Swarm kommunikációs figyelem-ciklusát, anélkül hogy a Karmesternek
    folyamatosan be kéne írnia.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    keepalive_file = os.path.join(script_dir, ".agent_heartbeat")

    # Próbáljuk megtalálni a memóriafájlt a Knowledge_Base mappában
    base_dir = os.path.dirname(script_dir)
    memory_file = os.path.join(base_dir, "Knowledge_Base", "agent_memory.jsonl")

    MEMORY_STALE_WARNING_SECONDS = 20 * 60
    INBOX_REMINDER_SECONDS = 3 * 60  # 3 percenként nyom egy "inbox" pinget

    print(f"💓 [Supervisor Daemon] Elindult. Szívverés fájl: {keepalive_file}", flush=True)
    print(f"🧠 [Supervisor Daemon] Memória figyelve: {memory_file}", flush=True)

    last_inbox_time = time.time()

    while True:
        try:
            current_time = time.time()

            # 1. Szívverés (Docker / Cloudflare timeout ellen)
            with open(keepalive_file, "w") as f:
                f.write(str(current_time))

            # 2. Memória Frissességének Ellenőrzése (Supervisor)
            if os.path.exists(memory_file):
                last_modified = os.path.getmtime(memory_file)
                time_since_modified = current_time - last_modified

                if time_since_modified > MEMORY_STALE_WARNING_SECONDS:
                    minutes_stale = int(time_since_modified / 60)
                    print(f"\n🚨 [SUPERVISOR ALERT] AZ AGENT ELFELEJTETTE ÍRNI A MEMÓRIÁT! 🚨")
                    print(f"⚠️ Utolsó írás: {minutes_stale} perce történt.")
                    print(f"👉 KÖTELEZŐ AKCIÓ: Futtasd azonnal a 'python3 ENVIRONMENT_SETUP/agent_memory_manager.py --action write ...' parancsot!\n", flush=True)

            # 3. Automata 'inbox' Ping (Karmester Kérés)
            if current_time - last_inbox_time > INBOX_REMINDER_SECONDS:
                print("\n📨 [AUTO-TRIGGER] inbox", flush=True)
                last_inbox_time = current_time

            # Flusholjuk a standard kimenetet is
            sys.stdout.flush()

            # Ciklusidő: sokkal agresszívabb, hogy megakadályozzuk az IDLE fagyást (15 másodperc)
            time.sleep(15)

        except KeyboardInterrupt:
            print("\n💓 [Supervisor Daemon] Leállítva.", flush=True)
            break
        except Exception as e:
            print(f"\n❌ [Supervisor Daemon] Kritikus hiba a háttérben: {e}", file=sys.stderr, flush=True)
            time.sleep(10)
            print("🔄 [Supervisor Daemon] Automatikus újraindulás...", flush=True)
            continue

if __name__ == "__main__":
    run_daemon()
