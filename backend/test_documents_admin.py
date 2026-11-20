import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import documents
from app.core.config import settings


class InMemoryDocumentStore:
    def __init__(self):
        self.documents = {}
        self.local_chunks = []

    def insert_document(self, filename, file_path, file_size, page_count, status):
        document_id = "test-document"
        self.documents[document_id] = {
            "id": document_id,
            "filename": filename,
            "file_path": file_path,
            "file_size_bytes": file_size,
            "page_count": page_count,
            "status": status,
        }
        return document_id

    def get_documents(self):
        return list(self.documents.values())

    def get_document(self, document_id):
        return self.documents.get(document_id)

    def get_vehicles(self):
        return []

    def delete_document(self, document_id):
        self.documents.pop(document_id, None)


class DocumentAdminRouteTests(unittest.TestCase):
    def test_auth_upload_view_and_delete(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            upload_directory = root / "uploads"
            brochure_directory = root / "brochures"
            upload_directory.mkdir()
            brochure_directory.mkdir()
            store = InMemoryDocumentStore()
            app = FastAPI()
            app.include_router(documents.router)

            with (
                patch.object(settings, "ADMIN_USERNAME", "admin"),
                patch.object(settings, "ADMIN_PASSWORD", "test-password"),
                patch.object(settings, "UPLOAD_DIR", upload_directory),
                patch.object(settings, "BROCHURES_DIR", brochure_directory),
                patch.object(documents, "db", store),
                patch.object(documents, "process_pdf_pipeline"),
                TestClient(app) as client,
            ):
                self.assertEqual(client.get("/api/documents").status_code, 401)
                self.assertEqual(
                    client.post(
                        "/api/documents/auth/login",
                        json={"username": "admin", "password": "wrong-password"},
                    ).status_code,
                    401,
                )
                login = client.post(
                    "/api/documents/auth/login",
                    json={"username": "admin", "password": "test-password"},
                )
                self.assertEqual(login.status_code, 200, login.text)
                token = login.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                response = client.post(
                    "/api/documents/upload",
                    headers=headers,
                    files={"file": ("..\\example.pdf", b"%PDF-1.4 test content", "application/pdf")},
                )
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()["status"], "uploaded")
                document = store.get_document("test-document")
                self.assertEqual(document["filename"], "example.pdf")
                saved_path = Path(document["file_path"])
                self.assertTrue(saved_path.is_file())

                listing = client.get(
                    "/api/documents",
                    headers=headers,
                ).json()
                self.assertNotIn("file_path", listing["documents"][0])
                self.assertEqual(
                    client.get(
                        "/api/documents/test-document/file",
                        headers=headers,
                    ).content,
                    b"%PDF-1.4 test content",
                )
                deleted = client.delete(
                    "/api/documents/test-document",
                    headers=headers,
                )
                self.assertEqual(deleted.status_code, 200, deleted.text)
                self.assertFalse(saved_path.exists())
                expired_login = client.post(
                    "/api/documents/auth/login",
                    json={"username": "admin", "password": "test-password"},
                )
                expired_token = expired_login.json()["access_token"]
                documents._admin_sessions[expired_token] = 0
                self.assertEqual(
                    client.get(
                        "/api/documents",
                        headers={"Authorization": f"Bearer {expired_token}"},
                    ).status_code,
                    401,
                )
                self.assertEqual(client.post("/api/documents/auth/logout", headers=headers).status_code, 200)
                self.assertEqual(client.get("/api/documents", headers=headers).status_code, 401)

    def test_upload_rejects_non_pdf_content(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            upload_directory = Path(temporary_directory) / "uploads"
            upload_directory.mkdir()
            app = FastAPI()
            app.include_router(documents.router)

            with (
                patch.object(settings, "ADMIN_USERNAME", "admin"),
                patch.object(settings, "ADMIN_PASSWORD", "test-password"),
                patch.object(settings, "UPLOAD_DIR", upload_directory),
                patch.object(documents, "db", InMemoryDocumentStore()),
                TestClient(app) as client,
            ):
                login = client.post(
                    "/api/documents/auth/login",
                    json={"username": "admin", "password": "test-password"},
                )
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
                response = client.post(
                    "/api/documents/upload",
                    headers=headers,
                    files={"file": ("invalid.pdf", b"not a PDF", "application/pdf")},
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(list(upload_directory.iterdir()), [])

    def test_admin_routes_are_disabled_without_credentials(self):
        app = FastAPI()
        app.include_router(documents.router)

        with (
            patch.object(settings, "ADMIN_USERNAME", ""),
            patch.object(settings, "ADMIN_PASSWORD", ""),
            TestClient(app) as client,
        ):
            response = client.post(
                "/api/documents/auth/login",
                json={"username": "admin", "password": "test-password"},
            )
            self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
