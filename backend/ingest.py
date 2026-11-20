import sys
import json
import time
from pathlib import Path

# Add backend directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings
from app.db.supabase_client import db
from app.services.pdf_extractor import pdf_extractor
from app.services.chunker import chunker
from app.services.embeddings import embedding_service

def ingest_all_brochures(save_cache: bool = True):
    print("=" * 70)
    print("AUTOMOTIVE AI ASSISTANT: BROCHURE INGESTION & VECTOR INDEXING")
    print("=" * 70)

    supabase_client = db.client
    if not db.is_connected or supabase_client is None:
        raise RuntimeError(
            "Supabase is not connected. Check backend/.env and run backend/schema.sql before ingestion; "
            "no brochures were written to the local fallback."
        )

    brochures_dir = settings.BROCHURES_DIR
    pdf_files = sorted(list(brochures_dir.glob("*.pdf")))
    print(f"\nDiscovered {len(pdf_files)} brochures in {brochures_dir}:")
    for f in pdf_files:
        print(f"  • {f.name} ({f.stat().st_size / (1024*1024):.2f} MB)")

    if not pdf_files:
        print("ERROR: No brochures found. Please add PDF brochures into the brochures folder.")
        return

    total_chunks_indexed = 0
    start_time = time.time()
    existing_indexed_filenames = {
        row["filename"]
        for row in (supabase_client.table("documents").select("filename,status").execute().data or [])
        if row.get("status") == "indexed"
    }

    all_indexed_chunks = []
    all_indexed_vehicles = []

    for idx, pdf_path in enumerate(pdf_files, start=1):
        if pdf_path.name in existing_indexed_filenames:
            print(f"\n[{idx}/{len(pdf_files)}] Skipping '{pdf_path.name}' (already indexed in Supabase).")
            continue
        print(f"\n[{idx}/{len(pdf_files)}] Ingesting '{pdf_path.name}'...")
        
        # 1. Extract text, specs, and pages
        extracted = pdf_extractor.extract_from_file(str(pdf_path))
        brand = extracted.get("brand", "Automotive")
        model = extracted.get("model", "Vehicle")
        page_count = extracted.get("page_count", 0)
        
        print(f"    Recognized Vehicle : {brand} {model}")
        print(f"    Pages Processed    : {page_count} pages")
        
        # 2. Register document in database
        doc_id = db.insert_document(
            filename=pdf_path.name,
            file_path=str(pdf_path),
            file_size=pdf_path.stat().st_size,
            page_count=page_count,
            status="processing"
        )
        
        # 3. Register vehicle entity
        veh_id = db.insert_vehicle(
            brand=brand,
            model=model,
            document_id=doc_id,
            summary=f"Official {brand} {model} technical brochure specifications."
        )
        all_indexed_vehicles.append({
            "id": veh_id,
            "brand": brand,
            "model": model,
            "document_id": doc_id
        })
        
        # 4. Chunk document with metadata
        chunks = chunker.chunk_document(extracted, document_id=doc_id, vehicle_id=veh_id)
        print(f"    Chunks Generated   : {len(chunks)} chunks")
        
        # 5. Embed chunks in batches
        print(f"    Generating embeddings for {len(chunks)} chunks...")
        batch_size = 32
        for b_start in range(0, len(chunks), batch_size):
            b_end = min(b_start + batch_size, len(chunks))
            batch = chunks[b_start:b_end]
            texts = [c["content"] for c in batch]
            embs = embedding_service.get_embeddings_batch(texts)
            for i, emb in enumerate(embs):
                batch[i]["embedding"] = emb
        
        # 6. Insert chunks into DB
        db.insert_chunks(chunks)
        db.update_document_status(doc_id, "indexed")
        existing_indexed_filenames.add(pdf_path.name)
        total_chunks_indexed += len(chunks)
        all_indexed_chunks.extend(chunks)
        print(f"    ✓ Successfully indexed into vector store.")

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"INGESTION COMPLETE: {len(pdf_files)} brochures | {total_chunks_indexed} total chunks in {elapsed:.2f}s")
    print("=" * 70)

    # Persist offline cache so backend starts with warm index
    if save_cache:
        cache_dir = BASE_DIR / "data"
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / "vector_cache.json"
        
        # Save chunks and vehicles (storing float embeddings)
        cache_data = {
            "vehicles": all_indexed_vehicles,
            "documents": db.get_documents(),
            "chunks": all_indexed_chunks
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)
        print(f"Persisted vector cache to: {cache_file} ({cache_file.stat().st_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    ingest_all_brochures()
