from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import os
import uvicorn
import uuid
from typing import Optional
from datetime import datetime

app = FastAPI(title="Jules Swarm Control Center (Web-TUI)")

SWARM_DB = os.path.expanduser('~/Jules_mx/temp/jules_swarm_jobs.db')

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
                 (id INTEGER PRIMARY KEY, job_type TEXT, target_repo TEXT, instruction TEXT, status TEXT DEFAULT 'PENDING', assigned_to TEXT, result TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db_if_needed()

def get_session_id(request: Request):
    return request.cookies.get("session_id")

@app.get("/chat_history", response_class=JSONResponse)
async def get_chat_history(request: Request, last_count: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM chat_messages")
        current_count = cursor.fetchone()[0]
    except Exception as e:
        current_count = 0

    is_thinking = False
    status_text = ""
    try:
        cursor.execute("SELECT status, job_type FROM jobs WHERE target_repo = 'Jules_mx' AND (status = 'PENDING' OR status = 'IN_PROGRESS') LIMIT 1")
        active_job = cursor.fetchone()
        if active_job:
            is_thinking = True
            status_text = f"{active_job[1]} ({active_job[0]})"
    except Exception as e:
        pass

    # Ha a szam megegyezik a kliensevel, nem kuldjuk el a teljes HTML-t, csak a statuszt
    if current_count == last_count and current_count != 0:
        conn.close()
        return {"html": None, "is_thinking": is_thinking, "status_text": status_text, "msg_count": current_count}

    try:
        cursor.execute("SELECT sender, agent_id, message, timestamp FROM chat_messages ORDER BY timestamp DESC LIMIT 50")
        chat_data = cursor.fetchall()
        chat_data.reverse()
    except Exception as e:
        chat_data = []

    conn.close()

    if not chat_data:
        html = "<div class='text-muted text-center my-auto'>Jules_mx üresjáratban. Várakozás parancsra...</div>"
    else:
        html = ""
        for row in chat_data:
            sender = row[0]
            msg = row[2]
            try:
                dt = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S') + timedelta(hours=2)
                ts = dt.strftime('%H:%M:%S')
            except:
                ts = row[3][11:19] if row[3] else ""

            if sender == 'USER':
                html += f"<div class='mb-2 text-start'><span class='text-success fw-bold'>[{ts}] KARMESTER:</span> <span class='text-light'>{msg}</span></div>"
            else:
                html += f"<div class='mb-2 text-start'><span class='text-info fw-bold'>[{ts}] Jules_mx:</span> <span class='text-light'>{msg}</span></div>"

    return {"html": html, "is_thinking": is_thinking, "status_text": status_text, "msg_count": current_count}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    session_id = get_session_id(request)
    if not session_id:
        session_id = str(uuid.uuid4())

    html_part_1 = f"""
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Jules Swarm Control Center (Web TUI)</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #0d1117; color: #c9d1d9; font-family: 'Courier New', Courier, monospace; margin: 0; padding: 10px; height: 100vh; display: flex; flex-direction: column; }}
            .card {{ background-color: #161b22; border: 1px solid #30363d; margin-bottom: 10px; flex-grow: 1; display: flex; flex-direction: column; }}
            .card-header {{ background-color: #21262d; font-weight: bold; border-bottom: 1px solid #30363d; color: #58a6ff; }}
            .text-success {{ color: #3fb950 !important; }}
            .text-info {{ color: #58a6ff !important; }}
            .text-warning {{ color: #d29922 !important; }}
            .text-danger {{ color: #f85149 !important; }}
            .btn-primary {{ background-color: #238636; border: none; color: #ffffff; font-weight: bold; }}
            .btn-primary:hover {{ background-color: #2ea043; }}
            .btn-warning {{ background-color: #d29922; border: none; color: #ffffff; font-weight: bold; margin-left: 5px; }}
            input, select, textarea {{ background-color: #0d1117 !important; color: #c9d1d9 !important; border: 1px solid #30363d !important; font-family: 'Courier New', Courier, monospace; }}
            input:focus, textarea:focus {{ border-color: #58a6ff !important; box-shadow: 0 0 0 0.2rem rgba(88, 166, 255, 0.25) !important; }}
            #chat-content {{
                flex-grow: 1;
                max-height: 50vh !important;
                overflow-y: scroll !important;
                background-color: #0d1117;
                padding: 15px;
                border-radius: 5px;
                border: 1px solid #30363d;
            }}
            #chat-content::-webkit-scrollbar {{ width: 8px; }}
            #chat-content::-webkit-scrollbar-track {{ background: #0d1117; }}
            #chat-content::-webkit-scrollbar-thumb {{ background: #30363d; border-radius: 4px; }}
            #chat-content::-webkit-scrollbar-thumb:hover {{ background: #58a6ff; }}
            .blink {{ animation: blinker 1.5s linear infinite; }}
            @keyframes blinker {{ 50% {{ opacity: 0; }} }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <span>╭─ 💻 Jules_mx Terminal [Session: {session_id[:8]}]</span>
                <span id="status-indicator" class="text-secondary fw-bold">✅ IDLE</span>
            </div>
            <div class="card-body d-flex flex-direction-column" style="flex-direction: column; padding-bottom: 5px;">
                <div id="chat-content" class="mb-3">
                    <div class='text-muted text-center my-auto'>Rendszer indítása...</div>
                </div>
                <form id="chat-form" action="/send_message" method="POST" style="margin-bottom: 0;">
                    <div class="d-flex">
                        <textarea class="form-control me-2" name="message" id="message_input" placeholder="Parancs vagy üzenet... (vagy PUSH gomb)" rows="2" style="resize: vertical; overflow-y: auto;" required></textarea>
                        <div class="d-flex flex-column justify-content-between">
                            <button type="submit" id="send_button" class="btn btn-primary mb-1">KÜLDÉS</button>
                            <button type="button" id="push_button" class="btn btn-warning">GITHUB PUSH</button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    """

    html_part_2 = """
    <script>
        var chatContent = document.getElementById('chat-content');
        var statusIndicator = document.getElementById('status-indicator');
        var isThinking = false;
        var needsScroll = true;
        var lastMsgCount = 0;

        function fetchChat() {
            fetch('/chat_history?last_count=' + lastMsgCount)
                .then(response => response.json())
                .then(data => {
                    if (data.html !== null) {
                        var isAtBottom = (chatContent.scrollHeight - chatContent.scrollTop) <= chatContent.clientHeight + 50;
                        chatContent.innerHTML = data.html;
                        lastMsgCount = data.msg_count;
                        if (isAtBottom || needsScroll) {
                            chatContent.scrollTop = chatContent.scrollHeight;
                            needsScroll = false;
                        }
                    }
                    isThinking = data.is_thinking;
                    if (isThinking) {
                        statusIndicator.innerHTML = '<span class="text-warning blink">⚡ ' + data.status_text + '</span>';
                    } else {
                        statusIndicator.innerHTML = '<span class="text-secondary">✅ IDLE</span>';
                    }
                })
                .catch(error => console.error('Hiba:', error));
        }

        setInterval(fetchChat, 5000);

        document.getElementById('chat-form').addEventListener('submit', function(e) {
            e.preventDefault();
            var messageInput = document.getElementById('message_input');
            var formData = new FormData(this);
            var btn = document.getElementById('send_button');

            btn.disabled = true;
            fetch('/send_message', {
                method: 'POST',
                body: formData
            }).then(() => {
                messageInput.value = '';
                btn.disabled = false;
                needsScroll = true;
                fetchChat();
            }).catch(() => {
                btn.disabled = false;
            });
        });

        document.getElementById('push_button').addEventListener('click', function(e) {
            var btn = this;
            btn.disabled = true;
            var formData = new FormData();
            formData.append('message', '/push');

            // Azonnal megnyitjuk a Github-ot egy új lapon, hogy a Karmester lássa az egyesítést (Merge/Pull Request)
            window.open('https://github.com/mihaly67/Jules_mx', '_blank');

            fetch('/send_message', {
                method: 'POST',
                body: formData
            }).then(() => {
                btn.disabled = false;
                needsScroll = true;
                fetchChat();
            }).catch(() => {
                btn.disabled = false;
            });
        });

        fetchChat();
    </script>
    </body>
    </html>
    """

    response = HTMLResponse(content=html_part_1 + html_part_2)
    if not request.cookies.get("session_id"):
        response.set_cookie(key="session_id", value=session_id, max_age=86400*30)
    return response

@app.post("/send_message")
async def send_message(request: Request, message: str = Form(...)):
    session_id = get_session_id(request)
    if not session_id:
        session_id = 'global'

    conn = get_db_connection()
    cursor = conn.cursor()

    if message.strip().upper() == "/PUSH":
        cursor.execute("INSERT INTO chat_messages (session_id, agent_id, sender, message) VALUES (?, 'Jules_mx', 'USER', ?)", (session_id, "🚀 [RENDSZER PARANCS]: Kérlek végezz el egy Github Commit és Push műveletet a jelenlegi munkádon!"))
        cursor.execute("INSERT INTO jobs (job_type, target_repo, instruction) VALUES (?, ?, ?)", ("GITHUB_PUSH", "Jules_mx", "Készíts egy commitot és töltsd fel a Githubra."))
    else:
        cursor.execute("INSERT INTO chat_messages (session_id, agent_id, sender, message) VALUES (?, 'Jules_mx', 'USER', ?)", (session_id, message))
        cursor.execute("INSERT INTO jobs (job_type, target_repo, instruction) VALUES (?, ?, ?)", ("CHAT", "Jules_mx", message))

    conn.commit()
    conn.close()
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
