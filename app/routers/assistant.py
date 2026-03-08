from fastapi import APIRouter, HTTPException

from app.models import AssistantQuery, AssistantResponse
from app.services import assistant

router = APIRouter(prefix="/api", tags=["assistant"])


@router.post("/assistant", response_model=AssistantResponse)
def ask_assistant(data: AssistantQuery):
    try:
        answer, sources = assistant.ask(data.question)
        return AssistantResponse(answer=answer, sources=sources)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
