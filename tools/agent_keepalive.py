import time
import os
import sys
import datetime
import subprocess
import json

def fetch_pending_jobs():
    """Lekérdezi az MCP bridge-en keresztül a VPS-ről a PENDING CHAT jobokat."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mcp_tool = os.path.join(script_dir, "skills", "mcp_bridge_tool.py")

    # Csak környezeti változókból olvassuk a jelszót/kulcsot, nem égetjük be a kódba!
    env = os.environ.copy()

    cmd = [
        "python3", mcp_tool,
        "--tool", "execute_bash",
        "--args", '{"command": "sqlite3 /home/misi/Jules_mx/temp/jules_swarm_jobs.db \\"SELECT id, instruction FROM jobs WHERE target_repo=\'Jules_mx\' AND job_type=\'CHAT\' AND status=\'PENDING\' ORDER BY timestamp ASC LIMIT 1;\\""}'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)

        # Tisztítjuk a kimenetet, megpróbáljuk megtalálni az igazi adatot a sok MCP log között
        output = result.stdout.strip()

        # Mivel az MCP bridge kiírja a "STDOUT:" és "STDERR:" sorokat, parzolnunk kell:
        if "STDOUT:" in output:
            stdout_part = output.split("STDOUT:")[1].split("STDERR:")[0].strip()
            if stdout_part and stdout_part != "":
                # Ellenőrizzük, hogy valóban egy valid id|instruction formátum-e (tartalmaz '|')
                if "|" in stdout_part:
                    return stdout_part
        return None
    except Exception as e:
        # Ne spammeljük tele a konzolt, ha hálózati hiba van
        pass
    return None

def run_daemon():
    """
    Egy nagyon könnyű (0.01% CPU), végtelen ciklusú háttérfolyamat (Daemon),
    amely nemcsak az Agent UI (Cloudflare/Docker) fagyását akadályozza meg
    szívveréssel (I/O event generálás), hanem SUPERVISOR-ként is működik.

    Ha a Hosszútávú Memória fájlt (agent_memory.jsonl) túl régóta (pl. 20 perc)
    nem módosította az Agent, hangos figyelmeztetést (ALERT) ír a logba,
    amit az Agent észrevehet, mielőtt elveszítené a kontextust!
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    keepalive_file = os.path.join(script_dir, ".agent_heartbeat")

    # Próbáljuk megtalálni a memóriafájlt a Knowledge_Base mappában
    base_dir = os.path.dirname(script_dir)
    memory_file = os.path.join(base_dir, "Knowledge_Base", "agent_memory.jsonl")

    # Mivel egy agent turn kb 2-5 perc, 15-20 perc memóriaírás nélkül már aggasztó
    MEMORY_STALE_WARNING_SECONDS = 20 * 60

    print(f"💓 [Supervisor Daemon] Elindult. Folyamatos szívverés generálása: {keepalive_file}", flush=True)
    print(f"🧠 [Supervisor Daemon] Memória figyelve: {memory_file}", flush=True)

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
                    print(f"👉 KÖTELEZŐ AKCIÓ: Futtasd azonnal a 'python3 ENVIRONMENT_SETUP/agent_memory_manager.py --action write ...' parancsot a szinkronizációhoz!\n", flush=True)
            else:
                 print(f"⚠️ [SUPERVISOR ALERT] A memória fájl ({memory_file}) NEM LÉTEZIK! Használd a memory managert a létrehozásához!", flush=True)

            # 3. Új Jobok (CHAT) Keresése az SQLite-ban (Minden 3. ciklusban = 45 mp)
            # Biztosabb ciklus számlálót használunk
            if not hasattr(run_daemon, "loop_count"):
                run_daemon.loop_count = 0
            run_daemon.loop_count += 1

            if run_daemon.loop_count % 3 == 0:
                pending_job = fetch_pending_jobs()
                if pending_job:
                    print(f"\n\n{'='*60}")
                    print(f"🚨🚨 [SWARM ORCHESTRATOR] ÚJ ÜZENET A TUI-BÓL! 🚨🚨")
                    print(f"👉 ÜZENET: {pending_job}")
                    print(f"👉 KÖTELEZŐ AKCIÓ: Kérlek olvasd el, reagálj a fenti üzenetre, és használd a jules_swarm_jobs.db-t (UPDATE status='COMPLETED') a válaszadásra!")
                    print(f"{'='*60}\n\n", flush=True)

            # Flusholjuk a standard kimenetet is
            sys.stdout.flush()

            # Ciklusidő: sokkal agresszívabb, hogy megakadályozzuk az IDLE fagyást (15 másodperc)
            time.sleep(15)

        except KeyboardInterrupt:
            print("\n💓 [Supervisor Daemon] Leállítva.", flush=True)
            break
        except Exception as e:
            print(f"\n❌ [Supervisor Daemon] Kritikus hiba a háttérben: {e}", file=sys.stderr, flush=True)
            # Az önreflexió jegyében, ha lehal a daemon, automatikusan próbáljon újraindulni kis pihenő után,
            # hogy ne maradjon a rendszer szívverés nélkül (rekurzió nélkül).
            time.sleep(10)
            print("🔄 [Supervisor Daemon] Automatikus újraindulás...", flush=True)
            continue

if __name__ == "__main__":
    run_daemon()
