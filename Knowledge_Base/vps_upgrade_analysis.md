# Ördög Ügyvédje: VPS Upgrade és Logolási Stratégia

## 1. Logolás: Ömlesztett vs. Strukturált
A felhasználó jogosan tette szóvá, hogy a `master_alerts.log`-ba ömlesztve kerül a Gerilla, a Skills és az MX Linux RAG minden találata.
- **Probléma:** Átláthatatlan, nehéz szűrni.
- **Megoldás:** A `vps_alerter.py`-t át kell írni úgy, hogy az alerts mappába érkező JSON fájlokban található "database_source" vagy "repo_name" alapján különálló log fájlokba (pl. `alerts_gerilla.log`, `alerts_skills.log`) írja az eredményeket.

## 2. VPS Bővítési Csomagok Értékelése
A jelenlegi szerver: 4 CPU Core, ~8GB RAM (Rendszeresen 98% körüli memóriafoglalás Ollama és RAG miatt).
A felkínált opciók:
1. `Cloud VPS 20 SSD`: 6 cores, 12 GB RAM, €11.37/mo
2. `Cloud VPS 30 SSD`: 8 cores, 24 GB RAM, €22.67/mo

**Elemzés:**
- A **12 GB RAM-os csomag** elegendő lenne a jelenlegi Qwen2.5:1.5b modell és egy stabil FastEmbed RAG futtatásához OOM hibák nélkül.
- A **24 GB RAM-os csomag** viszont egy **kategóriaváltást** jelentene! 24 GB RAM-mal már futtathatunk nagyobb modelleket (pl. Llama 3 8B vagy Qwen 7B), amiknek a kódolási és következtetési (reasoning) képessége nagyságrendekkel jobb, mint az 1.5B-s modellé. Emellett 8 maggal a RAG vektorizálás, az Ollama, és egy esetleges Mester-Szolga dispatcher *párhuzamosan*, kompromisszumok (taskset) nélkül futhatna.

**Javaslat a felhasználónak:** Ha komolyan gondoljuk a Mester-Szolga autonóm kódolást a VPS-en (VPS Coder), mindenképpen a **Cloud VPS 30 SSD (24 GB, 8 Core)** a nyertes választás. Ha csak a háttér scoutolás a cél, a 12GB is tökéletes.
