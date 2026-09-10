from fastapi import APIRouter, HTTPException, status
from schemas import (
    MusicPlanRequest, MusicPlanResponse,
    MusicGenerateRequest, MusicGenerateResponse,
    MusicStatusResponse,
    MusicDownloadRequest, MusicDownloadResponse
)
from services.ai_service import plan_10_suno_prompts
from services.suno_service import generate_suno_music, check_suno_status, download_audio_to_pc

router = APIRouter(prefix="/api/music", tags=["Suno AI Music Generation & Download"])

@router.post("/plan", response_model=MusicPlanResponse, summary="10가지 Suno 음악 프롬프트 자동 기획")
def plan_music_prompts(req: MusicPlanRequest):
    """
    사용자의 기분과 컨디션을 기반으로 AI가 10가지 맞춤형 Suno AI 음악 프롬프트를 생성합니다.
    """
    try:
        prompts = plan_10_suno_prompts(
            mood=req.mood,
            condition=req.condition,
            custom_request=req.custom_request or "",
            include_lyrics=req.include_lyrics if req.include_lyrics is not None else True,
            count=req.count
        )
        return MusicPlanResponse(prompts=prompts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suno 프롬프트 기획 실패: {str(e)}")

@router.post("/generate", response_model=MusicGenerateResponse, summary="Suno AI 음원 생성 요청 (Apiframe v2)")
def request_music_generation(req: MusicGenerateRequest):
    """
    선택한 프롬프트를 Apiframe Suno v2 API로 전달하여 음원 생성을 시작합니다.
    """
    try:
        res = generate_suno_music(
            prompt=req.prompt,
            tags=req.tags or "",
            title=req.title or "",
            lyrics=req.lyrics or ""
        )
        return MusicGenerateResponse(
            task_id=res["task_id"],
            status=res["status"],
            message=res["message"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suno 음원 생성 요청 실패: {str(e)}")

@router.get("/status/{task_id}", response_model=MusicStatusResponse, summary="Suno 음원 생성 진행 상태 조회")
def get_music_task_status(task_id: str):
    """
    Task ID를 기반으로 작업 진행 상태 (PENDING, PROCESSING, SUCCESS) 및 audio_url을 조회합니다.
    """
    try:
        status_data = check_suno_status(task_id)
        return MusicStatusResponse(
            status=status_data["status"],
            audio_url=status_data.get("audio_url"),
            video_url=status_data.get("video_url"),
            message=status_data.get("message", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")

@router.post("/download", response_model=MusicDownloadResponse, summary="생성된 MP3 음원을 내 PC 지정 폴더로 다운로드")
def download_music_to_pc(req: MusicDownloadRequest):
    """
    생성 완료된 MP3 파일 URL을 내 PC의 지정된 폴더(C:\\Users\\DiCiA\\Downloads\\SunoMusic 등)로 저장합니다.
    """
    try:
        res = download_audio_to_pc(
            audio_url=req.audio_url,
            file_name=req.file_name or "suno_music.mp3",
            save_dir=req.save_dir
        )
        return MusicDownloadResponse(
            status=res["status"],
            file_path=res["file_path"],
            message=res["message"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"내 PC 음원 다운로드 실패: {str(e)}")
