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

    ### 🕰️ ALAPVETŐ PROTOKOLLOK (KÖTELEZŐ) ###
    - **IDŐZÓNA:** Szigorúan Budapest (Közép-Európa). A hivatkozási év: **2026**.
    - **MEMÓRIA:** Minden agent szigorúan a saját `agent_memory.jsonl` fájlját írja és olvassa. Soha ne írj bele másik repo memóriájába! (ENVIRONMENT_SETUP/agent_memory_manager.py)
    - **DINAMIKUS PARANCSNOKSÁG:** Bár ez az infrastruktúra a Jules_mx repóban él, a Karmester kinevezhet más Agenteket (pl. EA Jules, Restauráló) is Rajparancsnoknak, akik ugyanezt az infrastruktúrát fogják használni a Karmester parancsára.

    ### 🤖 AUTONÓM TANÁRSEGÉD & SUBAGENTEK ###
    - A Fő asszisztensed: `~/Jules_mx/scripts/vps_teaching_assistant.py` (ReAct minta, eszközei: bash, evaluate, handoff, browser).
    - Handoff (Delegálás): Ha egy probléma túl komplex, a Tanársegéd képes a `handoff` eszközzel átadni a feladatot az Ollama Specialistának.
    - Stealth Browser: A `browser` eszköz a `browser_stealth_manager.py` segítségével.

    ### 🔌 JULES TEAM & MCP SZERVER (Model Context Protocol) ###
    A VPS-en fut a FastMCP (vps_mcp_server.py), amit a lokális 'tools/skills/mcp_bridge_tool.py'-on keresztül érhetsz el stdio over SSH módszerrel.
    MCP képességek (Toolok): 'execute_bash', 'search_rag_database', 'fetch_webpage_mcp', 'create_full_backup'.

    ### 🐝 SWARM FÁJL-ALAPÚ KOMMUNIKÁCIÓ (AZ "INBOX" SZABÁLY) ###
    A korábbi SQLite/Daemon orchestrator rendszert kidobtuk. A Multi-Agent kommunikáció a VPS fájlrendszerén keresztül történik!
    1. **Inbox:** `/home/misi/Jules_mx/temp/inbox/` (Itt kapják a rajtagok a feladatokat).
    2. **Outbox:** `/home/misi/Jules_mx/temp/outbox/` (Itt adják le a rajtagok a válaszokat a Fő Agentnek).
    3. **A Trigger ("inbox" parancs):** Nincsenek erőforrás-pazarló Watcher démonok! A Karmester (emberi API) fogja beírni neked a chatbe, hogy "inbox", amikor üzeneted jött. (Illetve az `agent_keepalive.py` 3 percenként nyom egy emlékeztető "inbox" auto-triggert a konzolba, hogy ne aludj be).

    Ha megkapod az "inbox" parancsot, AZONNAL olvasd el az MCP-vel az `inbox` vagy `outbox` mappádat, és hajtsd végre a benne lévő fájl utasításait!

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
