from fastapi import APIRouter, HTTPException, status
from typing import List
from schemas import DataItemCreate, DataItemUpdate, DataItemResponse, SummaryResponse
from services.firestore_service import (
    add_data, get_all_data, get_data_by_id, update_data, delete_data, get_data_summary
)

router = APIRouter(prefix="/api/data", tags=["Time Series Data (CRUD & Summary)"])

@router.post("", response_model=DataItemResponse, status_code=status.HTTP_201_CREATED, summary="새 시계열 데이터 추가")
def create_data_item(item: DataItemCreate):
    """
    date, value, memo 형태의 새 시계열 컨디션/기분 데이터를 추가합니다.
    """
    try:
        created = add_data(item.model_dump())
        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 추가 중 오류가 발생했습니다: {str(e)}")

@router.get("", response_model=List[DataItemResponse], summary="시계열 데이터 목록 조회")
def list_data_items():
    """
    저장된 모든 시계열 데이터를 날짜 순으로 조회합니다.
    """
    try:
        return get_all_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 목록 조회 실패: {str(e)}")

@router.get("/summary", response_model=SummaryResponse, summary="시계열 데이터 요약 정보 (컨텍스트 주입용)")
def read_data_summary():
    """
    기간, 총 개수, 주요 지표(총합, 평균, 최대, 최소), 최근 추세 등 시스템 프롬프트 주입용 요약 정보를 반환합니다.
    """
    try:
        summary = get_data_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 요약 정보 생성 실패: {str(e)}")

@router.put("/{data_id}", response_model=DataItemResponse, summary="시계열 데이터 수정")
def modify_data_item(data_id: str, updates: DataItemUpdate):
    """
    지정한 ID의 시계열 항목 정보를 수정합니다.
    """
    try:
        updated = update_data(data_id, updates.model_dump(exclude_unset=True))
        if not updated:
            raise HTTPException(status_code=404, detail="해당 ID의 데이터를 찾을 수 없습니다.")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 수정 실패: {str(e)}")

@router.delete("/{data_id}", status_code=status.HTTP_200_OK, summary="시계열 데이터 삭제")
def remove_data_item(data_id: str):
    """
    지정한 ID의 시계열 항목을 삭제합니다.
    """
    try:
        success = delete_data(data_id)
        if not success:
            raise HTTPException(status_code=404, detail="해당 ID의 데이터를 찾을 수 없습니다.")
        return {"status": "success", "message": f"데이터({data_id})가 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 삭제 실패: {str(e)}")
