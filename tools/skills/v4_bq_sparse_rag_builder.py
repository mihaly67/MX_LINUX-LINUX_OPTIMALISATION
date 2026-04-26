import sqlite3
import os
import time
import json
import numpy as np
import traceback
from fastembed import TextEmbedding, SparseTextEmbedding

print(f"[{time.strftime('%H:%M:%S')}] 🚀 VPS RAG Építő (v4) - LOW MEMORY MODE indítása...", flush=True)

DENSE_MODEL_NAME = "BAAI/bge-small-en-v1.5"
SPARSE_MODEL_NAME = "prithivida/Splade_PP_en_v1"

# A legfontosabb módosítás: explicit limitáljuk a memóriahasználatot és a CPU szálakat
print(f"[{time.strftime('%H:%M:%S')}] 📦 Modellek betöltése (Korlátozott szálakkal)...", flush=True)
dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME, providers=["CPUExecutionProvider"], threads=1)
sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME, providers=["CPUExecutionProvider"], threads=1)
print(f"[{time.strftime('%H:%M:%S')}] ✅ Modellek betöltve!", flush=True)

def create_target_db(target_conn):
    cursor = target_conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rag_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_repo TEXT,
            filepath TEXT,
            language TEXT,
            file_type TEXT,
            content TEXT,
            chunk_id INTEGER,
            chunk_index INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rag_dense_vectors (
            id INTEGER PRIMARY KEY,
            vector BLOB
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rag_sparse_vectors (
            id INTEGER PRIMARY KEY,
            indices BLOB,
            weight_values BLOB
        )
    ''')
    target_conn.commit()

def chunk_text(text, max_chars=1000, overlap=100):
    """Kisebb darabokra vágjuk (1000 karakter), hogy csökkentsük a VRAM/RAM terhelést a beágyazásnál."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        start += (max_chars - overlap)
    return chunks

def float_array_to_binary(float_array):
    binary_array = np.packbits(np.where(float_array >= 0, 1, 0))
    return binary_array.tobytes()

def process_database(source_db_path, target_db_path):
    print(f"\n[{time.strftime('%H:%M:%S')}] 📂 Adatbázis feldolgozásának megkezdése: {source_db_path}", flush=True)
    os.makedirs(os.path.dirname(target_db_path), exist_ok=True)

    source_conn = sqlite3.connect(source_db_path)
    target_conn = sqlite3.connect(target_db_path)
    create_target_db(target_conn)

    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()

    # Megszámoljuk az összes sort
    source_cursor.execute("SELECT COUNT(*) FROM rag_data")
    total_rows = source_cursor.fetchone()[0]
    print(f"[{time.strftime('%H:%M:%S')}] 📊 Összes rekord: {total_rows}", flush=True)

    start_time = time.time()
    processed_chunks = 0

    # LOW MEMORY: Nem töltjük be a teljes adatbázist a memóriába (fetchall), hanem darabonként kérjük le (fetchmany)
    source_cursor.execute("SELECT id, source_repo, filepath, language, file_type, content FROM rag_data")

    idx = 0
    while True:
        rows = source_cursor.fetchmany(10) # Csak 10 rekordot tartunk egyszerre a memóriában!
        if not rows:
            break

        for row in rows:
            orig_id, source_repo, filepath, language, file_type, content = row
            if not content:
                idx += 1
                continue

            chunks = chunk_text(content)
            if not chunks:
                idx += 1
                continue

            # Batch méret csökkentése a generálásnál: paraméter a modellben
            try:
                # Kicsi batch_size = 2 -> Garantáltan alacsony RAM használat
                dense_embeddings = list(dense_model.embed(chunks, batch_size=2))
                sparse_embeddings = list(sparse_model.embed(chunks, batch_size=2))
            except Exception as e:
                print(f"⚠️ Hiba beágyazás generálásakor ({filepath}): {e}", flush=True)
                idx += 1
                continue

            for chunk_idx, (chunk_text_data, dense_emb, sparse_emb) in enumerate(zip(chunks, dense_embeddings, sparse_embeddings)):
                try:
                    binarized_vector = float_array_to_binary(dense_emb)
                    sparse_indices = sparse_emb.indices.tolist()
                    sparse_values = sparse_emb.values.tolist()

                    target_cursor.execute('''
                        INSERT INTO rag_data (source_repo, filepath, language, file_type, content, chunk_id, chunk_index)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (source_repo, filepath, language, file_type, chunk_text_data, orig_id, chunk_idx))

                    new_id = target_cursor.lastrowid

                    target_cursor.execute('''
                        INSERT INTO rag_dense_vectors (id, vector)
                        VALUES (?, ?)
                    ''', (new_id, binarized_vector))

                    target_cursor.execute('''
                        INSERT INTO rag_sparse_vectors (id, indices, weight_values)
                        VALUES (?, ?, ?)
                    ''', (new_id, json.dumps(sparse_indices), json.dumps(sparse_values)))

                    processed_chunks += 1
                except Exception as e:
                    print(f"⚠️ Hiba beszúráskor ({filepath}, chunk {chunk_idx}): {e}", flush=True)
                    continue

            idx += 1
            if idx % 10 == 0:
                target_conn.commit()
                print(f"[{time.strftime('%H:%M:%S')}] ⏳ {idx}/{total_rows} dokumentum feldolgozva... (Darabok: {processed_chunks})", flush=True)

    target_conn.commit()
    source_conn.close()
    target_conn.close()

    print(f"✅ {source_db_path} feldolgozva! Vektorizált darabok: {processed_chunks}. Idő: {time.time() - start_time:.1f} másodperc.", flush=True)

if __name__ == "__main__":
    GERILLA_SOURCE = "/home/misi/Gerilla_RAG/Gerilla_RAG.db"
    GERILLA_TARGET = "/home/misi/Gerilla_RAG/v4_bq_sparse/gerilla_v4.db"

    print(f"[{time.strftime('%H:%M:%S')}] 🚦 V4 BQ & Sparse RAG építő indítása...", flush=True)
    if os.path.exists(GERILLA_SOURCE):
        process_database(GERILLA_SOURCE, GERILLA_TARGET)
    else:
        print(f"❌ Forrás adatbázis nem található: {GERILLA_SOURCE}")

    print(f"[{time.strftime('%H:%M:%S')}] 🎉 Kész!", flush=True)
