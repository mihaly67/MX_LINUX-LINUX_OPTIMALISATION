import os
import json
import time
import sqlite3

ALERTS_DIR = os.path.expanduser("~/Jules_mx/alerts")
OUTPUT_MD = os.path.expanduser("~/Jules_mx/alerts/alerts_summary.md")
SCANNED_DB = os.path.expanduser("~/Jules_mx/temp/scanned_files.db")

DB_PATHS = {
    "Gerilla": os.path.expanduser("~/Gerilla_RAG/Gerilla_RAG.db"),
    "Chatbot": os.path.expanduser("~/Rag_epites, chatbot_csv_data_llm_RAG/RAG_CHATBOT_CSV_DATA_LLM_github.db"),
    "MX_Linux": os.path.expanduser("~/MX_LINUX_RAG/mx_linux_knowledge.db")
}

def get_scanned_files():
    if not os.path.exists(SCANNED_DB):
        return set()
    try:
        conn = sqlite3.connect(SCANNED_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT filepath FROM scanned")
        files = {row[0] for row in cursor.fetchall()}
        conn.close()
        return files
    except Exception:
        return set()

def calculate_progress():
    scanned = get_scanned_files()
    progress_stats = {}

    for rag_name, db_path in DB_PATHS.items():
        if not os.path.exists(db_path):
            progress_stats[rag_name] = {"total": 0, "scanned": 0, "percent": 0.0}
            continue

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT filepath FROM rag_data WHERE filepath LIKE '%.py' OR filepath LIKE '%.sh' OR filepath LIKE '%.asm'")
            all_files = {row[0] for row in cursor.fetchall()}
            conn.close()

            total = len(all_files)
            scanned_in_rag = len(all_files.intersection(scanned))
            percent = (scanned_in_rag / total * 100) if total > 0 else 0

            progress_stats[rag_name] = {
                "total": total,
                "scanned": scanned_in_rag,
                "percent": percent
            }
        except Exception:
            progress_stats[rag_name] = {"total": 0, "scanned": 0, "percent": 0.0}

    return progress_stats

def draw_progress_bar(percent, width=30):
    filled = int(width * percent / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"|{bar}| {percent:.1f}%"

def generate_report():
    if not os.path.exists(ALERTS_DIR):
        return

    rag_folders = [f for f in os.listdir(ALERTS_DIR) if os.path.isdir(os.path.join(ALERTS_DIR, f))]
    stats = calculate_progress()

    with open(OUTPUT_MD, "w", encoding="utf-8") as md:
        md.write("# 🤖 Qwen Scout Autonóm RAG Elemzési Jelentés\n\n")
        md.write(f"**Utolsó frissítés:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        md.write("## 📊 Átfogó Feldolgozási Progress\n\n")
        md.write("A Qwen bot folyamatosan szkenneli a RAG adatbázisok tartalmát. Az alábbiak mutatják, hány kód fájlon futott eddig végig:\n\n")

        for rag_name, stat in stats.items():
            if stat["total"] > 0:
                bar = draw_progress_bar(stat["percent"])
                md.write(f"- **{rag_name}**: {stat['scanned']} / {stat['total']} fájl feldolgozva\n")
                md.write(f"  `{bar}`\n\n")

        md.write("---\n\n")

        for rag in rag_folders:
            md.write(f"## 📂 {rag} RAG Találatok\n")
            md.write("---\n\n")

            rag_path = os.path.join(ALERTS_DIR, rag)
            files = [f for f in os.listdir(rag_path) if f.endswith('.json')]

            if not files:
                md.write("*Még nincsenek találatok ebben az adatbázisban.*\n\n")
                continue

            # Rendezzük módosítási idő szerint (legújabb legelöl)
            files.sort(key=lambda x: os.path.getmtime(os.path.join(rag_path, x)), reverse=True)

            for f in files:
                filepath = os.path.join(rag_path, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                        source_file = data.get("file", "Ismeretlen fájl")
                        analysis = data.get("qwen_analysis", "").strip()

                        md.write(f"### 📄 Fájl: `{source_file}`\n")
                        md.write(f"> {analysis}\n\n")
                except Exception as e:
                    pass
            md.write("\n")

if __name__ == "__main__":
    generate_report()
    print(json.dumps(calculate_progress())) # Konzolos visszajelzés
