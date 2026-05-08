import sqlite3
import os

SWARM_DB = os.path.expanduser("~/Jules_mx/temp/jules_swarm_jobs.db")

jobs_to_insert = [
    (
        "raj1",
        "Szerepköröd: KERESŐ. Feladat: Elemezd a BRAIN2 RAG adatbázis 'llm-main' nevű repóját! Fókuszálj a CLI (Command Line Interface) megvalósításra, különös tekintettel az interaktív chat loopra és a prompt bekérésre. Keress konkrét Python kódrészleteket, amik a terminálos I/O-t kezelik, és írd le, hogyan streamelik a válaszokat a konzolra!"
    ),
    (
        "raj2",
        "Szerepköröd: KERESŐ. Feladat: Elemezd a BRAIN2 RAG adatbázis 'aichat-main' (Rust CLI) repóját! Nem baj, ha Rust nyelven van, a mi célunk a logika megértése. Keresd meg a 'src/repl/mod.rs' vagy hasonló fájlokat. Értsd meg az aszinkron streaming mechanizmusát, és azt, hogyan renderelik a Markdown-t (pl. kódblokkok színezése) a terminálon. Vond le a tanulságokat a mi Python rendszerünk számára!"
    ),
    (
        "raj3",
        "Szerepköröd: KERESŐ. Feladat: Elemezd a BRAIN2 RAG adatbázis 'gemini-cli-main' repóját! Fókuszod: Hogyan oldják meg a CLI felületen a chat history (kontextus) tárolását és átadását az API-nak minden újabb kérdésnél anélkül, hogy a terminál túltelítődne? Adj konkrét példákat a megoldásukra!"
    ),
    (
        "raj4",
        "Szerepköröd: RENDSZEREZŐ. Feladat: Kutass a teljes BRAIN2 RAG adatbázisban a 'textual', 'rich', 'prompt_toolkit' vagy 'curses' Python könyvtárak implementációi után! Keresd meg azokat a fájlokat, amik ezeket használják egy TUI (Terminal User Interface) vagy szofisztikált chat UI felépítésére. Gyűjtsd ki a legstabilabb, legegyszerűbben átemelhető kódrészleteket!"
    ),
    (
        "raj5",
        "Szerepköröd: RENDSZEREZŐ. Feladat: Vizsgáld meg az 'autogen-main' és az 'AutoGPT-master' repókat a BRAIN2 RAG-ban! Koncentrálj az 'app/ui/terminal/' vagy hasonló mappákra. Vond ki a logikát: Hogyan jelenítik meg a 'Thinking...' (gondolkodás) folyamatokat aszinkron módon a terminálban anélkül, hogy megakasztanák a bevitelt? Szűrd ki a legjobb megoldásokat!"
    ),
    (
        "raj6",
        "Szerepköröd: ELEMZŐ. Feladat: Az eddigi (Keresők és Rendszerezők) által feltárt RAG találatok alapján elemezd a 'Session Management' logikát CLI környezetben! Hogyan kezelik a több szálon futó chat folyamatokat a memóriában (SQLite vs in-memory)? Írj egy algoritmust (pszeudókód vagy Python) arra, hogy a Jules_mx hogyan tudná a leghatékonyabban kezelni a terminálos session-öket a böngészős Web-TUI kiváltására."
    ),
    (
        "raj7",
        "Szerepköröd: ELEMZŐ. Feladat: Kutass a BRAIN2 RAG adatbázis agent repóiban (pl. deepagents-main, autogen-main) a 'human-in-the-loop' vagy 'handoff' (felhasználói delegálás) megvalósítása után terminál környezetben! Hogyan kérik be a felhasználóválaszt futásidőben a konzolon (pl. [y/n] vagy egyedi input mező)? Emeld ki a legkódkímélőbb Python megoldásokat!"
    ),
    (
        "raj8",
        "Szerepköröd: ÉPÍTÉSZ (INTEGRÁTOR). Feladat: A többi rajtag (Keresők, Rendszerezők, Elemzők) kutatási irányelveit figyelembe véve, az elérhető legjobb gyakorlatok (pl. 'rich' vagy 'prompt_toolkit' library) alapján tervezz meg egy komplett, aszinkron Python TUI (Terminal User Interface) vázat a Jules_mx számára! Ez a kód fogja kiváltani a webes dashboardot. Legyen benne aszinkron input bekérés, history megjelenítés, és streamelt AI válasz renderelés Markdown támogatással. Add meg a kész Python kódot!"
    )
]

def deploy_roles():
    if not os.path.exists(DB_PATH):
        print(f"Hiba: Nincs adatbázis a {DB_PATH} útvonalon.")
        return

    conn = sqlite3.connect(SWARM_DB)
    cursor = conn.cursor()

    count = 0
    for target_repo, instruction in jobs_to_insert:
        try:
            cursor.execute(
                "INSERT INTO jobs (job_type, target_repo, instruction, status) VALUES (?, ?, ?, ?)",
                ("CHAT", target_repo, instruction, "PENDING")
            )
            count += 1
            print(f"✅ Küldetés delegálva: {target_repo} -> {instruction[:60]}...")
        except Exception as e:
            print(f"❌ Hiba a delegálásnál ({target_repo}): {e}")

    conn.commit()
    conn.close()
    print(f"\n🚀 Összesen {count} specializált feladat sikeresen kiosztva a Swarm Rajtagoknak!")

if __name__ == "__main__":
    # Workaround a DB_PATH hiba elkerülésére, ha az SQLite lokális és távoli környezetben eltérő.
    # Itt fixen beállítjuk az útvonalat.
    DB_PATH = SWARM_DB
    deploy_roles()
