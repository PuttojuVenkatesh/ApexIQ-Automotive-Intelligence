import unittest
from unittest.mock import Mock, patch

from app.core.config import settings
from app.db import supabase_client


class SupabaseConnectionTests(unittest.TestCase):
    def create_manager(self):
        manager = supabase_client.SupabaseManager.__new__(supabase_client.SupabaseManager)
        manager.client = None
        manager.is_connected = False
        return manager

    def test_connection_is_enabled_only_after_required_tables_are_reachable(self):
        client = Mock()
        client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = []
        manager = self.create_manager()

        with (
            patch.object(supabase_client, "SUPABASE_AVAILABLE", True),
            patch.object(supabase_client, "create_client", return_value=client),
            patch.object(settings, "SUPABASE_URL", "https://project.supabase.co"),
            patch.object(settings, "SUPABASE_KEY", "server-secret"),
        ):
            manager._init_connection()

        self.assertTrue(manager.is_connected)
        self.assertIs(manager.client, client)
        self.assertEqual(client.table.call_count, 6)

    def test_connection_failure_leaves_local_fallback_enabled(self):
        client = Mock()
        client.table.return_value.select.return_value.limit.return_value.execute.side_effect = (
            RuntimeError("database unavailable")
        )
        manager = self.create_manager()

        with (
            patch.object(supabase_client, "SUPABASE_AVAILABLE", True),
            patch.object(supabase_client, "create_client", return_value=client),
            patch.object(settings, "SUPABASE_URL", "https://project.supabase.co"),
            patch.object(settings, "SUPABASE_KEY", "server-secret"),
        ):
            manager._init_connection()

        self.assertFalse(manager.is_connected)
        self.assertIsNone(manager.client)

    def test_missing_credentials_do_not_initialize_a_supabase_client(self):
        manager = self.create_manager()

        with (
            patch.object(supabase_client, "SUPABASE_AVAILABLE", True),
            patch.object(supabase_client, "create_client") as create_client,
            patch.object(settings, "SUPABASE_URL", ""),
            patch.object(settings, "SUPABASE_KEY", ""),
        ):
            manager._init_connection()

        create_client.assert_not_called()
        self.assertFalse(manager.is_connected)

    def test_connected_document_list_uses_database_rows_only(self):
        manager = self.create_manager()
        manager.is_connected = True
        manager.local_documents = {"cached": {"id": "cached", "filename": "old.pdf"}}
        database_documents = [{"id": "db", "filename": "new.pdf"}]
        manager.client = Mock()
        manager.client.table.return_value.select.return_value.order.return_value.execute.return_value.data = (
            database_documents
        )

        self.assertEqual(manager.get_documents(), database_documents)

    def test_connected_vehicle_list_does_not_duplicate_local_cache_rows(self):
        manager = self.create_manager()
        manager.is_connected = True
        manager.local_vehicles = {"cached": {"id": "cached", "model": "Creta"}}
        manager.local_variants = []
        database_vehicles = [{"id": "db", "model": "Creta", "vehicle_variants": []}]
        manager.client = Mock()
        manager.client.table.return_value.select.return_value.execute.return_value.data = (
            database_vehicles
        )

        self.assertEqual(manager.get_vehicles(), database_vehicles)


if __name__ == "__main__":
    unittest.main()
