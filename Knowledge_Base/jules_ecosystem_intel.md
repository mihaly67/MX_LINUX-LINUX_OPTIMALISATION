# Jules Ökoszisztéma Felderítési Jelentés

A RAG adatbázis (`RAG_CHATBOT_CSV_DATA_LLM_github.db`) lekérdezésével kinyertem a Google Jules AI ügynök különböző komponenseire vonatkozó legfontosabb információkat. Az alábbiakban a három fő repository (`jules-sdk`, `jules-skills`, `jules-action`) tudásbázisának összegzése olvasható:

## 1. Jules Action (`jules-action`)
**Leírás**: Egy GitHub Action, amellyel a Jules (egy távoli, Google Labs által fejlesztett, Gemini 3 Pro alapú AI kódoló ügynök) automatikusan meghívható különböző GitHub események (issues, PR-ok, cron scedule-ok) hatására.
**Képességek**:
- Autonóm módon képes a kódbázis elemzésére, hibajavításokra, teljesítményoptimalizálásra, majd ezekről Pull Requesteket készít.
- Biztonsági scannelések: Keresi a hardcode-olt jelszavakat, XSS/SQL Injection sérülékenységeket, és automatikus javítást végez.
- Telepítés: `uses: google-labs-code/jules-invoke@v1` a GitHub workflow YAML-ben.
- Szükséges kulcs: `JULES_API_KEY` (titkosított változóként megadva).

## 2. Jules SDK (`jules-sdk`)
**Leírás**: Egy fejlesztői környezet, amellyel a Jules AI képességei integrálhatók különböző Node.js/TypeScript alkalmazásokba.
**Képességek / Eszközök (MCP Tools)**:
- **`get_session_state`**: Ellenőrzi a Jules munkamenet státuszát (pl. `busy`, `stable`, `failed`), az utolsó aktivitásokat és a függőben lévő terveket (pending plans), amiket a felhasználónak jóvá kell hagynia.
- **`query_cache`**: A sessionök és aktivitások lokális gyorsítótárból történő lekérdezése (gyors, de potenciálisan nem naprakész adatok).
- Az SDK lehetővé teszi egyedi CLI-k, Express szerverek, és GitHub Action-ök fejlesztését.

## 3. Jules Skills (`jules-skills`)
**Leírás**: Egy "Agent Skills" nyílt szabványt követő könyvtár a Jules SDK-hoz. Olyan kódoló ágensekkel kompatibilis, mint a Cursor, a Claude Code vagy a Gemini CLI.
**Képességek**:
- Automatikus issue osztályozás (triage): Elemzi a nyitott hibajegyeket, megtervezi az implementációs lépéseket, majd párhuzamosan indít Jules ágenseket a javításukra (pl. a `automate-github-issues` skill).
- Architektúra: Minden skill egy `SKILL.md` ("Mission Control") fájlból, szkriptekből, erőforrásokból (tudásbázis) és asse-tekből áll, amik az AI ágens "few-shot" tanulását segítik.

---
**Következtetés a további OOM-safe automatizációhoz**:
A `jules-action` használatával automatizált workflow-kat építhetünk a VPS szerveren úgy, hogy az I/O intenzív és bonyolult elemzéseket kiszervezzük a Google infrastruktúrájára (Jules API), így kímélve a mi 8GB-os limitált szerverünket. Az SDK-n keresztül fejlesztett eszközök (pl. `get_session_state`) aszinkron módon lekérdezhetik a munkafolyamatot, fenntartva az ügynök OOM-safe "Stateless + Condense" architekturális követelményeit.
