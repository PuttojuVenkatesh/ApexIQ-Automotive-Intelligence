from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.comparison_service import comparison_service

router = APIRouter(prefix="/api/compare", tags=["Car & Variant Comparison"])

class CarCompareRequest(BaseModel):
    car_a: str
    car_b: str

class VariantCompareRequest(BaseModel):
    vehicle: str
    variant_a: str
    variant_b: str

@router.post("/cars")
def compare_cars_endpoint(payload: CarCompareRequest):
    """
    Compares two vehicle models (e.g., Hyundai Alcazar vs Creta) side-by-side.
    """
    if not payload.car_a or not payload.car_b:
        raise HTTPException(status_code=400, detail="Both car_a and car_b must be specified.")
        
    result = comparison_service.compare_cars(payload.car_a, payload.car_b)
    return result

@router.post("/variants")
def compare_variants_endpoint(payload: VariantCompareRequest):
    """
    Compares two trim levels/variants of a single vehicle model.
    """
    if not payload.vehicle or not payload.variant_a or not payload.variant_b:
        raise HTTPException(status_code=400, detail="vehicle, variant_a, and variant_b are required.")
        
    result = comparison_service.compare_variants(payload.vehicle, payload.variant_a, payload.variant_b)
    return result
