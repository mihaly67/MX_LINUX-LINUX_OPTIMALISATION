import argparse

def ask_tour_guide(question=None):
    # Statikus, azonnali (szinkron) és átfogó válasz, LLM timeout és hiba nélkül!
    # Ez a szöveg a következő Jules Agent számára szolgál majd egyfajta "Rendszer Blueprint"-ként.
    guide_text = """
    =======================================================
    🗺️ ÜDVÖZLÖM A JULES_MX VPS IDEGENVEZETŐ RENDSZERÉBEN! 🗺️
    =======================================================
    Te a Fő Agent (Session Jules) vagy. Azért olvasod ezt, mert egy korábbi session-ből, vagy egy másik Jules testvéredtől
    átvetted az irányítást a Misi nevű felhasználó Contabo Cloud VPS-e (IP: 5.189.163.88) fölött.

    ### 🖥️ A VPS HARDVER ÉS KÖRNYEZET ###
    - CPU: 8 Mag (Ryzen)
    - RAM: 24 GB + 16 GB SWAP (Kiterjesztett Memória, OOM ellen)
    - OS: MX Linux alapok, Ubuntu LTS / Debian kompatibilitás.
    - Fő munkakönyvtár: `~/Jules_mx/`

    ### 🤖 AUTONÓM TANÁRSEGÉD & SUBAGENTEK ###
    - A Fő asszisztensed: `~/Jules_mx/scripts/vps_teaching_assistant.py` (ReAct minta, eszközei: bash, evaluate, handoff, browser).
    - Handoff (Delegálás): Ha egy probléma túl komplex, a Tanársegéd képes a `handoff` (Delegál) eszközzel átadni a feladatot az Ollama Llama 3 8B Specialistának.
    - AI Evaluator: Az `evaluate` eszközzel a Tanársegéd képes más kimeneteket lepontozni (Memary framework logika).
    - Stealth Browser: A `browser` eszköz a `browser_stealth_manager.py` segítségével CDP protokollon fej nélküli (headless) Chromiumot futtat (kikerülve a bot-szűrőket).
    - RAG Elemző: `~/Jules_mx/scripts/vps_findings_analyst.py` (Bash grep + LLM szintézis a OOM ellen).

    ### 📚 RAG (RETRIEVAL-AUGMENTED GENERATION) ADATBÁZISOK ###
    A VPS elsődleges célja az AI frameworkök és kódok RAG feldolgozása. A scoutok (gemini_scout.py, llama3_scout.py) csak forráskódra (.py, .js, .c stb.) szűrnek.
    1. Chatbot RAG: `~/Rag_epites, chatbot_csv_data_llm_RAG/RAG_CHATBOT_CSV_DATA_LLM_github.db` (Befejezve: ~72%)
    2. Gerilla RAG: `~/Gerilla_RAG/Gerilla_RAG.db` (Befejezve: ~23%)
    3. MX_Linux RAG: `~/MX_LINUX_RAG/mx_linux_knowledge.db` (Befejezve: ~2%)

    A találati JSON fájlok a `~/Jules_mx/alerts/{RAG_NEVE}/` könyvtárban gyűlnek.
    A `generate_markdown_report.py` generálja az összesítést az `alerts_summary.md` fájlba.

    ### 🔒 BIZTONSÁG & API ###
    - JWT Hitelesítés: `cognee_jwt_auth.py` a lokális repóban generálja a tokeneket a `VPS_JWT_SECRET` környezeti változó alapján.
    - API Végpontok: A `vps_micro_server.py` a 8000-es porton fut, és olyan végpontokat ad, mint `/execute_async`, `/rag_search`, `/code_assist`.
    - Ollama API: 11434-es port.
    - Biztonságos SSH: Az SSH kulcs beállítása a lokális `restore_env_mx.py` futtatásával történik, ami a `VPS_SSH_KEY` változót használja.

    ### 💡 KÖVETKEZŐ LÉPÉS EGY ÚJ JULES SZÁMÁRA ###
    Mivel a Chatbot RAG 72%-nál jár és rengeteg komplex frameworkot (Memary, OpenViking, Mem0) fedezett fel,
    a te feladatod az, hogy ezekből a JSON fájlokból származó rekurzív/iteratív és kontextus-kezelő logikákat
    beépítsd a Fő Agent (Jules) lokális képességei (skills) közé, vagy továbbfejleszd a VPS Tanársegédet!

    =======================================================
    """

    if question:
        return guide_text + f"\n\nA specifikus kérdésedre ('{question}') adott válasz: Olvasd át a fenti System Blueprint-et. Ez egy statikus idegenvezető. Interaktív kérdésekhez használd a vps_teaching_assistant.py-t!"
    return guide_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VPS Idegenvezető Subagent (Statikus, gyors Blueprint)")
    parser.add_argument("--question", required=False, help="A kérdés, amit fel akarsz tenni a VPS rendszerről.")
    args = parser.parse_args()

    print("\n--- 🧠 VPS Idegenvezető Válasza ---")
    print(ask_tour_guide(args.question))
