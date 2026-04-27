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
        # A timeout és az extrém terhelés elkerülése végett Qwen2.5 1.5B a backend agent.
        data = json.dumps({"model": "qwen2.5:1.5b", "prompt": prompt, "stream": False, "options": {"num_predict": 250}}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=300) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "Nincs válasz.")
        except Exception as e:
            return f"Hiba az LLM hívásakor: {e}"

    def process_query(self, user_query: str) -> str:
        tools_desc = "\\n".join([f"- {name}: {t.description}" for name, t in self.tools.items()])

        system_prompt = f\"\"\"
Te egy Tanársegéd Agent vagy. A rendelkezésedre álló eszközök:
{tools_desc}

A Fő Agent (Jules) kérdése: {user_query}

FONTOS SZABÁLY: Ha a fenti eszközök valamelyikére van szükséged a pontos válaszhoz (például RAG százalék, memória, fájlrendszer), NE tippelj, hanem használd a Toolt! ÍRD LE EZZEL A FORMÁTUMMAL A GENERÁLÁSBAN:
EXECUTE_TOOL: pontos_eszkoz_neve | ARG: parameterek_ide

Például:
EXECUTE_TOOL: rag_progress | ARG: none
\"\"\"
        llm_response = self.call_llm(system_prompt)

        tool_match = re.search(r"EXECUTE_TOOL:\\s*([\\w_]+)(?:\\s*\\|\\s*ARG:\\s*(.*))?", llm_response)

        if tool_match:
            tool_name = tool_match.group(1)
            tool_arg = tool_match.group(2).strip() if tool_match.group(2) else ""

            if tool_name in self.tools:
                tool = self.tools[tool_name]
                if tool_name == "rag_progress":
                    res = tool.execute()
                elif tool_name == "search_rag_knowledge":
                    res = tool.execute(query=tool_arg)
                elif tool_arg:
                    res = tool.execute(cmd=tool_arg)
                else:
                    res = tool.execute()

                # Mivel az LLM timeoutol az ismételt hívásnál a terhelt rendszeren,
                # egyenesen visszaadjuk a formázott tool eredményt LLM szintézis nélkül
                return f"Eszköz ('{tool_name}') nyers eredménye:\\n\\n{res.content}"
            else:
                return f"{llm_response}\\n\\n(Hiba: A '{tool_name}' eszköz nem létezik.)"

        return llm_response

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

assistant = TeachingAssistant()
assistant.register_tool(Tool("bash_command", "Futtat egy egyszerű bash/linux parancsot a VPS-en (pl. 'ls -l', 'free -h')", run_vps_bash_command))
assistant.register_tool(Tool("rag_progress", "Lekérdezi a jelenlegi RAG feldolgozottsági százalékot", check_rag_progress))
assistant.register_tool(Tool("search_rag_knowledge", "Keres a Chatbot RAG json találataiban. Paramétere a keresőszó.", search_rag_knowledge))

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
