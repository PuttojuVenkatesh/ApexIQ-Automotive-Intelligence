import json
import unittest
import tempfile
from pathlib import Path

from app.db.supabase_client import SupabaseManager
from app.services.rag_service import RAGService


class BrochureGroundedRecommendationTests(unittest.TestCase):
    def test_space_recommendation_uses_retrieved_boot_figures(self):
        chunks = [
            {
                "metadata": {"brand": "Kia", "model": "Seltos"},
                "content": "Boot Space (l) 447**",
            },
            {
                "metadata": {"brand": "Tata", "model": "Nexon"},
                "content": "Boot Space (L) 382** 321**",
            },
        ]

        answer = RAGService._recommend_from_brochures(
            "Which is better for space, Kia Seltos or Tata Nexon?",
            chunks,
        )

        self.assertIn("Kia Seltos", answer)
        self.assertIn("447 L", answer)
        self.assertIn("382 L / 321 L", answer)
        self.assertNotIn("4,370", answer)
        self.assertNotIn("2,610", answer)

    def test_does_not_recommend_without_comparable_brochure_data(self):
        chunks = [
            {"metadata": {"brand": "Kia", "model": "Seltos"}, "content": "Roomy cabin."},
            {"metadata": {"brand": "Tata", "model": "Nexon"}, "content": "Flexible seating."},
        ]

        answer = RAGService._recommend_from_brochures(
            "Which is better for space, Kia Seltos or Tata Nexon?",
            chunks,
        )

        self.assertIn("don't provide comparable boot or dimension figures", answer)
        self.assertNotIn("Best for", answer)

    def test_explicit_new_pair_is_not_contaminated_by_earlier_comparison(self):
        history = [
            {"role": "user", "content": "Compare Kia Seltos and Tata Nexon"},
            {"role": "assistant", "content": "Kia Seltos has more boot space."},
        ]

        context = RAGService._conversation_context(
            "Which is better for space, Alcazar or Creta?",
            history,
        )

        self.assertEqual(context, "")

    def test_follow_up_context_uses_last_user_pair_not_assistant_answer(self):
        history = [
            {"role": "user", "content": "Compare Kia Seltos and Tata Nexon"},
            {"role": "assistant", "content": "Kia Seltos has more boot space."},
            {"role": "user", "content": "Compare Alcazar and Creta"},
            {"role": "assistant", "content": "Creta has more boot space."},
        ]

        context = RAGService._conversation_context("Which one is better?", history)

        self.assertEqual(context, "Compare Alcazar and Creta")

    def test_model_comparison_uses_technical_rows_instead_of_marketing_copy(self):
        chunks = [
            {
                "metadata": {"brand": "Hyundai", "model": "Alcazar"},
                "content": (
                    "Overall length (mm) 4 560 Overall width (mm) 1 800 "
                    "Wheelbase (mm) 2 760 1.5 l turbo GDi petrol 1.5l U2 CRDi diesel"
                ),
            },
            {
                "metadata": {"brand": "Hyundai", "model": "Creta"},
                "content": (
                    "Overall length (mm) 4 330 Overall width (mm) 1 790 "
                    "Wheelbase (mm) 2 610 1.5l MPi petrol 1.5l Turbo GDi petrol"
                ),
            },
        ]

        answer = RAGService._compare_from_brochures("Compare Alcazar and Creta", chunks)

        self.assertIn("4,560 mm", answer)
        self.assertIn("4,330 mm", answer)
        self.assertIn("2,760 mm", answer)
        self.assertIn("2,610 mm", answer)
        self.assertIn("1.5l MPi petrol", answer)
        self.assertNotIn("seamlessly blends", answer)

    def test_comparison_uses_feature_evidence_for_unlisted_brochure_models(self):
        chunks = [
            {
                "metadata": {"brand": "Brand A", "model": "Alpha", "page": 2, "section": "Safety"},
                "content": "Six airbags and electronic stability control are provided.",
            },
            {
                "metadata": {"brand": "Brand B", "model": "Beta", "page": 4, "section": "Technology"},
                "content": "The cabin has a 12-inch touchscreen with wireless phone connectivity.",
            },
        ]

        answer = RAGService._compare_from_brochures(
            "Compare Alpha and Beta in terms of features",
            chunks,
        )

        self.assertIn("Brand A Alpha", answer)
        self.assertIn("six airbags", answer.lower())
        self.assertIn("Brand B Beta", answer)
        self.assertIn("12-inch touchscreen", answer)

    def test_all_brochure_comparison_includes_every_retrieved_model(self):
        chunks = [
            {"metadata": {"brand": "Brand A", "model": "Alpha"}, "content": "Alpha safety feature evidence."},
            {"metadata": {"brand": "Brand B", "model": "Beta"}, "content": "Beta safety feature evidence."},
            {"metadata": {"brand": "Brand C", "model": "Gamma"}, "content": "Gamma safety feature evidence."},
        ]

        answer = RAGService._compare_from_brochures(
            "Compare all brochure vehicles by features",
            chunks,
        )

        self.assertIn("Brand A Alpha", answer)
        self.assertIn("Brand B Beta", answer)
        self.assertIn("Brand C Gamma", answer)

    def test_comparison_chunk_selection_keeps_evidence_from_every_requested_model(self):
        chunks = [
            {"metadata": {"model": "Alpha"}, "chunk_index": index}
            for index in range(5)
        ] + [
            {"metadata": {"model": "Beta"}, "chunk_index": index}
            for index in range(2)
        ]

        selected = RAGService._balance_comparison_chunks(
            chunks,
            ["alpha", "beta"],
            per_model_limit=2,
        )

        self.assertEqual(
            [chunk["metadata"]["model"] for chunk in selected],
            ["Alpha", "Beta", "Alpha", "Beta"],
        )

    def test_feature_evidence_does_not_confuse_power_seats_with_powertrain(self):
        evidence = RAGService._comparison_feature_evidence(
            "Compare vehicle features",
            [{
                "metadata": {"model": "Alpha"},
                "content": (
                    "Hyundai Motor India Limited recommends you to avoid using mobile back covers.\n"
                    "8-Way Power Driver Seat\nFront Seat Side Airbags\nMaximum power 86 PS at 5,500 rpm.\n"
                    "Remote Engine Start/Stop\nFuel Tank Capacity (l)"
                ),
            }],
        )

        self.assertIn("8-Way Power Driver Seat", evidence["Comfort & convenience"][0])
        self.assertIn("Front Seat Side Airbags", evidence["Safety"][0])
        self.assertIn("Maximum power 86 PS", evidence["Powertrain"][0])
        self.assertNotIn("Hyundai Motor India", " ".join(evidence["Powertrain"]))
        self.assertIn("Remote Engine Start/Stop", evidence["Technology"][0])
        self.assertNotIn("Fuel Tank Capacity", " ".join(
            fact for facts in evidence.values() for fact in facts
        ))

    def test_space_recommendation_uses_dimensions_when_boot_is_missing(self):
        chunks = [
            {
                "metadata": {"brand": "Hyundai", "model": "Alcazar"},
                "content": "Overall length (mm) 4 560 Wheelbase (mm) 2 760",
            },
            {
                "metadata": {"brand": "Hyundai", "model": "Creta"},
                "content": "Overall length (mm) 4 330 Wheelbase (mm) 2 610",
            },
        ]

        answer = RAGService._recommend_from_brochures(
            "Which is better for space, Alcazar or Creta?",
            chunks,
        )

        self.assertIn("Better for exterior size: Hyundai Alcazar", answer)
        self.assertIn("4,560 mm vs 4,330 mm length", answer)
        self.assertIn("not necessarily more usable cabin or boot space", answer)

    def test_local_brochure_state_survives_reload(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            local_store = Path(temporary_directory) / "local_store.json"
            manager = SupabaseManager.__new__(SupabaseManager)
            manager._local_store_file = local_store
            manager.local_documents = {
                "doc-id": {"id": "doc-id", "filename": "brochure.pdf", "status": "indexed"}
            }
            manager.local_chunks = [{"document_id": "doc-id", "content": "verified brochure text"}]
            manager.local_vehicles = {"vehicle-id": {"id": "vehicle-id", "document_id": "doc-id"}}
            manager.local_variants = []
            manager._persist_local_store()

            restored = SupabaseManager.__new__(SupabaseManager)
            restored._local_store_file = local_store
            restored.local_documents = {}
            restored.local_chunks = []
            restored.local_vehicles = {}
            restored.local_variants = []
            restored._load_local_cache()

            self.assertEqual(restored.local_documents["doc-id"]["status"], "indexed")
            self.assertEqual(restored.local_chunks[0]["content"], "verified brochure text")
            self.assertIn("vehicle-id", restored.local_vehicles)

    def test_deleting_brochure_removes_only_its_retrieval_chunks(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            local_store = Path(temporary_directory) / "local_store.json"
            manager = SupabaseManager.__new__(SupabaseManager)
            manager.client = None
            manager.is_connected = False
            manager._local_store_file = local_store
            manager.local_documents = {
                "removed-doc": {"id": "removed-doc", "filename": "old.pdf"},
                "remaining-doc": {"id": "remaining-doc", "filename": "active.pdf"},
            }
            manager.local_chunks = [
                {
                    "document_id": "removed-doc",
                    "content": "old brochure facts",
                    "embedding": [1.0, 0.0],
                },
                {
                    "document_id": "remaining-doc",
                    "content": "active brochure facts",
                    "embedding": [1.0, 0.0],
                },
            ]
            manager.local_vehicles = {}
            manager.local_variants = []

            manager.delete_document("removed-doc")

            matches = manager.match_document_chunks([1.0, 0.0], match_threshold=0.1)
            self.assertEqual([chunk["document_id"] for chunk in matches], ["remaining-doc"])
            saved = json.loads(local_store.read_text(encoding="utf-8"))
            self.assertEqual([chunk["document_id"] for chunk in saved["chunks"]], ["remaining-doc"])


if __name__ == "__main__":
    unittest.main()
