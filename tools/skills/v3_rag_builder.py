import sqlite3
import os
import time
import uuid
import sys

def get_script_dir():
    return os.path.dirname(os.path.abspath(__file__))

def chunk_text(text, max_length=1500):
    """Szó alapú darabolás kb. max_length hosszúságú szövegekre (FastEmbed BGE 512 token limit)."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_len = 0
    for word in words:
        if current_len + len(word) > max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_len = len(word)
        else:
            current_chunk.append(word)
            current_len += len(word) + 1
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def process_database(source_db_path, target_db_path, embedding_model):
    print(f"\n[{time.strftime('%H:%M:%S')}] 📂 Adatbázis feldolgozásának megkezdése: {source_db_path}", flush=True)

    os.makedirs(os.path.dirname(target_db_path), exist_ok=True)

    target_conn = sqlite3.connect(target_db_path)
    target_cursor = target_conn.cursor()
    target_cursor.execute("""
        CREATE TABLE IF NOT EXISTS rag_data_v2 (
            id TEXT PRIMARY KEY,
            source_repo TEXT,
            filepath TEXT,
            content TEXT,
            embedding BLOB
        )
    """)
    target_conn.commit()

    source_conn = sqlite3.connect(source_db_path)
    source_cursor = source_conn.cursor()

    try:
        source_cursor.execute("SELECT count(*) FROM rag_data WHERE file_type IN ('Code', 'Documentation')")
        total_files = source_cursor.fetchone()[0]
    except Exception as e:
         print(f"❌ Hiba a {source_db_path} olvasásakor: {e}", flush=True)
         return

    print(f"📦 Összesen {total_files} fájl (Code/Doc) vár vektorizálásra.", flush=True)

    # BATCH processing az OOM elkerülésére (500 fájlonként)
    # Tovább csökkentve 250-re a 8GB RAM stabilitása miatt
    batch_size = 250
    offset = 0
    processed_chunks = 0
    start_time = time.time()

    while True:
        source_cursor.execute(f"SELECT source_repo, filepath, content FROM rag_data WHERE file_type IN ('Code', 'Documentation') LIMIT {batch_size} OFFSET {offset}")
        rows = source_cursor.fetchall()

        if not rows:
            break

        print(f"[{time.strftime('%H:%M:%S')}] Feldolgozás alatt: fájlok {offset} - {offset + len(rows)} / {total_files}", flush=True)

        all_chunks = []
        chunk_metadata = []

        for repo, filepath, content in rows:
            if not content: continue

            chunks = chunk_text(content)
            for chunk in chunks:
                all_chunks.append(chunk)
                chunk_metadata.append((repo, filepath, chunk))

        if all_chunks:
            # FastEmbed Batch generálás
            embeddings = list(embedding_model.embed(all_chunks))

            # Mentés adatbázisba
            target_data = []
            for i in range(len(all_chunks)):
                doc_id = str(uuid.uuid4())
                repo, filepath, chunk = chunk_metadata[i]
                emb_blob = embeddings[i].tobytes()
                target_data.append((doc_id, repo, filepath, chunk, emb_blob))

            target_cursor.executemany(
                "INSERT INTO rag_data_v2 (id, source_repo, filepath, content, embedding) VALUES (?, ?, ?, ?, ?)",
                target_data
            )
            target_conn.commit()
            processed_chunks += len(all_chunks)

            print(f"   ⏳ {processed_chunks} chunk vektorizálva és elmentve...", flush=True)

        offset += batch_size

    source_conn.close()
    target_conn.close()
    print(f"✅ {source_db_path} feldolgozva! Vektorizált darabok: {processed_chunks}. Idő: {time.time() - start_time:.1f} másodperc.", flush=True)

def main():
    print("=================================================================", flush=True)
    print("🚀 UNIVERZÁLIS FASTEMBED RAG BUILDER V3 (OOM SAFE) 🚀", flush=True)
    print("=================================================================", flush=True)

    # A HÁROM KÜLÖNÁLLÓ ADATBÁZIS! Nem egyesítjük őket, mindegyiknek saját target db-je van!
    DATABASES = [
        {
            "source": os.path.expanduser("~/Rag_epites, chatbot_csv_data_llm_RAG/RAG_CHATBOT_CSV_DATA_LLM_github.db"),
            "target": os.path.expanduser("~/Rag_epites, chatbot_csv_data_llm_RAG/v2_fastembed/skills_v2.db")
        },
        {
            "source": os.path.expanduser("~/Gerilla_RAG/Gerilla_RAG.db"),
            "target": os.path.expanduser("~/Gerilla_RAG/v2_fastembed/gerilla_v2.db")
        },
        {
            "source": os.path.expanduser("~/MX_LINUX_RAG/mx_linux_knowledge.db"),
            "target": os.path.expanduser("~/MX_LINUX_RAG/v2_fastembed/mx_linux_v2.db")
        }
    ]

    print(f"[{time.strftime('%H:%M:%S')}] FastEmbed Modell betöltése a memóriába (BAAI/bge-small-en-v1.5) ...", flush=True)
    from fastembed import TextEmbedding

    # Az előző futás 93% RAM-ot evett meg. Le kell vennünk a szálakat 2-re, hogy a VPS túlélje!
    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", threads=2)
    print("✅ Modell betöltve.", flush=True)

    overall_start = time.time()

    for db in DATABASES:
        if os.path.exists(db["source"]):
            process_database(db["source"], db["target"], model)
        else:
            print(f"⚠️ KIVÉTEL: Forrás DB nem található: {db['source']}", flush=True)

    print("\n=================================================================", flush=True)
    print(f"🎉 MINDEN RAG ADATBÁZIS ÚJRAÉPÍTVE! Összes eltelt idő: {(time.time() - overall_start)/60:.1f} perc.", flush=True)
    print("=================================================================", flush=True)

if __name__ == "__main__":
    main()
