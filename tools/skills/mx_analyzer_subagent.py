# Autonomous Subagent Skill: Restoration Codebase Architect
# Az Ördög Ügyvédje Protokoll alapján: ez a script végigmegy a
# mx_linux_knowledge.db adatbázison, kigyűjti a fontos
# repókat (GFPGAN, BasicSR, CodeFormer, VapourSynth), és
# KIZÁRÓLAG AZ ARCHITEKTURÁLIS VÁZAT (Osztályok, Fő Metódusok, Importok)
# menti le egy JSONL fájlba.
# Így OOM nélkül, tisztán látja a LLM, hogy "hogyan kell megépíteni egy restaurálót".

import sqlite3
import os
import re
import json
import argparse
import sys

def parse_python_architecture(content: str):
    """RegEx alapú, memóriakímélő architektúra kivonó (Parser)."""
    architecture = {
        "imports": [],
        "classes": {},
        "functions": []
    }

    current_class = None

    for line in content.splitlines():
        line = line.strip()

        # 1. Importok (Csak a legfontosabb AI/CV könyvtárak érdekelnek)
        if line.startswith("import ") or line.startswith("from "):
            if any(k in line for k in ["torch", "cv2", "numpy", "vapoursynth", "basicsr", "mmcv"]):
                architecture["imports"].append(line)

        # 2. Osztályok
        class_match = re.match(r"^class\s+([A-Za-z0-9_]+)[\(:]", line)
        if class_match:
            current_class = class_match.group(1)
            architecture["classes"][current_class] = []

        # 3. Osztály metódusai (Kritikusak: __init__, forward)
        if current_class and line.startswith("def "):
            method_match = re.match(r"^def\s+([A-Za-z0-9_]+)\s*(\(.*\))", line)
            if method_match:
                m_name = method_match.group(1)
                m_args = method_match.group(2)
                # Csak az infrastruktúrát építő metódusokat tartjuk meg
                if m_name in ["__init__", "forward", "process", "enhance", "run"]:
                    architecture["classes"][current_class].append(f"{m_name}{m_args}")

        # 4. Globális Főfüggvények
        elif not current_class and line.startswith("def "):
            func_match = re.match(r"^def\s+([A-Za-z0-9_]+)\s*(\(.*\))", line)
            if func_match:
                 architecture["functions"].append(f"{func_match.group(1)}{func_match.group(2)}")

    return architecture

def run_restoration_analysis():
    print("🤖 [Restoration Architect Subagent] Mélyfúrás és Kód Kivonatolás Indítása...")

    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Knowledge_Base", "RAG_DB", "mx_linux_knowledge.db")
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Skill", "Utils maps")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "mx_linux_signatures_full.txt")

    if not os.path.exists(db_path):
        print(f"❌ Hiba: Nem találom a RAG adatbázist: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT source_repo, filepath, content FROM rag_data WHERE filepath LIKE '%.py' OR filepath LIKE '%.sh' OR filepath LIKE '%.bash'"

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Hiba az SQL lekérdezésben: {e}")
        conn.close()
        return

    print(f"📂 {len(rows)} forrásfájl feldolgozása a teljes adatbázisból...")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("# 🧩 MX LINUX SZIGNATÚRA TÉRKÉP (Mélyfúrás test nélkül)\n\n")

    extracted_count = 0

    with open(out_file, "a", encoding="utf-8") as f:
        for repo, filepath, content in sorted(rows, key=lambda x: (x[0], x[1])):
            if not content: continue

            # Kinyerjük az architekturális vázat
            arch = parse_python_architecture(content)

            # Csak akkor mentjük, ha találtunk valami érdemlegeset (osztályt vagy AI importot)
            if arch["classes"] or arch["functions"] or arch["imports"]:
                f.write(f"📜 {repo}/{filepath}\n")
                for cls_name, methods in arch.get("classes", {}).items():
                    f.write(f"    Class: {cls_name}\n")
                    for method in methods:
                        f.write(f"      Method/Func: {method}\n")
                for func in arch.get("functions", []):
                    f.write(f"    Func: {func}\n")
                f.write("\n")
                extracted_count += 1

    conn.close()
    print(f"✅ [Restoration Architect Subagent] Kész! {extracted_count} fájl Architektúrája kimentve ide: {out_file}")

    # Hívjuk meg a Memória Menedzsert, hogy a Fő Agent tudjon róla!
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from ENVIRONMENT_SETUP.agent_memory_manager import write_memory
    write_memory("Subagent_Report", f"Az mx_analyzer_subagent.py kigyűjtötte a teljes MX LINUX RAG architekturális vázát a Skill/Utils maps/mx_linux_signatures_full.txt fájlba.")

if __name__ == "__main__":
    run_restoration_analysis()
