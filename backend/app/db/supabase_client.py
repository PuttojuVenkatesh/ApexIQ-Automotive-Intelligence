from __future__ import annotations

import uuid
import json
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Dict, Any, Optional
import numpy as np
from app.core.config import settings
from pathlib import Path

if TYPE_CHECKING:
    from supabase import Client

# Attempt to import supabase
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

class SupabaseManager:
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_connected = False
        
        # Local in-memory store for fallback / offline evaluation
        self.local_documents: Dict[str, Dict[str, Any]] = {}
        self.local_chunks: List[Dict[str, Any]] = []
        self.local_vehicles: Dict[str, Dict[str, Any]] = {}
        self.local_variants: List[Dict[str, Any]] = []
        self.local_chat_sessions: Dict[str, List[Dict[str, Any]]] = {}
        self._local_store_file = Path(settings.UPLOAD_DIR) / "local_store.json"

        self._init_connection()
        self._load_local_cache()

    def _init_connection(self):
        if not SUPABASE_AVAILABLE:
            print("[Supabase] SDK is unavailable; using local fallback storage.")
            return
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            print("[Supabase] SUPABASE_URL and SUPABASE_KEY are not configured; using local fallback storage.")
            return

        try:
            client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            for table in (
                "documents",
                "vehicles",
                "vehicle_variants",
                "document_chunks",
                "chat_sessions",
                "chat_messages",
            ):
                client.table(table).select("id").limit(1).execute()
            self.client = client
            self.is_connected = True
            print("[Supabase] Connected; required database tables are available.")
        except Exception as error:
            self.client = None
            self.is_connected = False
            print(
                "[Supabase] Connection/schema check failed; using local fallback storage. "
                f"Check the project URL, service-role key, network, and backend/schema.sql: {error}"
            )
            self.is_connected = False

    def _load_local_cache(self):
        """Loads pre-indexed vector cache if present."""
        import json
        from pathlib import Path
        cache_file = Path(__file__).resolve().parent.parent.parent / "data" / "vector_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                self.local_chunks = cache_data.get("chunks", [])
                for doc in cache_data.get("documents", []):
                    self.local_documents[doc["id"]] = doc
                for v in cache_data.get("vehicles", []):
                    self.local_vehicles[v["id"]] = v
                print(f"[Cache] Successfully loaded {len(self.local_chunks)} pre-indexed chunks from vector cache.")
            except Exception as e:
                print(f"[Cache] Notice: Could not load cache: {e}")
        if self._local_store_file.exists():
            try:
                with self._local_store_file.open("r", encoding="utf-8") as store:
                    saved = json.load(store)
                self.local_documents = {item["id"]: item for item in saved.get("documents", [])}
                self.local_chunks = saved.get("chunks", [])
                self.local_vehicles = {item["id"]: item for item in saved.get("vehicles", [])}
                self.local_variants = saved.get("variants", [])
                print(f"[Local store] Restored {len(self.local_documents)} brochures and {len(self.local_chunks)} chunks.")
            except (OSError, ValueError, KeyError) as e:
                print(f"[Local store] Could not restore saved brochure data: {e}")

    def _persist_local_store(self):
        """Persist the complete fallback index so uploads survive backend restarts."""
        self._local_store_file.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = self._local_store_file.with_suffix(".tmp")
        with temporary_file.open("w", encoding="utf-8") as store:
            json.dump({
                "documents": list(self.local_documents.values()),
                "chunks": self.local_chunks,
                "vehicles": list(self.local_vehicles.values()),
                "variants": self.local_variants,
            }, store)
        os.replace(temporary_file, self._local_store_file)

    # ----------------- Documents -----------------
    def insert_document(self, filename: str, file_path: str, file_size: int, page_count: int, status: str = "uploaded") -> str:
        doc_id = str(uuid.uuid4())
        doc_data = {
            "id": doc_id,
            "filename": filename,
            "file_path": file_path,
            "file_size_bytes": file_size,
            "page_count": page_count,
            "status": status,
            "error_message": None,
            "metadata": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        if self.is_connected:
            try:
                res = self.client.table("documents").insert(doc_data).execute()
                if res.data:
                    return res.data[0]["id"]
            except Exception as e:
                print(f"[Supabase] insert_document failed: {e}. Storing locally.")
        
        self.local_documents[doc_id] = doc_data
        self._persist_local_store()
        return doc_id

    def update_document_status(
        self,
        doc_id: str,
        status: str,
        error_message: Optional[str] = None,
        page_count: Optional[int] = None,
    ):
        if self.is_connected:
            try:
                update_data = {
                    "status": status,
                    "error_message": error_message
                }
                if page_count is not None:
                    update_data["page_count"] = page_count
                self.client.table("documents").update(update_data).eq("id", doc_id).execute()
                return
            except Exception as e:
                print(f"[Supabase] update_document_status failed: {e}")
                
        if doc_id in self.local_documents:
            self.local_documents[doc_id]["status"] = status
            self.local_documents[doc_id]["error_message"] = error_message
            if page_count is not None:
                self.local_documents[doc_id]["page_count"] = page_count
            self._persist_local_store()

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        if self.is_connected:
            try:
                response = self.client.table("documents").select("*").eq("id", doc_id).limit(1).execute()
                return response.data[0] if response.data else None
            except Exception as e:
                print(f"[Supabase] get_document failed: {e}")
        return self.local_documents.get(doc_id)

    def delete_document(self, doc_id: str):
        if self.is_connected:
            try:
                self.client.table("document_chunks").delete().eq("document_id", doc_id).execute()
                vehicle_ids = [
                    vehicle["id"] for vehicle in self.get_vehicles()
                    if vehicle.get("document_id") == doc_id
                ]
                if vehicle_ids:
                    self.client.table("vehicle_variants").delete().in_("vehicle_id", vehicle_ids).execute()
                self.client.table("vehicles").delete().eq("document_id", doc_id).execute()
                self.client.table("documents").delete().eq("id", doc_id).execute()
            except Exception as e:
                print(f"[Supabase] delete_document failed: {e}. Removing from local fallback store.")
                self.is_connected = False

        self.local_documents.pop(doc_id, None)
        vehicle_ids = {
            vehicle_id for vehicle_id, vehicle in self.local_vehicles.items()
            if vehicle.get("document_id") == doc_id
        }
        self.local_vehicles = {
            vehicle_id: vehicle for vehicle_id, vehicle in self.local_vehicles.items()
            if vehicle_id not in vehicle_ids
        }
        self.local_variants = [
            variant for variant in self.local_variants
            if variant.get("vehicle_id") not in vehicle_ids
        ]
        self.local_chunks = [
            chunk for chunk in self.local_chunks
            if chunk.get("document_id") != doc_id
        ]
        self._persist_local_store()

    def get_documents(self) -> List[Dict[str, Any]]:
        if self.is_connected:
            try:
                res = self.client.table("documents").select("*").order("created_at", desc=True).execute()
                return res.data or []
            except Exception as e:
                print(f"[Supabase] get_documents failed: {e}")
                
        return list(self.local_documents.values())

    # ----------------- Vehicles & Variants -----------------
    def insert_vehicle(self, brand: str, model: str, document_id: Optional[str] = None, model_year: Optional[int] = 2024, summary: str = "") -> str:
        veh_id = str(uuid.uuid4())
        veh_data = {
            "id": veh_id,
            "document_id": document_id,
            "brand": brand,
            "model": model,
            "model_year": model_year,
            "summary": summary
        }
        
        if self.is_connected:
            try:
                res = self.client.table("vehicles").insert(veh_data).execute()
                if res.data:
                    return res.data[0]["id"]
            except Exception as e:
                print(f"[Supabase] insert_vehicle failed: {e}")
                
        self.local_vehicles[veh_id] = veh_data
        self._persist_local_store()
        return veh_id

    def insert_variant(self, vehicle_id: str, variant_name: str, fuel_type: str, transmission: str, engine_specs: Dict, key_features: List[str]):
        var_id = str(uuid.uuid4())
        var_data = {
            "id": var_id,
            "vehicle_id": vehicle_id,
            "variant_name": variant_name,
            "fuel_type": fuel_type,
            "transmission": transmission,
            "engine_specs": engine_specs,
            "key_features": key_features
        }
        
        if self.is_connected:
            try:
                self.client.table("vehicle_variants").insert(var_data).execute()
                return var_id
            except Exception as e:
                print(f"[Supabase] insert_variant failed: {e}")
                
        self.local_variants.append(var_data)
        self._persist_local_store()
        return var_id

    def get_vehicles(self) -> List[Dict[str, Any]]:
        if self.is_connected:
            try:
                res = self.client.table("vehicles").select("*, vehicle_variants(*)").execute()
                return res.data or []
            except Exception as e:
                print(f"[Supabase] get_vehicles failed: {e}")
                
        vehicles_copy = []
        for vid, vdata in self.local_vehicles.items():
            v_copy = dict(vdata)
            v_copy["vehicle_variants"] = [var for var in self.local_variants if var["vehicle_id"] == vid]
            vehicles_copy.append(v_copy)
        return vehicles_copy

    # ----------------- Document Chunks & Vector Search -----------------
    def insert_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Each chunk item should have:
        document_id, vehicle_id, chunk_index, content, metadata, embedding (list of floats)
        """
        if not chunks:
            return
            
        if self.is_connected:
            try:
                # Batch insert chunks
                self.client.table("document_chunks").insert(chunks).execute()
                return
            except Exception as e:
                print(f"[Supabase] insert_chunks failed: {e}. Storing locally.")
                
        for chunk in chunks:
            chunk_copy = dict(chunk)
            if "id" not in chunk_copy:
                chunk_copy["id"] = str(uuid.uuid4())
            self.local_chunks.append(chunk_copy)
        self._persist_local_store()

    def match_document_chunks(self, query_embedding: List[float], match_threshold: float = 0.2, match_count: int = 6, filter_vehicle_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.is_connected:
            try:
                params = {
                    "query_embedding": query_embedding,
                    "match_threshold": match_threshold,
                    "match_count": match_count,
                    "filter_vehicle_id": filter_vehicle_id
                }
                res = self.client.rpc("match_document_chunks", params).execute()
                if res.data:
                    return res.data
            except Exception as e:
                print(f"[Supabase] RPC match_document_chunks failed: {e}. Falling back to local cosine calculation.")

        # Local Cosine Similarity Search
        if not self.local_chunks:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        scored_chunks = []
        for c in self.local_chunks:
            if filter_vehicle_id and c.get("vehicle_id") != filter_vehicle_id:
                continue
            
            c_emb = c.get("embedding")
            if not c_emb:
                continue
                
            c_vec = np.array(c_emb, dtype=np.float32)
            # Dimension alignment if needed
            min_dim = min(len(q_vec), len(c_vec))
            dot = np.dot(q_vec[:min_dim], c_vec[:min_dim])
            c_norm = np.linalg.norm(c_vec[:min_dim])
            
            sim = 0.0
            if c_norm > 0:
                sim = float(dot / (q_norm * c_norm))
                
            if sim >= match_threshold:
                scored_chunks.append({
                    "id": c.get("id"),
                    "document_id": c.get("document_id"),
                    "vehicle_id": c.get("vehicle_id"),
                    "chunk_index": c.get("chunk_index"),
                    "content": c.get("content"),
                    "metadata": c.get("metadata", {}),
                    "similarity": sim
                })

        scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_chunks[:match_count]

    # ----------------- Chat Sessions & Messages -----------------
    def create_chat_session(self, title: str = "New Conversation") -> str:
        session_id = str(uuid.uuid4())
        if self.is_connected:
            try:
                res = self.client.table("chat_sessions").insert({"id": session_id, "title": title}).execute()
                if res.data:
                    return res.data[0]["id"]
            except Exception as e:
                print(f"[Supabase] create_chat_session failed: {e}")
                
        self.local_chat_sessions[session_id] = []
        return session_id

    def add_chat_message(self, session_id: str, role: str, content: str, sources: List[Dict[str, Any]] = None):
        msg_id = str(uuid.uuid4())
        msg_data = {
            "id": msg_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "sources": sources or []
        }
        
        if self.is_connected:
            try:
                self.client.table("chat_messages").insert(msg_data).execute()
                return msg_id
            except Exception as e:
                print(f"[Supabase] add_chat_message failed: {e}")
                
        if session_id not in self.local_chat_sessions:
            self.local_chat_sessions[session_id] = []
        self.local_chat_sessions[session_id].append(msg_data)
        return msg_id

    def get_chat_messages(self, session_id: str) -> List[Dict[str, Any]]:
        if self.is_connected:
            try:
                res = self.client.table("chat_messages").select("*").eq("session_id", session_id).order("created_at").execute()
                return res.data
            except Exception as e:
                print(f"[Supabase] get_chat_messages failed: {e}")
                
        return self.local_chat_sessions.get(session_id, [])

if settings.DATABASE_URL:
    from app.db.postgres_client import PostgresManager

    db = PostgresManager()
else:
    db = SupabaseManager()
