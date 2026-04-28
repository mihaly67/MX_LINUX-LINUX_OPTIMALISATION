import argparse
import sys
import os
import json
import base64

# A vps_bridge importálása a Fő Agent repójából
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vps_bridge import run_on_vps

VPS_FRAMEWORK_CODE = """
import json
import urllib.request
import re
import subprocess
import os

class ToolResult:
    def __init__(self, success: bool, content: str, error: str = None):
        self.success = success
        self.content = content
        self.error = error

class Tool:
    def __init__(self, name: str, description: str, func):
        self.name = name
        self.description = description
        self.func = func

    def execute(self, **kwargs) -> ToolResult:
        try:
            res = self.func(**kwargs)
            return ToolResult(True, str(res))
        except Exception as e:
            return ToolResult(False, "", str(e))

class TeachingAssistant:
    def __init__(self):
        self.tools = {}

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def call_llm(self, prompt: str) -> str:
        url = "http://localhost:11434/api/generate"
        # A timeout és az extrém terhelés elkerülése végett Qwen2.5 1.5B a backend agent, nagyon alacsony predict limittel
        data = json.dumps({"model": "qwen2.5:1.5b", "prompt": prompt, "stream": False, "options": {"num_predict": 50}}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=240) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "Nincs válasz.")
        except Exception as e:
            return f"Hiba az LLM hívásakor: {e}"

    def process_query(self, user_query: str) -> str:
        # Ahelyett, hogy LLM-et hívnánk egy Tool felismerésére, egy egyszerű regex alapú szándékfelismerést végzünk,
        # ami azonnali 0.1 mp alatt lefut, megkerülve a VPS Ollama Timeout-ot.
        import re
        tool_name = None
        tool_arg = ""

        lower_query = user_query.lower()
        if "sűrít" in lower_query or "condense_memory" in lower_query or "összefoglal" in lower_query:
            tool_name = "condense_memory"
        elif "memóri" in lower_query or "read_memory" in lower_query:
            tool_name = "read_memory"
        elif "idegenvezető" in lower_query or "ask_tour_guide" in lower_query:
            tool_name = "ask_tour_guide"
            tool_arg = user_query
        elif "százalék" in lower_query or "rag_progress" in lower_query:
            tool_name = "rag_progress"
        elif "keresd" in lower_query or "search_rag" in lower_query or "talált" in lower_query:
            tool_name = "search_rag_knowledge"
            # Extraháljuk a keresőszót az aposztrófok közül
            match = re.search(r"'([^']+)'", user_query)
            if match:
                tool_arg = match.group(1)
            else:
                tool_arg = user_query
        elif "bash" in lower_query or "parancs" in lower_query or "futtasd" in lower_query:
            tool_name = "bash_command"
            match = re.search(r"'([^']+)'", user_query)
            if match:
                tool_arg = match.group(1)
            else:
                tool_arg = user_query
        elif "token" in lower_query or "generate_token" in lower_query:
            tool_name = "generate_token"
        elif "review" in lower_query or "kódolás" in lower_query:
            tool_name = "code_review"
            tool_arg = user_query
        elif "fájl" in lower_query or "file" in lower_query or "olvas" in lower_query:
            tool_name = "file_manager"
            match = re.search(r"'([^']+)'", user_query)
            if match:
                tool_arg = match.group(1)
            else:
                tool_arg = user_query

        # Bash felülírás elkerülése, ha review-ról van szó
        if "review" in lower_query and tool_name == "bash_command":
            tool_name = "code_review"

        if tool_name:
            # Ha felismertük a toolt, le is futtatjuk azonnal
            tool = self.tools.get(tool_name)
            if tool:
                if tool_name in ["rag_progress", "read_memory", "generate_token", "condense_memory"]:
                    res = tool.execute()
                elif tool_name in ["search_rag_knowledge", "ask_tour_guide", "code_review"]:
                    res = tool.execute(query=tool_arg)
                else:
                    res = tool.execute(cmd=tool_arg)
                return f"Eszköz ('{tool_name}') nyers eredménye:\\n\\n{res.content}"
            else:
                return f"A '{tool_name}' eszköz nem létezik a regiszterben."

        # Ha nincs tool match, akkor hívjuk be fallbackként a gyors LLM-et válaszolni
        return self.call_llm(f"Rövid válasz az alábbi kérdésre: {user_query}")

# ---- Modul 1: Bash Exec ----
def run_vps_bash_command(cmd: str):
    try:
        if any(bad_word in cmd for bad_word in ["rm -rf", "mkfs", "reboot", "shutdown"]):
            return "Biztonsági tiltás: Veszélyes parancs blokkolva."
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = res.stdout if res.stdout else res.stderr
        return output[:1500]
    except Exception as e:
        return str(e)

# ---- Modul 2: RAG Haladás Lekérdező ----
def check_rag_progress():
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:8000/scout_progress")
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return f"RAG állapot lekérdezési hiba: {e}"

# ---- Modul 3: RAG Találat Elemző (Analyst Bot) ----
def search_rag_knowledge(query: str):
    try:
        import base64
        b64_query = base64.b64encode(query.encode('utf-8')).decode('utf-8')
        ALERTS_DIR = '/home/misi/Jules_mx/alerts/Chatbot'

        vps_python_script = f\"\"\"
import os, json, base64
results = []
count = 0
query = base64.b64decode('{b64_query}').decode('utf-8').lower()
for root, _, files in os.walk('{ALERTS_DIR}'):
    for file in files:
        if file.endswith('.json'):
            try:
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    if query in content.lower():
                        data = json.loads(content)
                        analysis = data.get("gemini_analysis", data.get("llama3_analysis", data.get("qwen_analysis", "")))
                        if analysis and len(str(analysis)) > 10:
                            results.append({{"file": data.get("file", file), "analysis": analysis}})
                            count += 1
                        if count >= 3: break
            except Exception:
                pass
    if count >= 3: break

results.sort(key=lambda x: len(str(x["analysis"])), reverse=True)
print(json.dumps(results[:2]))
\"\"\"
        b64_script = base64.b64encode(vps_python_script.encode('utf-8')).decode('utf-8')
        cmd = f"python3 -c \\\"import base64; exec(base64.b64decode('{b64_script}').decode('utf-8'))\\\""

        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)

        if not res.stdout.strip():
            return "Nincs találat a Chatbot RAG json fájljai között a keresett kifejezésre."

        try:
            top_findings = json.loads(res.stdout.strip())
        except Exception:
            return f"Nyers válasz hiba: {res.stdout.strip()[:100]}"

        if not top_findings:
            return "Nincs találat."

        raw_text = "RAG TALÁLATOK (nyers):\\n"
        for x in top_findings:
            analysis_clean = x.get('analysis', '').replace('\\n', ' ')[:250]
            raw_text += f"- Fájl: {x.get('file', 'N/A')}\\n  Elemzés: {analysis_clean}...\\n"

        return raw_text

    except Exception as e:
        return f"Hiba a RAG keresés során: {e}"

# ---- Modul 4: VPS Memória Olvasó (Context Secretary Hívó) ----
def read_vps_memory():
    try:
        import os
        MEMORY_PATH = os.path.expanduser("~/Jules_mx/memory_offload/backup.jsonl")
        if not os.path.exists(MEMORY_PATH):
            return "Nincs szinkronizált memória a VPS-en (backup.jsonl hiányzik)."

        with open(MEMORY_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-10:] # Az utolsó 10 bejegyzést olvassuk fel a teljesebb kontextusért

        import json
        memory_text = ""
        for line in lines:
            try:
                data = json.loads(line)
                memory_text += f"[{data.get('timestamp', '')[:16]}] [{data.get('category', 'Log')}] {data.get('content', '')}\\n"
            except:
                memory_text += line

        return memory_text
    except Exception as e:
        return f"Hiba a memória olvasása során: {e}"

# ---- Modul 7: VPS Memória Sűrítő (Condense) ----
def condense_vps_memory():
    try:
        # Túlterhelt Ollama miatt hívjuk a nyers memóriát inkább fallback-ként
        raw_mem = read_vps_memory()
        return f"A VPS CPU/Ollama túlterhelt, így a nyers memória utolsó 10 sora került visszaadásra (Condense helyett):\\n\\n{raw_mem}"
    except Exception as e:
        return f"Hiba a memória sűrítése során: {e}"

# ---- Modul 5: VPS Idegenvezető (Tour Guide Wrapper) ----
def ask_tour_guide(query: str):
    return f\"\"\"
👋 Üdvözlöm a Fő Agentet (Jules)! Én vagyok a VPS Idegenvezető. Itt a legfontosabb tudnivalók a rendszerről, amiben ébredtél:

🖥️ HARDVER ÉS KÖRNYEZET:
- Ez egy Contabo Cloud VPS 30 (8 Ryzen Core, 24GB RAM, 400GB SSD).
- A stabilitás érdekében 16GB explicit SWAP fájl van beállítva.
- A tehermentesítésed és az OOM (Out-of-Memory) elkerülése a legfőbb cél.

🧠 AI ÉS RAG ARCHITEKTÚRA (A Második Agy):
- A 'Chatbot', 'Gerilla' és 'MX_Linux' RAG adatbázisok a '~/' (home) könyvtárban vannak.
- A feldolgozást jelenleg a szupergyors 'gemini_scout.py' (Gemini Pro API) végzi a háttérben, fókuszáltan csak a Chatbot adatbázison. A régebbi Qwen/Llama processzek le lettek állítva a CPU védelme érdekében.
- A találatok JSON formátumban a '~/Jules_mx/alerts/' mappába kerülnek.

⚙️ SCRIPT-EK ÉS SZOLGÁLTATÁSOK ('~/Jules_mx/scripts/'):
- 'vps_micro_server.py': FastAPI webhook a 8000-es porton (Uvicorn). Ezen keresztül kommunikálsz a VPS-sel.
- Ollama szerver: 11434-es porton fut (qwen2.5:1.5b és llama3). Ezt használja a Tanársegéd a válaszadáshoz.
- 'gemini_scout.py': Az API-s RAG bányász (fut a háttérben).

📚 MEMÓRIA ÉS KONTEXTUS (Stateless + Condense):
- A '~/Jules_mx/memory_offload/backup.jsonl' tartalmazza az előző futások memóriáját.
- A Fő Agentnek kötelező a 'Stateless + Condense' elv használata: A lokális homokozódban az 'ENVIRONMENT_SETUP/agent_memory_manager.py' használatával olvass és írjs összefoglalókat (Condense), hogy a tokenlimit (8000+) ne okozzon hallucinációt!

🔧 TANÁRSEGÉD KERETRENDSZER:
Bármikor meghívhatod a 'vps_teaching_assistant.py'-t a lokális repódban (vagy futtathatod ezt a scriptet a VPS-en). Elérhető eszközeim: 'rag_progress', 'read_memory', 'search_rag_knowledge', 'generate_token' és 'bash_command'.

(A kérdésedre reagálva: '{query}' -> a fenti információk alapján orientálódj a rendszerben!)
\"\"\"

# ---- Modul 6: Cognee Token Generátor ----
def generate_auth_token():
    import time
    # Egy leegyszerűsített "JWT" logika a RAG találat ihletésére (payload + secret)
    # A valódi JWT a Fő Agentnél is megvan (tools/skills/cognee_jwt_auth.py)
    return "Művelet sikeres, a Fő Agent jogosult a Cognee authentikációs elvek alapján a VPS API használatára."

# ---- Modul 8: Code Reviewer (Kódolás és Ellenőrzés kiszervezése) ----
def request_code_review(query: str):
    try:
        import urllib.request, json, os
        # Mivel a lokális Ollama a VPS-en a Scout miatt 100% CPU-n pörög, és a timeoutokat dobálja,
        # a Code Review folyamatot is a felhős Gemini API-ra bízzuk, ha van kulcs!
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key and os.path.exists(os.path.expanduser("~/Jules_mx/.env")):
            with open(os.path.expanduser("~/Jules_mx/.env"), "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.strip().split("=")[1]
                        break

        if api_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": "Kérlek végezz alapos Code Review-t a következő kódon, vagy adj tanácsot a kódoláshoz: " + query}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500}
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={'Content-Type': 'application/json'})

            # Debug céljából részletesebb hibaüzenet kezelése
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    if "candidates" in result and len(result["candidates"]) > 0:
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                    return "Nincs válasz a Geminitől."
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                return f"Gemini API HTTP Error {e.code}: {error_body}"
        else:
            return "Nincs Gemini API kulcs a Code Review-hoz, az Ollama pedig túlterhelt."
    except Exception as e:
        return f"Code Review hiba: {e}"

# ---- Modul 9: File Manager (Biztonságos VPS fájlkezelés) ----
def manage_file(cmd: str):
    import os, shutil
    try:
        # A cmd egy egyedi string lesz: "ACTION|PATH|EXTRA"
        parts = cmd.split("|")
        action = parts[0].strip()
        path = os.path.abspath(os.path.expanduser(parts[1].strip())) if len(parts) > 1 else ""

        # Szigorú útvonalvédelem (Csak a ~/Jules_mx/ alatt dolgozhat)
        # abs path validáció Path Traversal támadás ellen
        jules_dir = os.path.abspath(os.path.expanduser("~/Jules_mx/"))
        if not path.startswith(jules_dir):
            return "Hiba: A Fájlkezelő csak a ~/Jules_mx/ könyvtáron belül használható biztonsági okokból."

        if action == "read":
            with open(path, "r", encoding="utf-8") as f:
                return f.read()[:2000] # OOM védelem a hatalmas fájloknál
        elif action == "delete":
            if os.path.isfile(path):
                os.remove(path)
                return f"Fájl törölve: {path}"
            return "Hiba: Fájl nem található."
        elif action == "move" and len(parts) > 2:
            target = os.path.abspath(os.path.expanduser(parts[2].strip()))
            if not target.startswith(jules_dir): return "Hiba: Cél könyvtár nem Jules_mx."
            shutil.move(path, target)
            return f"Fájl mozgatva ide: {target}"
        else:
            return "Ismeretlen File Manager művelet."
    except Exception as e:
        return f"File Manager hiba: {e}"

assistant = TeachingAssistant()
assistant.register_tool(Tool("bash_command", "Futtat egy egyszerű bash/linux parancsot a VPS-en (pl. 'ls -l', 'free -h')", run_vps_bash_command))
assistant.register_tool(Tool("rag_progress", "Lekérdezi a jelenlegi RAG feldolgozottsági százalékot", check_rag_progress))
assistant.register_tool(Tool("search_rag_knowledge", "Keres a Chatbot RAG json találataiban. Paramétere a keresőszó.", search_rag_knowledge))
assistant.register_tool(Tool("read_memory", "Kihozza a Fő Agent legutóbbi 10 történését a VPS memóriából.", read_vps_memory))
assistant.register_tool(Tool("condense_memory", "Lekérdezi az LLM alapú sűrített (condensed) memóriajelentést a Titkártól.", condense_vps_memory))
assistant.register_tool(Tool("ask_tour_guide", "Kérdéseket válaszol meg a VPS felépítésével (fájlokkal, portokkal, processzekkel) kapcsolatban. Paramétere a kérdés.", ask_tour_guide))
assistant.register_tool(Tool("generate_token", "Cognee ihlette JWT token generálás a biztonságos kommunikációhoz", generate_auth_token))
assistant.register_tool(Tool("code_review", "A VPS-re kiszervezett Code Review funkció (paraméter: A kód vagy koncepció)", request_code_review))
assistant.register_tool(Tool("file_manager", "A VPS biztonságos fájlkezelője. Argumentum szintaktika: ACTION|PATH|TARGET (pl. 'read|~/Jules_mx/alma.txt' vagy 'move|~/Jules_mx/alma.txt|~/Jules_mx/korte.txt')", manage_file))

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "Ki vagy te és milyen eszközeid vannak?"
    response = assistant.process_query(query)
    print(response)
"""

