from fastapi import APIRouter, HTTPException, status
from typing import List
from schemas import ConversationCreate, ConversationResponse
from services.firestore_service import (
    save_conversation, list_conversations, get_conversation, delete_conversation
)

router = APIRouter(prefix="/api/conversations", tags=["Conversations History"])

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED, summary="대화 기록 저장")
def create_conversation(conv: ConversationCreate):
    """
    새 대화 기록 세션 또는 메시지 목록을 Firestore에 저장합니다.
    """
    try:
        saved = save_conversation(
            conv_id=None,
            title=conv.title or "새 대화 세션",
            messages=[m.model_dump() for m in conv.messages]
        )
        return saved
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 저장 실패: {str(e)}")

@router.get("", response_model=List[ConversationResponse], summary="저장된 대화 목록 조회")
def get_conversations_list():
    """
    저장된 모든 대화 기록 세션 목록을 조회합니다.
    """
    try:
        return list_conversations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 목록 조회 실패: {str(e)}")

@router.get("/{conv_id}", response_model=ConversationResponse, summary="특정 대화 상세 조회 (불러오기 UX 지원)")
def read_conversation_detail(conv_id: str):
    """
    선택한 대화 세션의 전체 메세지 목록을 불러옵니다.
    """
    try:
        conv = get_conversation(conv_id)
        if not conv:
            raise HTTPException(status_code=404, detail="해당 대화 기록을 찾을 수 없습니다.")
        return conv
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 불러오기 실패: {str(e)}")

@router.delete("/{conv_id}", status_code=status.HTTP_200_OK, summary="특정 대화 기록 삭제")
def remove_conversation(conv_id: str):
    """
    지정한 대화 세션을 삭제합니다.
    """
    try:
        success = delete_conversation(conv_id)
        if not success:
            raise HTTPException(status_code=404, detail="해당 대화 기록을 찾을 수 없습니다.")
        return {"status": "success", "message": f"대화 기록({conv_id})이 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 삭제 실패: {str(e)}")
