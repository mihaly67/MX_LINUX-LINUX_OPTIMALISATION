import argparse
import sys
import os
import json
import base64

# A vps_bridge importálása a Fő Agent repójából
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vps_bridge import run_on_vps

# Ezt a scriptet feltöltjük a VPS-re base64-ként, majd ott lefut, hogy ott hívja a lokális Ollamát
# Az "awesome-llm-apps" inspirálta Tool és ToolResult architektúra:
VPS_FRAMEWORK_CODE = """
import json
import urllib.request

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
        data = json.dumps({"model": "llama3", "prompt": prompt, "stream": False}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "Nincs válasz.")
        except Exception as e:
            return f"Hiba az LLM hívásakor: {e}"

    def process_query(self, user_query: str) -> str:
        # A Tanársegéd megkapja az eszközkészletet
        tools_desc = "\\n".join([f"- {name}: {t.description}" for name, t in self.tools.items()])

        system_prompt = f\"\"\"
Te egy Tanársegéd Agent vagy. A rendelkezésedre álló eszközök:
{tools_desc}

A Fő Agent (Jules) kérdése: {user_query}

FONTOS SZABÁLY: Ha a fenti eszközök valamelyikére van szükséged a válaszhoz, NE futtass parancsot, hanem ÍRD LE a következő pontos formátumot a válaszodban:
EXECUTE_TOOL: pontos_eszkoz_neve | ARG: parameterek_ide

Például:
EXECUTE_TOOL: bash_command | ARG: free -h

Ha tudsz válaszolni az eszköz nélkül is, válaszolj közvetlenül.
\"\"\"
        # Első iteráció a LLM-mel
        llm_response = self.call_llm(system_prompt)

        # Tool futtatási logika (ReAct pattern)
        import re
        tool_match = re.search(r"EXECUTE_TOOL:\\s*([\\w_]+)(?:\\s*\\|\\s*ARG:\\s*(.*))?", llm_response)

        if tool_match:
            tool_name = tool_match.group(1)
            tool_arg = tool_match.group(2) if tool_match.group(2) else ""

            if tool_name in self.tools:
                tool = self.tools[tool_name]
                # Ha a tool rag_progress, annak nincs cmd argumentuma
                if tool_name == "rag_progress":
                    res = tool.execute()
                elif tool_arg:
                    res = tool.execute(cmd=tool_arg.strip())
                else:
                    res = tool.execute()

                # Második iteráció az eredménnyel
                followup_prompt = f"{system_prompt}\\n\\nAz eszköz ({tool_name}) eredménye:\\n{res.content}\\n\\nMost fogalmazd meg a végső választ a Fő Agentnek."
                return self.call_llm(followup_prompt)
            else:
                return f"{llm_response}\\n\\n(Hiba: A '{tool_name}' eszköz nem létezik.)"

        return llm_response

# ---- Modul 1: Tool Registry és Bash Command Exec (A Piramiskő) ----
import subprocess

def run_vps_bash_command(cmd: str):
    try:
        # Biztonsági okokból csak olvasási/lekérdezési parancsokat engedünk meg
        if any(bad_word in cmd for bad_word in ["rm -rf", "mkfs", "reboot", "shutdown"]):
            return "Biztonsági tiltás: Veszélyes parancs blokkolva."

        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = res.stdout if res.stdout else res.stderr
        return output[:1500]  # OOM védelem miatt csak az első 1500 karaktert adjuk vissza
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

assistant = TeachingAssistant()
assistant.register_tool(Tool("bash_command", "Futtat egy egyszerű bash/linux parancsot a VPS-en és visszaadja az eredményt (pl. 'ls -l', 'free -h', 'uptime')", run_vps_bash_command))
assistant.register_tool(Tool("rag_progress", "Lekérdezi a jelenlegi RAG feldolgozottsági százalékot", check_rag_progress))

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "Ki vagy te és milyen eszközeid vannak?"
    response = assistant.process_query(query)
    print(response)
"""

def talk_to_assistant(query):
    # Kódoljuk a VPS keretrendszert
    b64_script = base64.b64encode(VPS_FRAMEWORK_CODE.encode('utf-8')).decode('utf-8')
    # Átadjuk a query-t paraméterként
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