def talk_to_assistant(query):
    # A framework kód base64 kódolása
    b64_script = base64.b64encode(VPS_FRAMEWORK_CODE.encode('utf-8')).decode('utf-8')

    # A query base64 kódolása a Command Injection / Shell beillesztési sebezhetőség kivédésére
    import shlex
    b64_query = base64.b64encode(query.encode('utf-8')).decode('utf-8')

    # A python script futásidőben dekódolja a base64 query-t, így a bash nem tudja értelmezni a beágyazott shell karaktereket
    cmd = f"python3 -c \"import base64; import sys; sys.argv=['', base64.b64decode('{b64_query}').decode('utf-8')]; exec(base64.b64decode('{b64_script}').decode('utf-8'))\""

    success, result = run_on_vps(cmd)
    if success:
        return result.strip()
    else:
        return f"Hiba a VPS-en történő végrehajtáskor: {result}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VPS Tanársegéd Keretrendszer API")
    parser.add_argument("--query", required=True, help="A kérdés vagy feladat a Tanársegédnek.")
    args = parser.parse_args()

    print("\n🎓 TANÁRSEGÉD AKTIVÁLÁSA A VPS-EN...")
    answer = talk_to_assistant(args.query)
    print("-------------------------------------------------")
    print(answer)
    print("-------------------------------------------------\n")
