import uuid
from typing import Optional

app = FastAPI(title="Jules Swarm Control Center")

SWARM_DB = os.path.expanduser('~/Jules_mx/temp/jules_swarm_jobs.db')

def get_db_connection():
    conn = sqlite3.connect(SWARM_DB)
    return conn

def get_session_id(request: Request):
    return request.cookies.get("session_id")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    session_id = get_session_id(request)
    if not session_id:
        session_id = str(uuid.uuid4())

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT agent_id, last_heartbeat, status, last_error, cpu_usage_percent, mem_usage_mb FROM swarm_health ORDER BY agent_id")
        health_data = cursor.fetchall()
    except Exception as e:
        print(e)
        health_data = []

    try:
        # 1. Fetch the latest 50 messages descending so we get the correct subset
        cursor.execute("SELECT sender, agent_id, message, timestamp FROM chat_messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT 50", (session_id,))
        chat_data = cursor.fetchall()
        # 2. Reverse the list so the oldest of those 50 is at the top, newest at bottom
        chat_data.reverse()
    except Exception as e:
        print(e)
        chat_data = []

    conn.close()

    html = f"""
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Jules Swarm Control Center</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #1e1e2f; color: #c8c8d0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            .card {{ background-color: #2a2a3f; border: none; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
            .card-header {{ background-color: #3b3b55; font-weight: bold; border-bottom: 1px solid #4a4a6a; }}
            .text-success {{ color: #4ade80 !important; }}
            .text-warning {{ color: #facc15 !important; }}
            .text-danger {{ color: #f87171 !important; }}
            pre {{ background-color: #151520; color: #a5b4fc; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            .btn-primary {{ background-color: #6366f1; border: none; }}
            .btn-primary:hover {{ background-color: #4f46e5; }}
            input, select, textarea {{ background-color: #151520 !important; color: white !important; border: 1px solid #4a4a6a !important; }}
            /* Ensure text wraps in chat bubbles */
            .chat-badge {{ white-space: pre-wrap; word-break: break-word; text-align: left; display: inline-block; max-width: 80%; padding: 10px; }}
        </style>
    </head>
    <body>
    <div class="container mt-4">
        <h2 class="mb-4 text-center">🤖 Jules Swarm Control Center</h2>

        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span>Rajtagok Allapota (Health Monitor)</span>
                        <button class="btn btn-sm btn-outline-light" onclick="location.reload()">Frissites</button>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-dark table-hover mb-0">
                                <thead>
                                    <tr>
                                        <th>Agent ID</th>
                                        <th>Statusz</th>
                                        <th>Utolso Eletjel</th>
                                        <th>CPU (%)</th>
                                        <th>RAM (MB)</th>
                                    </tr>
                                </thead>
                                <tbody>
    """

    for agent in health_data:
        status_badge = '<span class="badge bg-success">Aktiv</span>' if agent[2] == 'ALIVE' else '<span class="badge bg-danger">Hiba</span>'
        html += f"""
                                    <tr>
                                        <td><strong>{agent[0]}</strong></td>
                                        <td>{status_badge}</td>
                                        <td>{agent[1]}</td>
                                        <td>{agent[4]}%</td>
                                        <td>{agent[5]} MB</td>
                                    </tr>
        """

    html += """
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span>💬 Jules Chat (Session: {session_id})</span>
                    </div>
                    <div class="card-body">
                        <div class="chat-box mb-3" style="height: 400px; overflow-y: auto; background-color: #151520; padding: 15px; border-radius: 5px; border: 1px solid #4a4a6a; display: flex; flex-direction: column;">
    """

    if not chat_data:
        html += "<div class='text-muted text-center my-auto'>Nincsenek még üzenetek ebben a sessionben.</div>"
    else:
        for chat in chat_data:
            sender, agent, msg, tstamp = chat
            if sender == 'USER':
                html += f"<div class='mb-3 text-end'><small class='text-muted'>{tstamp}</small><br><div class='badge bg-primary fs-6 chat-badge'>{msg}</div></div>"
            else:
                html += f"<div class='mb-3 text-start'><small class='text-muted'>{tstamp} - <strong>{agent}</strong></small><br><div class='badge bg-secondary fs-6 chat-badge'>{msg}</div></div>"

    html += """
                        </div>

                        <form action="/send_message" method="POST">
                            <input type="hidden" name="agent_id" value="Jules_mx">
                            <div class="row align-items-end">
                                <div class="col-md-10">
                                    <textarea class="form-control" name="message" placeholder="Írj üzenetet a Fő Agentnek..." rows="4" style="resize: vertical;" required></textarea>
                                </div>
                                <div class="col-md-2">
                                    <button type="submit" class="btn btn-primary w-100 h-100">Küldés</button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>

    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Scroll to bottom of chat box on load
        document.addEventListener("DOMContentLoaded", function() {
            var chatBox = document.querySelector('.chat-box');
            if (chatBox) {
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        });
    </script>
    </body>
    </html>
    """

    response = HTMLResponse(content=html)
    if not request.cookies.get("session_id"):
        response.set_cookie(key="session_id", value=session_id, max_age=86400*30) # 30 days
    return response

@app.post("/send_message")
async def send_message(request: Request, agent_id: str = Form(...), message: str = Form(...)):
    session_id = get_session_id(request)
    if not session_id:
        return RedirectResponse(url="/", status_code=303)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_messages (session_id, agent_id, sender, message) VALUES (?, ?, 'USER', ?)", (session_id, agent_id, message))

    # Készítünk egy Swarm Job-ot, hogy az ügynök tényleg válaszoljon rá
    instruction = f"CHAT MESSAGE from User (Session: {session_id}): {message}. Please respond to it."
    cursor.execute("INSERT INTO jobs (job_type, target_repo, instruction) VALUES (?, ?, ?)", ("CHAT", agent_id, instruction))

    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

STDERR:
