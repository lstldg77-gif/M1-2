from fastapi import APIRouter, HTTPException
from schemas import ChatRequest, ChatResponse
from services.ai_service import generate_ai_chat_response

router = APIRouter(prefix="/api/chat", tags=["AI Chatbot (Context Injection)"])

@router.post("", response_model=ChatResponse, summary="AI 비서 대화 (컨텍스트 주입 & 자동 대화 저장)")
def process_chat(req: ChatRequest):
    """
    1. 데이터 요약 조회 (/api/data/summary)
    2. 시스템 프롬프트에 요약 주입 (Context Injection)
    3. OpenAI / Gemini API 호출
    4. 대화 내역 Firestore 'conversations'에 자동 저장
    """
    try:
        if not req.message or not req.message.strip():
            raise HTTPException(status_code=400, detail="메시지 내용이 필요합니다.")

        reply, conv_id, summary_context, suno_prompts = generate_ai_chat_response(
            user_message=req.message.strip(),
            conv_id=req.conversation_id
        )

        return ChatResponse(
            reply=reply,
            conversation_id=conv_id,
            summary_context=summary_context,
            suno_prompts=suno_prompts
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 대화 처리 실패: {str(e)}")
