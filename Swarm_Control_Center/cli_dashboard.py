import sqlite3
import os
import time
import uuid
import sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
import threading

SWARM_DB = os.path.expanduser('~/Jules_mx/temp/jules_swarm_jobs.db')

console = Console()
session_id = str(uuid.uuid4())

current_messages = []
is_thinking = False

def get_db_connection():
    try:
        conn = sqlite3.connect(SWARM_DB)
        return conn
    except Exception as e:
        os.makedirs(os.path.dirname(SWARM_DB), exist_ok=True)
        return sqlite3.connect(SWARM_DB)

def init_db_if_needed():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages
                 (id INTEGER PRIMARY KEY, session_id TEXT, sender TEXT, agent_id TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS jobs
                 (id INTEGER PRIMARY KEY, job_type TEXT, target_repo TEXT, payload TEXT, status TEXT, created_at DATETIME, completed_at DATETIME, result TEXT, priority INTEGER)''')
    conn.commit()
    conn.close()

def fetch_messages():
    global current_messages, is_thinking
    conn = get_db_connection()
    c = conn.cursor()

    try:
        c.execute("SELECT sender, message, timestamp FROM chat_messages ORDER BY timestamp ASC")
        current_messages = c.fetchall()
    except Exception as e:
        pass

    try:
        c.execute("SELECT status, job_type FROM jobs WHERE target_repo = 'Jules_mx' AND (status = 'PENDING' OR status = 'IN_PROGRESS') LIMIT 1")
        active_job = c.fetchone()
        if active_job:
            is_thinking = active_job[1]
        else:
            is_thinking = False
    except Exception as e:
        is_thinking = False

    conn.close()

def render_ui():
    """Leképezi a chat history-t és a status bart. Ezt a Live folyamatosan (get_renderable) hívja!"""
    text = Text()
    text.append("JULES SWARM COMMAND CENTER\n", style="bold cyan")
    text.append("=" * 40 + "\n\n")

    if not current_messages:
        text.append("Nincsenek üzenetek.\n", style="dim")
    else:
        for msg in current_messages[-15:]:
            sender, content, ts = msg
            if sender == "USER":
                text.append(f"[{ts[11:19]}] KARMESTER: ", style="bold green")
                text.append(f"{content}\n")
            else:
                text.append(f"[{ts[11:19]}] {sender}: ", style="bold blue")
                text.append(f"{content}\n")

    text.append("\n" + "=" * 40 + "\n")
    if is_thinking:
        text.append(f"🤖 Jules_mx dolgozik... [Státusz: {is_thinking}]", style="bold yellow blink")
    else:
        text.append("✅ Rendszer üresjáratban. Várakozás parancsra.", style="bold dim")

    return Panel(text, title="Terminal UI", border_style="cyan")

def background_poller():
    """Folyamatosan frissíti a háttérben az állapotot. A Live a render_ui callbackel automatikusan kiolvassa."""
    while True:
        fetch_messages()
        time.sleep(1.0)

def send_message(msg: str):
    if msg.strip().upper() == "/PUSH":
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO chat_messages (session_id, sender, agent_id, message) VALUES (?, ?, ?, ?)",
                  (session_id, "USER", "Jules_mx", "🚀 [RENDSZER PARANCS]: Kérlek végezz el egy Github Commit és Push műveletet a jelenlegi munkádon!"))
        c.execute("INSERT INTO jobs (job_type, target_repo, payload, status, created_at, priority) VALUES (?, ?, ?, ?, ?, ?)",
                  ("GITHUB_PUSH", "Jules_mx", "Készíts egy commitot és töltsd fel a Githubra.", "PENDING", datetime.now().isoformat(), 1))
        conn.commit()
        conn.close()
        # Erőszakoljunk ki egy azonnali frissítést
        fetch_messages()
        return

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO chat_messages (session_id, sender, agent_id, message) VALUES (?, ?, ?, ?)",
              (session_id, "USER", "Jules_mx", msg))
    c.execute("INSERT INTO jobs (job_type, target_repo, payload, status, created_at, priority) VALUES (?, ?, ?, ?, ?, ?)",
              ("CHAT", "Jules_mx", msg, "PENDING", datetime.now().isoformat(), 1))
    conn.commit()
    conn.close()

    # Frissítsük azonnal a nézetet
    fetch_messages()

def main():
    init_db_if_needed()

    # A poller azonnal letölti az első képet
    fetch_messages()
    poller = threading.Thread(target=background_poller, daemon=True)
    poller.start()

    session = PromptSession()

    # get_renderable=render_ui az aszinkron, folyamatos frissítéshez!
    with Live(get_renderable=render_ui, refresh_per_second=4, console=console) as live:
        while True:
            # A prompt blokkol, de a háttérszál + a Live get_renderable frissíti az ablakot.
            with patch_stdout():
                try:
                    user_input = session.prompt("\nÜzenet Jules-nek (vagy /push a mentéshez, /exit a kilépéshez): ")
                except (EOFError, KeyboardInterrupt):
                    break

                if user_input.strip().lower() == "/exit":
                    break
                elif user_input.strip():
                    send_message(user_input)

if __name__ == "__main__":
    main()
