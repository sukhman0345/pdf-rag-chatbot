from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import answer_query

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        response = answer_query(request.query, session_id=request.session_id)
        return ChatResponse(
            answer=response["answer"],
            sources=response["sources"],
            session_id=request.session_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
