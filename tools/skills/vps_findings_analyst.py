import argparse
import sys
import os
import json
import re

# Felszabadítjuk a vps_bridge importját
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vps_bridge import run_on_vps

def search_and_analyze(query, max_files=10):
    print(f"🔍 1. Lépés: Gyors előszűrés a VPS JSON fájljain a '{query}' kulcsszóra...")

    # Egy gyors python egysoros futtatása a VPS-en ami kigreppeli a JSON fájlokat és visszaadja a top X releváns tartalmát
    # Escape-eljük a query-t hogy ne törje el a scriptet
    safe_query = query.replace('"', '\\"').replace("'", "\\'")

    vps_python_script = f"""
import os, json, re

ALERTS_DIR = '/home/misi/Jules_mx/alerts/Chatbot'
query = '{safe_query}'.lower()
results = []

for root, _, files in os.walk(ALERTS_DIR):
    for file in files:
        if file.endswith('.json'):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if query in content.lower():
                        data = json.loads(content)
                        results.append({{"file": data.get("file", file), "analysis": data.get("llama3_analysis", "")}})
            except Exception:
                pass

# Rendezzük a leghosszabb elemzések szerint (feltételezve hogy az a legrészletesebb)
results.sort(key=lambda x: len(x["analysis"]), reverse=True)
top_results = results[:{max_files}]

print(json.dumps(top_results))
"""

    # A bash scriptként küldött python egy command, amihez a dupla idézőjelek ne okozzanak bajt
    import base64
    b64_script = base64.b64encode(vps_python_script.encode('utf-8')).decode('utf-8')
    cmd = f"python3 -c \"import base64; exec(base64.b64decode('{b64_script}').decode('utf-8'))\""

    success, result = run_on_vps(cmd)
    if not success or not result.strip():
        return f"Hiba az előszűréskor vagy nem található egyezés a VPS-en: {result}"

    try:
        top_findings = json.loads(result.strip())
    except json.JSONDecodeError as e:
        return f"Hiba a JSON feldolgozásakor a VPS-ről: {e}\nNyers válasz: {result[:500]}"

    if not top_findings:
        return f"Nincs találat a Chatbot RAG json fájljai között a '{query}' keresésre."

    print(f"🧠 2. Lépés: {len(top_findings)} legrelevánsabb találat szintetizálása a VPS Llama 3 modellel...")

    # Felépítjük a promptot a Llama 3-nak a szűrt adatokból
    context_text = "\n\n".join([f"Fájl: {item['file']}\nElemzés: {item['analysis']}" for item in top_findings])

    prompt = f"""Te egy AI Rendszerelemző Bot vagy. A feladatod a következő RAG találatok összefoglalása és szintézise a megadott téma alapján.
Téma: {query}

Találatok:
{context_text}

Kérlek, magyar nyelven, szakmai, de érthető formában foglald össze:
1. Milyen hasznos kódokat / eszközöket találtunk a témában?
2. Hogyan tudná ezeket a Fő Agent (Jules) a saját eszköztárába (skills) vagy autonóm folyamataiba integrálni?

Légy tömör és fókuszálj a gyakorlati megvalósíthatóságra!
"""

    # Hívjuk a Llama 3-at a VPS-en
    payload = {"model": "llama3", "prompt": prompt, "stream": False}
    payload_str = json.dumps(payload).replace("'", "'\\''")
    curl_command = f"curl -s -X POST http://localhost:11434/api/generate -H 'Content-Type: application/json' -d '{payload_str}'"

    success, llm_result = run_on_vps(curl_command)

    if success and llm_result:
        try:
            data = json.loads(llm_result)
            return data.get("response", "Nincs válasz az Ollamától.")
        except json.JSONDecodeError:
            return "JSON dekódolási hiba az Ollama válaszában:\n" + llm_result
    else:
        return "Hiba a VPS LLM elérésében: " + str(llm_result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VPS Találat Elemző Bot (RAG JSON Szintetizátor)")
    parser.add_argument("--query", required=True, help="A keresett téma vagy kulcsszó (pl. 'memory', 'agent').")
    parser.add_argument("--max", type=int, default=10, help="Maximum hány találatot dolgozzon fel a LLM egyszerre (OOM elkerülésére).")
    args = parser.parse_args()

    answer = search_and_analyze(args.query, args.max)
    print("\n===============================")
    print("🤖 TALÁLAT ELEMZŐ JELENTÉSE")
    print("===============================\n")
    print(answer)
