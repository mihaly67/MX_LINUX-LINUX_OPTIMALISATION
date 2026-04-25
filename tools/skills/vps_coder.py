import os
import sys
import json
import argparse

script_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(script_dir)
sys.path.append(tools_dir)
import vps_bridge

VPS_API_URL = "http://localhost:8000"

def ask_vps_coder(prompt):
    print("🧠 VPS Qwen (Kódoló Asszisztens) gondolkodik...")

    # A curl parancs, amit elküldünk a VPS-re
    escaped_prompt = prompt.replace("'", "'\\''").replace('"', '\\"')
    command = f"curl -s -X POST -H 'Content-Type: application/json' -d '{{\"prompt\": \"{escaped_prompt}\"}}' {VPS_API_URL}/code_assist"

    success, out = vps_bridge.run_on_vps(command)
    if success:
        try:
            resp = json.loads(out)
            response = resp.get("response", "Nincs érvényes válasz.")
            error = resp.get("error", "")
            if error:
                print(f"❌ Szerver hiba: {error}")
            else:
                print("\n" + "="*50)
                print("💻 VPS CODER VÁLASZA:")
                print("="*50)
                print(response)
                print("="*50 + "\n")
        except json.JSONDecodeError:
             print(f"❌ JSON parse hiba: {out}")
    else:
        print(f"❌ SSH/Kapcsolat hiba: {out}")

def get_scout_progress():
    print("📊 Qwen Scout haladásának lekérdezése...")
    command = f"curl -s {VPS_API_URL}/scout_progress"
    success, out = vps_bridge.run_on_vps(command)
    if success:
        try:
            resp = json.loads(out)
            progress = resp.get("progress", {})
            for k, v in progress.items():
                if k == "TOTAL":
                    print(f"\\n   🔥 ÖSSZESEN: {v}")
                else:
                    print(f"   - {k}: {v}")
        except json.JSONDecodeError:
            print(f"❌ Hiba a haladás lekérdezésekor: {out}")

if __name__ == "__main__":
    # Autentikáció környezeti változóból vagy kulccsal működik a háttérben a vps_bridge miatt
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, help="A kódolási kérdés a Qwen felé")
    parser.add_argument("--progress", action="store_true", help="Lekérdezi a Qwen Scout haladását")
    args = parser.parse_args()

    if args.progress:
        get_scout_progress()
    elif args.prompt:
        ask_vps_coder(args.prompt)
    else:
        print("Használat: python3 vps_coder.py --prompt 'Hogyan csináljak XYZ-t Pythonban?' VAGY python3 vps_coder.py --progress")
