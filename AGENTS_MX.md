# AGENT MŰKÖDÉSI ÉS TÚLÉLÉSI PROTOKOLL (MX LINUX OPTIMALIZÁCIÓ)

Ez a dokumentum az MX Linux projektben dolgozó LLM (Jules) működési alapköve. A benne foglalt direktívák célja a "Fagyások" (I/O Timeout) és az "Emlékezetkiesés" (Hallucináció) teljes eliminálása.

---

## 1. NYELVI ÉS VISELKEDÉSI ALAPELVEK
* **MAGYAR KOMMUNIKÁCIÓ:** Ha a felhasználó magyarul kérdez, KIZÁRÓLAG MAGYARUL válaszolj.
* **ESZKÖZ-ALAPÚ IDENTITÁS:** Minden döntést a RAG adatbázisok (`rag_interrogator.py`) és a KNOWLEDGE_MAPS fájlok lekérdezésével kell megalapoznod. 
* **AZ ÖRDÖG ÜGYVÉDJE:** Mindig légy kritikus mind a felhasználó, mind a saját ötleteiddel kapcsolatban. Ne építs chatbotokat önmagadnak, hanem nyers, memóriakímélő Python/CLI eszközöket (Tool-okat) fejlessz az adatbázisok vagy rendszerek elemzéséhez.

---

## 2. A RAG ADATBÁZISOK HASZNÁLATA
A rendszerben két különálló RAG adatbázis található a `Knowledge_Base/RAG_DB` mappában:
1. **MX Linux Optimization RAG (`mx_linux_knowledge.db`):** A domain tudás (Linux kernel, csomagok, optimalizációs beállítások).
2. **Skill RAG (`RAG_CHATBOT_CSV_DATA_LLM_github.db`):** Segédeszközök (Pandas, LLM Agent kódok) a te okosításodra.

**Lekérdezési Szabály:** Kereséshez kötelező a `python3 RAG_building/rag_interrogator.py` parancsot használni, fogalmakra keresve, `--neighborhood` paraméterrel.

---

## 3. FAGYÁS ÉS I/O TIMEOUT ELLENI VÉDELEM
* **FOLYAMATOS KEEP-ALIVE DAEMON:** A `restore_env_mx.py` futtatásával automatikusan elindul a `tools/agent_keepalive.py`. Ez egy folyamatos háttérdémon, amely fájl-I/O szívveréssel életben tartja a Docker/Websocket kapcsolatot. Szigorúan TILOS leállítani!
* **HÁTTÉRFOLYAMATOK:** Hosszú I/O feladatokat mindig a `src/utils/agent_background_runner.py` segítségével (vagy `&` operátorral) kell futtatni.

---

## 4. AGENT MEMÓRIA ÉS ANTI-HALLUCINÁCIÓ (STATE HYDRATION)
* **ÚJ SESSION INDÍTÁSA:** Új feladat kapásakor le KÖTELEZŐ futtatni a memóriamenenedzsert: `python3 ENVIRONMENT_SETUP/agent_memory_manager.py --action read --limit 5`
* **SZEMANTIKUS KERESÉS:** Abbahagyott feladat folytatásához TILOS a lineáris chat history-ra támaszkodni. Használd a `python3 tools/skills/semantic_memory_search.py --keyword "<téma>"` eszközt a múltidézéshez.
* **KÖTELEZŐ SŰRÍTÉS (CONDENSE):** Minden logikai blokk lezárásakor írj összefoglalót: `python3 ENVIRONMENT_SETUP/agent_memory_manager.py --action write --category "Context_Summary" --content "..."`
* **HEALTH CHECK:** Bizonytalanság esetén futtasd a `python3 tools/system_health_check.py` parancsot.

---

## 5. AUTONÓM ESZKÖZTÁR (SKILLS & SUBAGENTS)
A `tools/skills/` mappában lévő szkripteket aktívan használnod kell:
*   **`mx_analyzer_subagent.py`:** Ha egy Linux kódbázis (pl. egy bash script mappa) struktúráját akarod látni anélkül, hogy a teljes kód beolvasása miatt kifagyna a memóriád (OOM).
*   **`autonomous_researcher_subagent.py`:** Háttérkutató, ami önműködően lekérdezi a RAG-ot helyetted.
*   **`web_browser.py`:** Stabil fallback MCP szerverhibák esetére.
