#!/usr/bin/env python3
"""
Jules VPS MCP Szerver (Model Context Protocol)
Ez a szerver a VPS-en (8 mag, 24GB RAM, 800GB SSD) fut, és stdio-n vagy SSE-n keresztül MCP protokollon
kiajánlja a VPS helyi erőforrásait (fájlrendszer, bash futtatás, RAG keresés, Memória Regiszter) a lokális Jules Sandboxnak.

Függőségek: mcp, anyio, sqlite3, requests
Telepítés: pip install mcp
"""
import os
import sys
import json
import sqlite3
import subprocess
import requests
import anyio
from mcp.server.fastmcp import FastMCP

# Létrehozunk egy MCP szervert
mcp = FastMCP("Jules VPS MCP")

# --- ALAPVETŐ RENDSZER ESZKÖZÖK ---

@mcp.tool()
async def execute_bash(command: str) -> str:
    """Futtat egy bash parancsot a VPS-en és visszatér a kimenettel. Használd nagy erőforrásigényű scriptek elindításához."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.expanduser("~/Jules_mx/")
        )
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except subprocess.CalledProcessError as e:
        return f"Hibakód: {e.returncode}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"

@mcp.tool()
async def list_files_mcp(directory: str) -> str:
    """Kilistázza a VPS-en lévő fájlokat egy adott könyvtárban."""
    target_dir = os.path.expanduser(directory)
    if not os.path.exists(target_dir):
        return f"Hiba: A(z) {target_dir} könyvtár nem létezik."
    try:
        files = os.listdir(target_dir)
        return "\n".join(files)
    except Exception as e:
        return f"Hiba olvasáskor: {str(e)}"

@mcp.tool()
async def read_file_mcp(filepath: str) -> str:
    """Beolvassa egy fájl tartalmát a VPS-ről."""
    target_file = os.path.expanduser(filepath)
    if not os.path.exists(target_file):
        return f"Hiba: A fájl nem létezik: {target_file}"
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Hiba beolvasáskor: {str(e)}"


@mcp.tool()
async def git_commit_and_push(repo_path: str, commit_message: str, branch: str = "main") -> str:
    """
    VPS Git Menedzser: Hozzáadja a változásokat, commitol, és pushol egy adott branch-re a VPS-en lévő repóban.
    Kiválóan alkalmas arra, hogy a lokális homokozóból irányítva a VPS autonóm módon elmentse a kódokat a GitHubra.
    """
    target_dir = os.path.expanduser(repo_path)
    if not os.path.exists(target_dir):
        return f"Hiba: A {target_dir} mappa nem létezik."

    try:
        # Git Add
        subprocess.run(["git", "add", "."], cwd=target_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Git Commit (Ha van mit)
        commit_res = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=target_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Git Push
        push_res = subprocess.run(
            ["git", "push", "origin", branch],
            cwd=target_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        return f"Git művelet sikeres.\nCommit:\n{commit_res.stdout}\nPush:\n{push_res.stderr} {push_res.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Git hiba: {e.stderr} {e.stdout}"

@mcp.tool()
async def write_file_mcp(filepath: str, content: str) -> str:
    """Fájl írása vagy felülírása a VPS-en. Használd konfigurációk vagy kódrészletek mentésére a VPS lemezére."""
    target_file = os.path.expanduser(filepath)
    try:
        os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Fájl sikeresen mentve: {target_file}"
    except Exception as e:
        return f"Hiba a fájl írásakor: {e}"


import urllib.request
from bs4 import BeautifulSoup

@mcp.tool()
async def fetch_webpage_mcp(url: str) -> str:
    """
    VPS Web Fetcher: Letölti egy megadott URL tartalmát a VPS-ről (így elrejti a lokális sandbox IP-jét).
    A HTML sallangot eltávolítja, csak a tiszta szöveget adja vissza. Használható dokumentációk olvasására.
    """
    try:
        req = urllib.request.Request(
            url,
            data=None,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'hu-HU,hu;q=0.9,en-US;q=0.8,en;q=0.7'
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')
            # Kiszedjük a felesleget
            for script in soup(["script", "style", "header", "footer", "nav", "aside"]):
                script.decompose()
            text = soup.get_text(separator=' ', strip=True)
            # Tokenkímélés
            if len(text) > 10000:
                text = text[:10000] + "... [TRUNCATED]"
            return text
    except Exception as e:
        return f"Hiba a weboldal letöltésekor: {e}"

# --- RAG ÉS MEMÓRIA (ARCHIVAL & RECALL) ESZKÖZÖK ---



RAG_DATABASES = {
    "Chatbot": os.path.expanduser("~/Rag_epites, chatbot_csv_data_llm_RAG/RAG_CHATBOT_CSV_DATA_LLM_github.db"),
    "BRAIN2": os.path.expanduser("/home/misi/BRAIN2_DEV_RAG/brain2_dev_knowledge.db"),
    "Gerilla": os.path.expanduser("~/Gerilla_RAG/Gerilla_RAG.db"),
    "MX_Linux": os.path.expanduser("~/MX_LINUX_RAG/mx_linux_knowledge.db")
}

@mcp.tool()
async def search_rag_database(rag_name: str, keyword: str, limit: int = 3) -> str:
    """
    RAG Archival Memory kereső.
    A megadott tudásbázisban (Chatbot, BRAIN2, Gerilla, MX_Linux) keres SQL LIKE vagy egzakt illeszkedés alapján.
    A lokális agent ezt használja tudás kinyerésére a VPS gigantikus lemezéről!
    """
    if rag_name not in RAG_DATABASES:
        return f"Hiba: Ismeretlen RAG adatbázis. Elérhetőek: {', '.join(RAG_DATABASES.keys())}"

    db_path = RAG_DATABASES[rag_name]
    if not os.path.exists(db_path):
        return f"Hiba: A(z) {db_path} adatbázis fájl nem található a VPS-en."

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Gyors SQL text search a RAG tartalmában
        query = f"%{keyword}%"
        cursor.execute("SELECT filepath, content FROM rag_data WHERE content LIKE ? LIMIT ?", (query, limit))
        results = cursor.fetchall()
        conn.close()

        if not results:
            return f"Nincs találat a '{keyword}' kulcsszóra a {rag_name} RAG-ban."

        output = f"🔍 {len(results)} találat a {rag_name} RAG-ban a '{keyword}' szóra:\n\n"
        for filepath, content in results:
            # Csak az elejét mutatjuk, hogy ne robbanjon fel az MCP csatorna
            snippet = content[:1500] + ("..." if len(content) > 1500 else "")
            output += f"📄 Fájl: {filepath}\n{snippet}\n"
            output += "-" * 50 + "\n"

        return output
    except Exception as e:
        return f"Adatbázis lekérdezési hiba: {e}"

# --- HIERARCHIKUS MEMÓRIA REGISZTER (CORE MEMORY / CONTEXT) ---

MEMORY_REGISTER_FILE = os.path.expanduser("~/Jules_mx/temp/mcp_memory_register.json")

def init_memory_register():
    if not os.path.exists(MEMORY_REGISTER_FILE):
        with open(MEMORY_REGISTER_FILE, "w", encoding="utf-8") as f:
            json.dump({"Core": {}, "Archival_Pointers": []}, f)

@mcp.tool()
async def read_memory_register() -> str:
    """
    Kiolvassa a VPS-en lévő globális Memória Regisztert.
    Ezt használhatja a lokális Agent a kontextus gyors helyreállítására (Core Memory).
    """
    init_memory_register()
    with open(MEMORY_REGISTER_FILE, "r", encoding="utf-8") as f:
        return f.read()

@mcp.tool()
async def write_memory_register(key: str, value: str) -> str:
    """
    Ír a VPS globális Memória Regiszterébe.
    Hasznos hosszú távú állapotok, feladat-listák (Task Queue) és kontextus mentésére.
    """
    init_memory_register()
    try:
        with open(MEMORY_REGISTER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["Core"][key] = value

        with open(MEMORY_REGISTER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return f"✅ '{key}' sikeresen elmentve a VPS Memória Regiszterbe."
    except Exception as e:
        return f"Hiba a memória mentésekor: {e}"


@mcp.tool()
async def create_full_backup() -> str:
    """Elindítja a VPS-en a teljes biztonsági mentést (Jules_mx + RAG adatbázisok). A folyamat hosszú lehet."""
    try:
        script_path = os.path.expanduser("~/Jules_mx/scripts/vps_backup_script.sh")
        if not os.path.exists(script_path):
            return "Hiba: A backup script nem található a VPS-en."

        result = subprocess.run(
            ["bash", script_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return f"Mentés sikeres:\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Hiba a mentés során: {e.stderr}"

def main():
    """Futtatja a szervert stdio módban."""
    print("🚀 Jules VPS MCP Szerver elindítva (stdio módban).", file=sys.stderr)
    mcp.run()

if __name__ == "__main__":
    main()
