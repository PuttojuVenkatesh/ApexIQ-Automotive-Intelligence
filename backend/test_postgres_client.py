import unittest
from unittest.mock import MagicMock

from app.db.postgres_client import PostgresManager


class PostgresManagerTests(unittest.TestCase):
    def create_manager_with_cursor(self):
        manager = PostgresManager.__new__(PostgresManager)
        connection = MagicMock()
        connection.__enter__.return_value = connection
        cursor = MagicMock()
        cursor.__enter__.return_value = cursor
        connection.cursor.return_value = cursor
        manager._connect = MagicMock(return_value=connection)
        return manager, cursor

    def test_insert_document_persists_and_returns_database_id(self):
        manager, cursor = self.create_manager_with_cursor()
        cursor.fetchone.return_value = {"id": "document-id"}

        document_id = manager.insert_document(
            "brochure.pdf", "uploads/brochure.pdf", 1024, 12
        )

        self.assertEqual(document_id, "document-id")
        query, params = cursor.execute.call_args.args
        self.assertIn("INSERT INTO public.documents", query)
        self.assertEqual(
            params[1:], ("brochure.pdf", "uploads/brochure.pdf", 1024, 12, "uploaded")
        )

    def test_get_documents_returns_rows_from_postgresql(self):
        manager, cursor = self.create_manager_with_cursor()
        documents = [{"id": "document-id", "filename": "brochure.pdf"}]
        cursor.fetchall.return_value = documents

        self.assertEqual(manager.get_documents(), documents)
        self.assertIn("SELECT * FROM public.documents", cursor.execute.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
