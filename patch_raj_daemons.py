import os
import glob
import subprocess

script_content = r"""import os
import glob
import re

SWARM_DIR = "/home/misi/Swarm_Agents"
daemon_files = glob.glob(os.path.join(SWARM_DIR, "raj*_daemon.py"))

new_func = '''def ask_ollama(prompt):
    import base64
    import tempfile
    import subprocess

    try:
        print("   [Gemini API] Kérés indítása a felhőbe...", flush=True)
        b64_prompt = base64.b64encode(prompt.encode('utf-8')).decode('utf-8')
        vps_python_script = """\
import base64
from tools.skills.gemini_scout import query_gemini
prompt = base64.b64decode('""" + b64_prompt + """').decode('utf-8')
response = query_gemini(prompt, system_instruction='Te egy elemző AI vagy (rajtag). Elemezd a kódot, és adj vissza hasznos TUI/CLI koncepciókat.')
print(response)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp:
            temp.write(vps_python_script)
            temp_path = temp.name

        result = subprocess.run(["python3", temp_path], capture_output=True, text=True, cwd="/home/misi/Jules_mx")
        os.remove(temp_path)

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Hiba a Gemini scriptben: {result.stderr}"
    except Exception as e:
        return f"Kivétel a Gemini híváskor: {e}"
'''

for file in daemon_files:
    with open(file, "r") as f:
        content = f.read()

    if "ai_response = 'Ezt a feladatot az Agentemnek küldtem" in content:
        content = content.replace(
            "ai_response = 'Ezt a feladatot az Agentemnek küldtem (Rajparancsnok) delegálásra, nem a lokális LLM fogja megválaszolni, hogy kíméljük a CPU-t!' # KIKAPCSOLVA",
            "ai_response = ask_ollama(job['instruction'])"
        )

    if "def ask_ollama(prompt):" in content:
        content = re.sub(r"def ask_ollama\(prompt\):.*?(?=def execute_bash)", new_func + "\n\n", content, flags=re.DOTALL)
        with open(file, "w") as f:
            f.write(content)
        print(f"Javítva: {file}")
"""

with open("temp_vps_patch.py", "w") as f:
    f.write(script_content)

subprocess.run('export VPS_PWD="1104" && sshpass -p "$VPS_PWD" scp -o StrictHostKeyChecking=no temp_vps_patch.py misi@5.189.163.88:/home/misi/Swarm_Agents/', shell=True)
subprocess.run('export VPS_PWD="1104" && python3 tools/skills/mcp_bridge_tool.py --tool execute_bash --args \'{"command": "python3 /home/misi/Swarm_Agents/temp_vps_patch.py"}\'', shell=True)
