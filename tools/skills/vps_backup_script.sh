#!/bin/bash
# Biztonsági mentés készítő script a Jules környezethez

BACKUP_DIR="/home/misi/jules_backups"
mkdir -p "$BACKUP_DIR"

DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/jules_FULL_backup_$DATE.tar.gz"

echo "⏳ TELJES Biztonsági mentés indítása: $BACKUP_FILE"

# Mentjük a Jules_mx mappát (kihagyva a hatalmas python venv-t, de minden mást igen),
# ÉS belevesszük a RAG adatbázis fájlokat is a többi mappából!
# Mivel a RAG mappákban lehetnek gigabájtos nyers repo kódok, CSAK A LÉNYEGET (db, index, jsonl) és a Jules_mx-et mentjük.

# Ideiglenes fájllista készítése
find /home/misi/Gerilla_RAG /home/misi/Rag_epites,\ chatbot_csv_data_llm_RAG /home/misi/MX_LINUX_RAG /home/misi/BRAIN2_DEV_RAG -type f \( -name "*.db" -o -name "*.index" -o -name "*.jsonl" \) > /tmp/jules_backup_files.txt

# Hozzáadjuk a Jules_mx mappát és a service-eket
echo "/home/misi/Jules_mx/" >> /tmp/jules_backup_files.txt
echo "/etc/systemd/system/jules-mcp.service" >> /tmp/jules_backup_files.txt
echo "/etc/systemd/system/jules-scout.service" >> /tmp/jules_backup_files.txt

# Tömörítés indítása
tar -czvf "$BACKUP_FILE" --exclude="/home/misi/Jules_mx/venv" -T /tmp/jules_backup_files.txt 2>/dev/null

echo "✅ TELJES Biztonsági mentés KÉSZ! Fájl mérete:"
ls -lh "$BACKUP_FILE"
