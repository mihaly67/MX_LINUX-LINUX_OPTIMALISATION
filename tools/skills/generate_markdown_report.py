import os
import json
import time

ALERTS_DIR = os.path.expanduser("~/Jules_mx/alerts")
OUTPUT_MD = os.path.expanduser("~/Jules_mx/alerts/alerts_summary.md")

def generate_report():
    if not os.path.exists(ALERTS_DIR):
        return

    rag_folders = [f for f in os.listdir(ALERTS_DIR) if os.path.isdir(os.path.join(ALERTS_DIR, f))]

    with open(OUTPUT_MD, "w", encoding="utf-8") as md:
        md.write("# 🤖 Qwen Scout Autonóm RAG Elemzési Jelentés\n\n")
        md.write(f"**Utolsó frissítés:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        md.write("Ez a dokumentum automatikusan frissül a Qwen Scout által a VPS-en talált legfontosabb kód-leletekkel.\n\n")

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

            for f in files: # Az összeset kigeneráljuk
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
    print("Markdown report generated.")
