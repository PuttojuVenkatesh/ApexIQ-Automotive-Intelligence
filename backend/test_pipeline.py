import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings
from app.db.supabase_client import db
from app.services.pdf_extractor import pdf_extractor
from app.services.chunker import chunker
from app.services.embeddings import embedding_service
from app.services.rag_service import rag_service
from app.services.comparison_service import comparison_service

def run_test():
    print("=" * 60)
    print("AUTOMOTIVE AI ASSISTANT: END-TO-END PIPELINE TEST")
    print("=" * 60)

    brochures_dir = settings.BROCHURES_DIR
    pdf_files = list(brochures_dir.glob("*.pdf"))
    print(f"\n[1] Located {len(pdf_files)} brochures in {brochures_dir}:")
    for f in pdf_files:
        print(f"  - {f.name} ({f.stat().st_size / (1024*1024):.2f} MB)")

    if not pdf_files:
        print("ERROR: No brochures found. Please ensure brochures exist.")
        return

    # Process first two brochures (e.g. Creta and Alcazar) for quick test
    test_files = [f for f in pdf_files if "creta" in f.name.lower() or "alcazar" in f.name.lower()]
    if not test_files:
        test_files = pdf_files[:2]

    print("\n[2] Indexing test brochures into vector store...")
    for pdf_path in test_files:
        print(f"\nProcessing {pdf_path.name}...")
        extracted = pdf_extractor.extract_from_file(str(pdf_path))
        print(f"  Extracted: {extracted['brand']} {extracted['model']} | Pages: {extracted['page_count']}")
        
        doc_id = db.insert_document(
            filename=pdf_path.name,
            file_path=str(pdf_path),
            file_size=pdf_path.stat().st_size,
            page_count=extracted['page_count'],
            status="indexed"
        )
        veh_id = db.insert_vehicle(
            brand=extracted['brand'],
            model=extracted['model'],
            document_id=doc_id
        )
        chunks = chunker.chunk_document(extracted, document_id=doc_id, vehicle_id=veh_id)
        print(f"  Generated {len(chunks)} chunks.")
        
        # Embed and insert chunks
        chunk_texts = [c["content"] for c in chunks]
        embeddings = embedding_service.get_embeddings_batch(chunk_texts)
        for idx, c in enumerate(chunks):
            c["embedding"] = embeddings[idx]
            
        db.insert_chunks(chunks)
        print(f"  Successfully indexed {len(chunks)} chunks into vector store.")

    # 3. Test RAG Query
    print("\n[3] Testing RAG Query with Citations:")
    query = "What are the engine specs and safety features of Hyundai Creta?"
    print(f"Query: '{query}'")
    rag_result = rag_service.query(user_query=query)
    print("\nAnswer:\n", rag_result["answer"])
    print("\nSource Citations:")
    for src in rag_result["sources"]:
        print(f"  * [{src['document']} | Page {src['page']} | {src['section']}] (Score: {src['similarity']})")
        print(f"    Excerpt: {src['excerpt'][:100]}...")

    # 4. Test Car Comparison
    print("\n[4] Testing Side-by-Side Car Comparison:")
    compare_result = comparison_service.compare_cars("Hyundai Alcazar", "Hyundai Creta")
    print(f"Comparison: {compare_result['car_a']} vs {compare_result['car_b']}")
    print("\nComparison Summary:\n", compare_result["summary"])
    print(f"\nCitations Used: {len(compare_result['sources'])} sources.")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
