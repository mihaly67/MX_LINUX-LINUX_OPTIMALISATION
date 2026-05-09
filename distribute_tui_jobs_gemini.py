import sqlite3
import os
import subprocess

repos_and_files = [
    ("aichat-main", "aichat-main/src/repl/mod.rs", "Rust REPL és TUI integráció, chat history és rendering logikák"),
    ("chatbox-main", "chatbox-main/src/renderer/components/message-parts", "React alapú ToolCall és Message history rendering, amit adaptálhatunk CLI-be"),
    ("AutoGPT-master", "AutoGPT-master/classic/original_autogpt/autogpt/app/ui/terminal", "AutoGPT natív terminál UI megvalósítása és aszinkron stream megjelenítése"),
    ("bloop-main", "bloop-main/client/src/components/Chat.tsx", "Bloop chat interfész state management logikája"),
    ("open-webui-main", "open-webui-main/backend/apps/webui/routers/chat.py", "Open-WebUI backend API hívások és kontextus kezelés TUI bekötéshez"),
    ("aider-main", "aider-main/aider/io.py", "Aider terminál Input/Output kezelése, prompt-toolkit használat"),
    ("langchain-master", "langchain-master/libs/cli/langchain_cli/utils/terminal.py", "LangChain CLI és terminál utility-k formázáshoz"),
    ("gemini-cli-main", "gemini-cli-main/src/ui/chat.rs", "Gemini CLI natív terminál chat loopja")
]

def generate_script():
    lines = []
    lines.append("import sqlite3")
    lines.append("import os")
    lines.append("conn = sqlite3.connect(os.path.expanduser('~/Jules_mx/temp/jules_swarm_jobs.db'))")
    lines.append("cursor = conn.cursor()")

    for idx, (repo, filepath, focus) in enumerate(repos_and_files):
        raj_id = f"raj{(idx % 8) + 1}"

        # Olyan utasítást adunk, ami egy python script legenerálását kéri a rajtagtól,
        # amit ő le fog futtatni a geminivel
        instruction = f"python3 /home/misi/Jules_mx/scripts/vps_findings_analyst.py '{filepath}'"

        lines.append(f"cursor.execute(\"INSERT INTO jobs (job_type, target_repo, instruction, status) VALUES (?, ?, ?, ?)\", ('BASH', '{raj_id}', \"{instruction}\", 'PENDING'))")

    lines.append("conn.commit()")
    lines.append("conn.close()")
    lines.append("print('Gemini alapú elemző feladatok kiosztva!')")

    with open("temp_deploy_gemini.py", "w") as f:
        f.write("\n".join(lines))

generate_script()
subprocess.run('export VPS_PWD="1104" && sshpass -p "$VPS_PWD" scp -o StrictHostKeyChecking=no temp_deploy_gemini.py misi@5.189.163.88:/home/misi/Jules_mx/scripts/', shell=True)
subprocess.run('export VPS_PWD="1104" && python3 tools/skills/mcp_bridge_tool.py --tool execute_bash --args \'{"command": "python3 /home/misi/Jules_mx/scripts/temp_deploy_gemini.py"}\'', shell=True)
