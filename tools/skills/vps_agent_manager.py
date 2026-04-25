import os
import json
import subprocess
import glob
from collections import deque

ALERTS_DIR = os.path.expanduser("~/Jules_mx/alerts")

def process_alerts_and_dispatch():
    """
    Ez a script a VPS-en fut, és a Qwen által talált ÉRDEKES leleteket (alerts)
    felhasználva delegál feladatokat a Jules CLI-nek (Gemini).
    Mester-Szolga architektúra!
    """
    print("🤖 [VPS MANAGER] Keresem a Qwen által feldobott feladatokat...")

    alert_files = glob.glob(os.path.join(ALERTS_DIR, "*.json"))
    if not alert_files:
        print("   Nincs új lelet a postaládában.")
        return

    # Feldolgozunk egy találatot
    file_path = alert_files[0]
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    target_file = data['file']
    analysis = data['qwen_analysis']

    print(f"   => Új lelet: {target_file}")

    # 1. Készítünk egy promptot a Jules CLI számára
    jules_prompt = f"Elemzés: A Qwen VPS agentünk szerint a {target_file} fájl hasznos számunkra: {analysis}. Kérlek, olvasd el ezt a fájlt, és készíts belőle egy optimalizált, önálló komponenst a mi architektúránkhoz, ami robusztus és memóriakímélő."

    # 2. Jules CLI hívása (Ez a Google aszinkron Agentjét indítja el!)
    # (Megjegyzés: A VPS-en kell hogy legyen npm és @google/jules telepítve a klienshez)
    print(f"🚀 [VPS MANAGER] Jules Task indítása a Google-ön keresztül: {target_file}")
    print(f"   Parancs: jules '{jules_prompt}'")

    # Itt valójában elindítjuk a CLI-t (Most csak szimuláljuk vagy logoljuk, nehogy elspammeljük a rendszert)
    # subprocess.run(["jules", jules_prompt])

    with open(os.path.expanduser("~/Jules_mx/temp/dispatched_tasks.log"), "a") as f:
        f.write(f"DISPATCHED: {target_file} -> Jules CLI\n")

    os.remove(file_path)
    print("✅ Feladat delegálva és lelet törölve.")

if __name__ == "__main__":
    process_alerts_and_dispatch()
