from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.supabase_client import db
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    session_id: str
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    related_vehicles: List[Dict[str, str]] = Field(default_factory=list)
    chunks_retrieved: int

@router.post("", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    """
    RAG-powered conversational endpoint.
    Answers vehicle queries with official brochure facts and page citations.
    """
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
    result = rag_service.query(
        user_query=payload.query.strip(),
        session_id=payload.session_id,
        filter_vehicle_id=payload.vehicle_id,
        conversation_history=payload.conversation_history[-8:]
    )
    return result

@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str):
    """Retrieves all past messages and source citations for a chat session."""
    messages = db.get_chat_messages(session_id)
    return {"session_id": session_id, "messages": messages}
