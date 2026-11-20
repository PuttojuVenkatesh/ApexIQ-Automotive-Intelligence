from typing import List, Dict, Any
from fastapi import APIRouter
from app.db.supabase_client import db

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])

@router.get("")
def list_vehicles():
    """Lists all recognized vehicles, models, and extracted variants."""
    vehicles = db.get_vehicles()
    return {"vehicles": vehicles, "total": len(vehicles)}
