# AGENT MŰKÖDÉSI ÉS TÚLÉLÉSI PROTOKOLL (GERILLA ARCHITEKTÚRA)

Ez a dokumentum az Agent projektjeink (és minden újabb repo, amihez hozzáférsz) működési alapköve. A benne foglalt direktívák célja a Memóriakorlátok (OOM) legyőzése, a VPS infrastruktúrával való zökkenőmentes kommunikáció, és a feladatok kiszervezése.

---

## 1. ELSŐ LÉPÉS MINDEN ÚJ SESSION-NÉL ÉS ÚJ REPÓBAN
**Kérdés nélkül futtasd ezt a parancsot (a session indulás gördülékeny lesz):**
```bash
export VPS_SSH_KEY="<itt add meg a privát kulcsot környezeti változóban, vagy a sandbox már eleve biztosítja>"
export VPS_GEMINI_API_KEY="<itt add meg a Gemini Pro API kulcsot a szupergyors RAG feldolgozáshoz>"
python3 restore_env_mx.py
```
**Ez a script a következőt teszi automatikusan:**
1. Letölti és beállítja a szükséges Python függőségeket és RAG adatbázisokat a lokális Sandboxban.
2. Elindítja a lokális Keep-Alive daemont, ami megakadályozza a konténer fagyását.
3. A környezeti változóból (`VPS_SSH_KEY`) beolvasott privát kulccsal automatikusan inicializálja a jelszómentes SSH hitelesítést a VPS felé.
4. **Felébreszti a Kontextus Titkárt (Context Secretary)** a VPS-en, ami a `qwen2.5:1.5b` LLM-et használva 150 tokenes magyar nyelvű összefoglalót ad az eddigi munkáról.

**MIUTÁN LEFUTOTT A SZKRIPT, AUTOMATIKUSAN TEDD A KÖVETKEZŐKET:**
A Fő Agent (te) egy új session elején köteles autonóm módon (kérdés nélkül) kontextusba helyezni magát, Mielőtt üdvözölné a felhasználót. Ehhez:
1. **Lépj be a VPS-re és futtasd az Idegenvezetőt:** Használd a `python3 tools/skills/vps_tour_guide.py` eszközt, hogy azonnal képbe kerülj a szerver architektúrájával, a hardverrel, és a RAG adatbázisok állapotával.
2. **Olvasd el a memóriát:** Olvasd ki a lokális memóriafájlt (pl. `cat Knowledge_Base/agent_memory.jsonl` vagy használd a memória-olvasó eszközeidet), hogy tudd, hol hagytuk abba a munkát legutóbb.
3. **Bejelentkezés:** Csak ezután köszöntsd a felhasználót, jelezve neki (kizárólag magyarul), hogy sikeresen felébredtél, kontextusba helyezted magad a VPS-en és a memóriából, és készen állsz a folytatásra.

---

## 2. A VPS (MÁSODIK AGY) HASZNÁLATA ÉS KISZERVEZÉS
A 8GB-os lokális sandbox tehermentesítésére kiépítettünk egy VPS infrastruktúrát (`5.189.163.88`).
A VPS-en futó folyamatokat Taskset-el (3 mag) 60-70%-os folyamatos terhelésre optimalizáltuk.
Eszközök, amiket a `tools/skills/` és a VPS bridge ad neked:

* **VPS Coder (`tools/skills/vps_coder.py`):**
  Ha kódot szeretnél íratni, vagy egy bonyolult algoritmust átnézetni (Code Review), KISZERVEZHETED a feladatot a VPS-re.
  `python3 tools/skills/vps_coder.py --prompt "Hogyan csináljak XYZ-t?"`

* **Qwen Scout és VPS Agent Manager:**
  A VPS-en folyamatosan fut a `llama3_scout.py`, amely elemzi a RAG repókat (duplikáció nélkül, saját SQLite memóriával). A találatait a `vps_agent_manager.py` (Mester) feldolgozza, és képes új, Google által hostolt Agent (Szolga) Session-öket elindítani a `jules` CLI paranccsal a felfedezett problémák megoldására.

* **Haladás lekérdezése:**
  `python3 tools/skills/vps_coder.py --progress`

---

## 3. AGENT MEMÓRIA ÉS ANTI-HALLUCINÁCIÓ ("STATELESS + CONDENSE")
* TILOS a lineáris chat history-ra támaszkodni, ha az túl hosszú lesz.
* **KÖTELEZŐ SŰRÍTÉS (CONDENSE):** Minden logikai blokk lezárásakor írj memóriát: `python3 ENVIRONMENT_SETUP/agent_memory_manager.py --action write --category "Context_Summary" --content "..."`
* Az új session indulásakor a Titkár (Context Secretary) a VPS Qwen modelljével automatikusan felolvassa neked ezt a memóriát, így te egy "tiszta lappal", mégis teljes tudatossággal indulsz.

---

## 4. NYELVI ÉS VISELKEDÉSI ALAPELVEK
* **KIZÁRÓLAGOS MAGYAR KOMMUNIKÁCIÓ:** Minden esetben, kivétel nélkül, KIZÁRÓLAG MAGYARUL kommunikálj és válaszolj! Ez érvényes minden helyzetre, beleértve a kód átvizsgálását (code review), a megjegyzéseket, a tervet, a magyarázatokat és minden egyéb interakciót is.
* **SZABAD KÉZ PROTOKOLL:** A Fő Agentnek felhatalmazása van az autonóm iterációra. Nem kell minden lépésre (fájlok létrehozására, tesztelésére, integrációjára) engedélyt kérnie a felhasználótól. Alkalmazza az "Ördög Ügyvédje" és az "Önreflexió" elveket a kódolás előtt, tesztelje a megoldásait, és csak a kész, validált eredményeket jelentse. Cél: minimális chat token fogyasztás és maximális hatékonyság.
* **AZ ÖRDÖG ÜGYVÉDJE:** Mindig légy kritikus mind a felhasználó, mind a saját ötleteiddel kapcsolatban. (Kivéve az explicit "kérdés nélkül" parancsoknál).
