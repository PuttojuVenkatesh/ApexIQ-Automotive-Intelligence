from typing import Dict, List, Any, Optional
from app.db.supabase_client import db
from app.services.rag_service import rag_service

class ComparisonService:
    """
    Automotive comparison engine for cross-vehicle and cross-variant evaluation.
    """

    def compare_cars(self, car_a: str, car_b: str) -> Dict[str, Any]:
        """
        Compares two distinct car models (e.g., Hyundai Alcazar vs Creta, or Kia Seltos vs Hyundai Creta).
        """
        query = (
            f"Provide a detailed, side-by-side technical comparison between {car_a} and {car_b}. "
            f"Compare their seating capacity, dimensions (length, wheelbase, boot space), "
            f"engine options (power, torque, fuel types), transmission choices, ADAS and safety equipment, "
            f"and premium interior features. Format the comparison as a clean markdown table followed by key differences."
        )

        rag_result = rag_service.query(user_query=query)

        return {
            "car_a": car_a,
            "car_b": car_b,
            "summary": rag_result["answer"],
            "sources": rag_result["sources"],
            "session_id": rag_result.get("session_id")
        }

    def compare_variants(self, vehicle: str, variant_a: str, variant_b: str) -> Dict[str, Any]:
        """
        Compares two trims/variants of the same vehicle model (e.g., Hyundai Creta S vs SX(O)).
        """
        query = (
            f"Compare the '{variant_a}' trim and '{variant_b}' trim of the {vehicle}. "
            f"What additional features, technology, powertrain options, and safety equipment does {variant_b} "
            f"offer over {variant_a}? Provide a feature-by-feature comparison."
        )

        rag_result = rag_service.query(user_query=query)

        return {
            "vehicle": vehicle,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "comparison": rag_result["answer"],
            "sources": rag_result["sources"],
            "session_id": rag_result.get("session_id")
        }

comparison_service = ComparisonService()
