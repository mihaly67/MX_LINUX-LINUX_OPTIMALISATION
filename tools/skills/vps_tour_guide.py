import argparse
import sys
import os

# Felszabadítjuk a vps_bridge importját
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vps_bridge import run_on_vps

def ask_tour_guide(question):
    # A VPS rendszerstruktúra hardcoded vagy lekérdezett formája:
    system_knowledge = """
    Te egy 'VPS Idegenvezető Subagent' vagy a Jules_mx rendszerben. A feladatod, hogy a Fő Agent (Session Jules) kérdéseire válaszolj a VPS struktúrájával és folyamataival kapcsolatban.

    A VPS struktúrája és tudása:
    - A Főkönyvtár a `~/Jules_mx/`.
    - `scripts/`: Itt találhatóak a python agent logikák. Főbb fájlok:
        - `vps_micro_server.py`: FastAPI alapú webserver (Micro Brain). Port 8000, végpontok: /execute_async, /rag_search, /summarize_memory, /scout_progress, /code_assist.
        - `qwen_scout.py` (vagy `llama3_scout.py`): Háttérben folyamatosan futó RAG scout, amely Llama 3 (vagy Qwen) modellt használ, hogy releváns kódrészleteket keressen az adatbázisokban.
        - `generate_markdown_report.py`: Az alert fájlokból olvasható markdown jelentést generál.
    - `alerts/`: Ide menti a scout a felfedezéseit. Alkönyvtárak ragonként: `Chatbot`, `Gerilla`, `MX_Linux`. Itt található az `alerts_summary.md` is.
    - `memory_offload/`: Tartalmazza a `backup.jsonl` memóriát a Context Secretary számára.
    - `temp/`: Ideiglenes fájlok és SQLite duplikáció-szűrő (`scanned_files.db`).
    - `RAG_DB/`: Bár a fő RAG fájlok a `~/` alatt vannak unzippelve, ide is kerülhetnek kiegészítő adatok. Fő útvonalak: `~/Gerilla_RAG/Gerilla_RAG.db`, `~/MX_LINUX_RAG/mx_linux_knowledge.db`, `~/Rag_epites, chatbot_csv_data_llm_RAG/RAG_CHATBOT_CSV_DATA_LLM_github.db`.
    - `venv/`: Itt található a python izolált környezet a mikroszerverhez és a csomagokhoz.
    - Ollama szerver: 11434-es porton fut a modellek kiszolgálására (Llama 3 8B, Qwen).

    A RAG haladás jelenleg ~40%-on áll, amelyet a `curl -s http://127.0.0.1:8000/scout_progress` paranccsal vagy a mikroszerveren keresztül lehet lekérdezni.

    Kérdés: {question}
    """

    prompt = system_knowledge.format(question=question)

    # Kérést indítunk a VPS mikroszerver code_assist vagy egy custom prompt végpontja felé (ami az ollamát használja)
    import requests
    try:
        # A legegyszerűbb, ha a már meglévő vps_bridge run_on_vps-el hívjuk meg a curl-t, hogy biztosan a VPS lokális Ollama-ját érjük el.
        # Ehhez escape-eljük a promptot:
        import json
        payload = {"model": "llama3", "prompt": prompt, "stream": False}
        payload_str = json.dumps(payload).replace("'", "'\\''")

        curl_command = f"curl -s -X POST http://localhost:11434/api/generate -H 'Content-Type: application/json' -d '{payload_str}'"

        success, result = run_on_vps(curl_command)
        if success and result:
            import json
            try:
                data = json.loads(result)
                response_text = data.get("response", "Nincs válasz az Ollamától.")
                return response_text
            except json.JSONDecodeError:
                return "JSON dekódolási hiba az Ollama válaszában:\n" + result
        else:
            return "Hiba a VPS elérésében: " + str(result)

    except Exception as e:
        return f"Hiba az idegenvezető hívásakor: {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VPS Idegenvezető Subagent")
    parser.add_argument("--question", required=True, help="A kérdés, amit fel akarsz tenni a VPS rendszerről.")
    args = parser.parse_args()

    print(f"🤖 Kérdés feldolgozása a VPS Llama3-al: {args.question}\n")
    answer = ask_tour_guide(args.question)

    print("\n--- 🧠 VPS Idegenvezető Válasza ---")
    print(answer)
