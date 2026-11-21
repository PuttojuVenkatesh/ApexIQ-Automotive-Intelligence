from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from app.core.config import settings

try:
    import psycopg
    from psycopg.rows import dict_row

    PSYCOPG_AVAILABLE = True
except ImportError:
    psycopg = None
    dict_row = None
    PSYCOPG_AVAILABLE = False


class PostgresManager:
    """Direct PostgreSQL implementation of the application's persistence API."""

    def __init__(self):
        if not PSYCOPG_AVAILABLE:
            raise RuntimeError(
                "PostgreSQL support requires psycopg. Install backend/requirements.txt."
            )

        self.is_connected = False
        self._check_connection()

    def _connect(self):
        return psycopg.connect(settings.DATABASE_URL, row_factory=dict_row)

    def _check_connection(self):
        required_tables = (
            "documents",
            "vehicles",
            "vehicle_variants",
            "document_chunks",
            "chat_sessions",
            "chat_messages",
        )
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    for table in required_tables:
                        cursor.execute("SELECT to_regclass(%s)", (f"public.{table}",))
                        if cursor.fetchone()["to_regclass"] is None:
                            raise RuntimeError("required table is missing")
                    cursor.execute(
                        "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                    )
                    if not cursor.fetchone()["exists"]:
                        raise RuntimeError("pgvector extension is missing")
        except Exception:
            raise RuntimeError(
                "Could not initialize PostgreSQL storage. Verify DATABASE_URL, "
                "network access, credentials, and that backend/schema.sql has been applied."
            ) from None
        self.is_connected = True
        print("[PostgreSQL] Connected; required tables and pgvector are available.")

    def insert_document(
        self,
        filename: str,
        file_path: str,
        file_size: int,
        page_count: int,
        status: str = "uploaded",
    ) -> str:
        doc_id = str(uuid.uuid4())
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO public.documents
                        (id, filename, file_path, file_size_bytes, page_count, status, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, '{}'::jsonb)
                    RETURNING id
                    """,
                    (doc_id, filename, file_path, file_size, page_count, status),
                )
                return str(cursor.fetchone()["id"])

    def update_document_status(
        self,
        doc_id: str,
        status: str,
        error_message: Optional[str] = None,
        page_count: Optional[int] = None,
    ):
        query = """
            UPDATE public.documents
            SET status = %s, error_message = %s, updated_at = NOW()
        """
        params: List[Any] = [status, error_message]
        if page_count is not None:
            query += ", page_count = %s"
            params.append(page_count)
        query += " WHERE id = %s"
        params.append(doc_id)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM public.documents WHERE id = %s LIMIT 1", (doc_id,)
                )
                return cursor.fetchone()

    def delete_document(self, doc_id: str):
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM public.documents WHERE id = %s", (doc_id,))

    def get_documents(self) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM public.documents ORDER BY created_at DESC"
                )
                return cursor.fetchall()

    def insert_vehicle(
        self,
        brand: str,
        model: str,
        document_id: Optional[str] = None,
        model_year: Optional[int] = 2024,
        summary: str = "",
    ) -> str:
        vehicle_id = str(uuid.uuid4())
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO public.vehicles
                        (id, document_id, brand, model, model_year, summary)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (vehicle_id, document_id, brand, model, model_year, summary),
                )
                return str(cursor.fetchone()["id"])

    def insert_variant(
        self,
        vehicle_id: str,
        variant_name: str,
        fuel_type: str,
        transmission: str,
        engine_specs: Dict[str, Any],
        key_features: List[str],
    ) -> str:
        variant_id = str(uuid.uuid4())
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO public.vehicle_variants
                        (id, vehicle_id, variant_name, fuel_type, transmission,
                         engine_specs, key_features)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                    RETURNING id
                    """,
                    (
                        variant_id,
                        vehicle_id,
                        variant_name,
                        fuel_type,
                        transmission,
                        json.dumps(engine_specs),
                        json.dumps(key_features),
                    ),
                )
                return str(cursor.fetchone()["id"])

    def get_vehicles(self) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM public.vehicles ORDER BY created_at DESC")
                vehicles = cursor.fetchall()
                if not vehicles:
                    return []
                vehicle_ids = [vehicle["id"] for vehicle in vehicles]
                cursor.execute(
                    """
                    SELECT * FROM public.vehicle_variants
                    WHERE vehicle_id = ANY(%s)
                    ORDER BY created_at
                    """,
                    (vehicle_ids,),
                )
                variants_by_vehicle: Dict[str, List[Dict[str, Any]]] = {}
                for variant in cursor.fetchall():
                    variants_by_vehicle.setdefault(
                        str(variant["vehicle_id"]), []
                    ).append(variant)
                for vehicle in vehicles:
                    vehicle["vehicle_variants"] = variants_by_vehicle.get(
                        str(vehicle["id"]), []
                    )
                return vehicles

    def insert_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return
        rows = []
        for chunk in chunks:
            embedding = chunk.get("embedding")
            rows.append(
                (
                    chunk.get("id") or str(uuid.uuid4()),
                    chunk["document_id"],
                    chunk.get("vehicle_id"),
                    chunk["chunk_index"],
                    chunk["content"],
                    json.dumps(chunk.get("metadata") or {}),
                    f"[{','.join(str(value) for value in embedding)}]"
                    if embedding is not None
                    else None,
                )
            )
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO public.document_chunks
                        (id, document_id, vehicle_id, chunk_index, content, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::vector)
                    """,
                    rows,
                )

    def match_document_chunks(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.2,
        match_count: int = 6,
        filter_vehicle_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        vector = f"[{','.join(str(value) for value in query_embedding)}]"
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, document_id, vehicle_id, chunk_index, content, metadata,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM public.document_chunks
                    WHERE (%s::uuid IS NULL OR vehicle_id = %s::uuid)
                      AND 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (
                        vector,
                        filter_vehicle_id,
                        filter_vehicle_id,
                        vector,
                        match_threshold,
                        vector,
                        match_count,
                    ),
                )
                return cursor.fetchall()

    def create_chat_session(self, title: str = "New Conversation") -> str:
        session_id = str(uuid.uuid4())
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO public.chat_sessions (id, title)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (session_id, title),
                )
                return str(cursor.fetchone()["id"])

    def add_chat_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        message_id = str(uuid.uuid4())
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO public.chat_messages (id, session_id, role, content, sources)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    RETURNING id
                    """,
                    (
                        message_id,
                        session_id,
                        role,
                        content,
                        json.dumps(sources or []),
                    ),
                )
                return str(cursor.fetchone()["id"])

    def get_chat_messages(self, session_id: str) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM public.chat_messages
                    WHERE session_id = %s
                    ORDER BY created_at
                    """,
                    (session_id,),
                )
                return cursor.fetchall()
