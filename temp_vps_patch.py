import os
import glob
import re

SWARM_DIR = "/home/misi/Swarm_Agents"
daemon_files = glob.glob(os.path.join(SWARM_DIR, "raj*_daemon.py"))

for file in daemon_files:
    with open(file, "r") as f:
        content = f.read()

    # Kicseréljük az Ollama hívást és a modellt, hogy LLM hívás nélkül maradjanak,
    # Vagy ha BASH feladat jön (pl. Python Gemini scriptek futtatása), akkor azt egyenesen
    # a bash végrehajtónak adják át.

    if "if 'python3' in job['instruction'] and '.py' in job['instruction']:" in content:
        content = content.replace(
            "if 'python3' in job['instruction'] and '.py' in job['instruction']:",
            "if job['type'] == 'BASH' or ('python3' in job['instruction'] and '.py' in job['instruction']):"
        )
        content = content.replace(
            "output = execute_bash(job['instruction'])",
            "instruction = job['instruction'].replace('BASH: ', '') if job['instruction'].startswith('BASH: ') else job['instruction']\n                    output = execute_bash(instruction)"
        )
        with open(file, "w") as f:
            f.write(content)
        print(f"BASH futtatás engedélyezve: {file}")
