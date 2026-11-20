import re
import secrets
import time
import uuid
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
from app.db.supabase_client import db
from app.services.chunker import chunker
from app.services.embeddings import embedding_service
from app.services.pdf_extractor import pdf_extractor
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/documents", tags=["Documents"])
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
ADMIN_SESSION_TTL_SECONDS = 8 * 60 * 60
_admin_sessions: Dict[str, float] = {}


class AdminLoginRequest(BaseModel):
    username: str
    password: str


def require_admin(authorization: Optional[str] = Header(default=None)) -> str:
    if not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail="Brochure administration is disabled. Configure ADMIN_USERNAME and ADMIN_PASSWORD on the backend.",
        )
    scheme, separator, token = (authorization or "").partition(" ")
    if not separator or scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="An administrator session is required.")
    expiry = _admin_sessions.get(token)
    if expiry is None or expiry <= time.time():
        _admin_sessions.pop(token, None)
        raise HTTPException(status_code=401, detail="Administrator session is invalid or expired.")
    return token


@router.post("/auth/login")
def login_admin(payload: AdminLoginRequest):
    if not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail="Brochure administration is disabled. Configure ADMIN_USERNAME and ADMIN_PASSWORD on the backend.",
        )
    username_matches = secrets.compare_digest(payload.username, settings.ADMIN_USERNAME)
    password_matches = secrets.compare_digest(payload.password, settings.ADMIN_PASSWORD)
    if not (username_matches and password_matches):
        raise HTTPException(status_code=401, detail="The administrator ID or password is incorrect.")

    now = time.time()
    for token, expiry in list(_admin_sessions.items()):
        if expiry <= now:
            _admin_sessions.pop(token, None)
    access_token = secrets.token_urlsafe(32)
    _admin_sessions[access_token] = now + ADMIN_SESSION_TTL_SECONDS
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ADMIN_SESSION_TTL_SECONDS,
        "username": settings.ADMIN_USERNAME,
    }


@router.post("/auth/logout")
def logout_admin(token: str = Depends(require_admin)):
    _admin_sessions.pop(token, None)
    return {"message": "Administrator signed out."}


def process_pdf_pipeline(file_path: str, doc_id: str):
    """Extract and index a brochure, recording failures for the admin page."""
    try:
        db.update_document_status(doc_id, "processing")
        extracted = pdf_extractor.extract_from_file(file_path)
        vehicle_id = db.insert_vehicle(
            brand=extracted.get("brand", "Unknown"),
            model=extracted.get("model", "Vehicle"),
            document_id=doc_id,
            summary=f"Official {extracted.get('brand', 'Unknown')} {extracted.get('model', 'Vehicle')} brochure.",
        )
        chunks = chunker.chunk_document(extracted, document_id=doc_id, vehicle_id=vehicle_id)
        embeddings = embedding_service.get_embeddings_batch([chunk["content"] for chunk in chunks])
        for index, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[index]
        db.insert_chunks(chunks)
        db.update_document_status(doc_id, "indexed", page_count=extracted["page_count"])
        rag_service.invalidate_cache()
        print(f"[Pipeline] Indexed '{Path(file_path).name}' ({len(chunks)} chunks).")
    except Exception as error:
        print(f"[Pipeline] Failed to process '{Path(file_path).name}': {error}")
        db.update_document_status(doc_id, "failed", error_message=str(error))


@router.post("/upload", dependencies=[Depends(require_admin)])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Validate and save a PDF, then start asynchronous indexing."""
    original_name = file.filename or ""
    filename = Path(original_name.replace("\\", "/")).name
    filename = re.sub(r"[^A-Za-z0-9._ -]", "_", filename).strip(" .")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    save_path = settings.UPLOAD_DIR / f"{uuid.uuid4().hex}_{filename}"
    total_bytes = 0
    try:
        header = await file.read(5)
        if header != b"%PDF-":
            raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")
        with save_path.open("wb") as saved_file:
            saved_file.write(header)
            total_bytes += len(header)
            while True:
                data = await file.read(1024 * 1024)
                if not data:
                    break
                total_bytes += len(data)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="PDFs must be 100 MB or smaller.")
                saved_file.write(data)
    except Exception:
        save_path.unlink(missing_ok=True)
        raise

    try:
        doc_id = db.insert_document(
            filename=filename,
            file_path=str(save_path),
            file_size=total_bytes,
            page_count=0,
            status="uploaded",
        )
    except Exception:
        save_path.unlink(missing_ok=True)
        raise
    background_tasks.add_task(process_pdf_pipeline, str(save_path), doc_id)
    return {
        "message": f"{filename} uploaded. Brochure details are being processed.",
        "document_id": doc_id,
        "status": "uploaded",
    }


@router.post("/process-local", dependencies=[Depends(require_admin)])
def process_local_brochures():
    """Index the PDFs in the configured brochures folder."""
    if not settings.BROCHURES_DIR.exists():
        raise HTTPException(status_code=404, detail="Brochures directory not found.")
    pdf_files = list(settings.BROCHURES_DIR.glob("*.pdf"))
    processed = []
    for pdf_path in pdf_files:
        doc_id = db.insert_document(
            filename=pdf_path.name,
            file_path=str(pdf_path),
            file_size=pdf_path.stat().st_size,
            page_count=0,
            status="processing",
        )
        process_pdf_pipeline(str(pdf_path), doc_id)
        processed.append({"filename": pdf_path.name, "document_id": doc_id, "status": "indexed"})
    return {"message": f"Processed {len(processed)} brochures.", "brochures": processed}


@router.get("", dependencies=[Depends(require_admin)])
def list_documents():
    """List brochures without exposing server-side file paths."""
    vehicles = db.get_vehicles()
    indexed_ids = {chunk.get("document_id") for chunk in db.local_chunks}
    documents = []
    for document in db.get_documents():
        vehicle = next(
            (item for item in vehicles if item.get("document_id") == document.get("id")),
            {},
        )
        status = document.get("status") or (
            "indexed" if document.get("id") in indexed_ids else "uploaded"
        )
        documents.append({
            "id": document.get("id"),
            "filename": document.get("filename", "Brochure.pdf"),
            "brand": vehicle.get("brand", ""),
            "model": vehicle.get("model", ""),
            "page_count": document.get("page_count", 0),
            "file_size_bytes": document.get("file_size_bytes", 0),
            "status": status,
            "error_message": document.get("error_message"),
            "created_at": document.get("created_at"),
        })
    documents.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return {"documents": documents, "total": len(documents)}


@router.get("/{doc_id}/file", dependencies=[Depends(require_admin)])
def view_document(doc_id: str):
    document = db.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Brochure not found.")
    file_path = Path(document.get("file_path", "")).resolve()
    allowed_directories = (settings.UPLOAD_DIR.resolve(), settings.BROCHURES_DIR.resolve())
    if not file_path.is_file() or not any(
        file_path.is_relative_to(directory) for directory in allowed_directories
    ):
        raise HTTPException(status_code=404, detail="The brochure PDF is not available on this server.")
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=document.get("filename", "brochure.pdf"),
        content_disposition_type="inline",
    )


@router.delete("/{doc_id}", dependencies=[Depends(require_admin)])
def remove_document(doc_id: str):
    document = db.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Brochure not found.")
    db.delete_document(doc_id)
    rag_service.invalidate_cache()

    file_path = Path(document.get("file_path", "")).resolve()
    upload_dir = settings.UPLOAD_DIR.resolve()
    if file_path.is_relative_to(upload_dir) and file_path.is_file():
        file_path.unlink()
    return {"message": f"{document.get('filename', 'Brochure')} was removed."}
