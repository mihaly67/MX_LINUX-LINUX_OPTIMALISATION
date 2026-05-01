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

def main():
    """Futtatja a szervert stdio módban."""
    print("🚀 Jules VPS MCP Szerver elindítva (stdio módban).", file=sys.stderr)
    mcp.run()

if __name__ == "__main__":
    main()
