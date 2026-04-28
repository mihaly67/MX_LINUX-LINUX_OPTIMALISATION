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
        if "memóri" in lower_query or "read_memory" in lower_query:
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

        if tool_name:
            # Ha felismertük a toolt, le is futtatjuk azonnal
            tool = self.tools.get(tool_name)
            if tool:
                if tool_name in ["rag_progress", "read_memory"]:
                    res = tool.execute()
                elif tool_name in ["search_rag_knowledge", "ask_tour_guide"]:
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
        safe_query = query.replace('"', '').replace("'", "")
        ALERTS_DIR = '/home/misi/Jules_mx/alerts/Chatbot'

        vps_python_script = f\"\"\"
import os, json
results = []
count = 0
for root, _, files in os.walk('{ALERTS_DIR}'):
    for file in files:
        if file.endswith('.json'):
            try:
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    if '{safe_query}' in content.lower():
                        data = json.loads(content)
                        analysis = data.get("llama3_analysis", data.get("qwen_analysis", ""))
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
            lines = f.readlines()[-5:] # Csak az utolsó 5 bejegyzést olvassuk fel

        import json
        memory_text = ""
        for line in lines:
            try:
                data = json.loads(line)
                memory_text += f"[{data.get('category', 'Log')}] {data.get('content', '')}\\n"
            except:
                memory_text += line

        return memory_text
    except Exception as e:
        return f"Hiba a memória olvasása során: {e}"

# ---- Modul 5: VPS Idegenvezető (Tour Guide Wrapper) ----
def ask_tour_guide(query: str):
    return "A Főkönyvtár a ~/Jules_mx/. Főbb fájlok a scripts mappában: vps_micro_server.py, qwen_scout.py (rag adatbányász). Alerts: Chatbot, Gerilla, MX_Linux mappák json fájlokkal. RAG adatbázisok a ~/ alatt. Micro szerver port: 8000. Ollama port: 11434."

assistant = TeachingAssistant()
assistant.register_tool(Tool("bash_command", "Futtat egy egyszerű bash/linux parancsot a VPS-en (pl. 'ls -l', 'free -h')", run_vps_bash_command))
assistant.register_tool(Tool("rag_progress", "Lekérdezi a jelenlegi RAG feldolgozottsági százalékot", check_rag_progress))
assistant.register_tool(Tool("search_rag_knowledge", "Keres a Chatbot RAG json találataiban. Paramétere a keresőszó.", search_rag_knowledge))
assistant.register_tool(Tool("read_memory", "Kihozza a Fő Agent legutóbbi történéseit a VPS memóriából.", read_vps_memory))
assistant.register_tool(Tool("ask_tour_guide", "Kérdéseket válaszol meg a VPS felépítésével (fájlokkal, portokkal, processzekkel) kapcsolatban. Paramétere a kérdés.", ask_tour_guide))

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "Ki vagy te és milyen eszközeid vannak?"
    response = assistant.process_query(query)
    print(response)
"""

def talk_to_assistant(query):
    b64_script = base64.b64encode(VPS_FRAMEWORK_CODE.encode('utf-8')).decode('utf-8')
    safe_query = query.replace('"', '\\"').replace("'", "\\'")
    cmd = f"python3 -c \"import base64; import sys; sys.argv=['', '{safe_query}']; exec(base64.b64decode('{b64_script}').decode('utf-8'))\""

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
