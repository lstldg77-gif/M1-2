from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Time Series Data Schemas ---
class DataItemCreate(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format", example="2026-03-01")
    value: float = Field(..., description="Condition rating / metric value (e.g., 1-10 scale or score)", example=7.5)
    memo: str = Field(..., description="Memo or description of condition/mood", example="약간 피곤함, 비 오는 날 잔잔한 음악 필요")

class DataItemUpdate(BaseModel):
    date: Optional[str] = None
    value: Optional[float] = None
    memo: Optional[str] = None

class DataItemResponse(BaseModel):
    id: str
    date: str
    value: float
    memo: str
    created_at: Optional[str] = None

# --- Summary Schemas ---
class SummaryMetrics(BaseModel):
    total: float
    average: float
    max: float
    min: float

class SummaryResponse(BaseModel):
    period: str
    count: int
    metrics: SummaryMetrics
    trend: str

# --- Conversation Schemas ---
class ChatMessage(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str
    timestamp: Optional[str] = None

class ConversationCreate(BaseModel):
    title: Optional[str] = "대화 세션"
    messages: List[ChatMessage] = []

class ConversationResponse(BaseModel):
    id: str
    title: str
    messages: List[ChatMessage] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# --- Chat Schema ---
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    include_lyrics: Optional[bool] = Field(True, description="가사 포함 여부 (True: 가사 포함, False: 가사 포함하지 않음)")

class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    summary_context: Optional[SummaryResponse] = None
    suno_prompts: Optional[List[Dict[str, Any]]] = None

# --- Music Generation Schemas ---
class MusicPlanRequest(BaseModel):
    mood: str = Field(..., example="잔잔하고 차분한 피아노")
    condition: str = Field(..., example="피곤하고 스트레스 받음")
    custom_request: Optional[str] = ""
    include_lyrics: Optional[bool] = Field(True, description="가사 포함 여부 (True: 가사 포함, False: 가사 포함하지 않음)")
    count: int = Field(10, description="생성할 음악 프롬프트 수 (1, 5, 10, 15)")


class SunoPromptItem(BaseModel):
    id: int
    title: str
    lyrics: str
    suno_prompt: str
    mood_keyword: str

class MusicPlanResponse(BaseModel):
    prompts: List[SunoPromptItem]

class MusicGenerateRequest(BaseModel):
    prompt: str
    tags: Optional[str] = ""
    title: Optional[str] = ""
    lyrics: Optional[str] = ""

class MusicGenerateResponse(BaseModel):
    task_id: str
    status: str
    message: str

class MusicStatusResponse(BaseModel):
    status: str
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    message: str

class MusicDownloadRequest(BaseModel):
    audio_url: str
    file_name: Optional[str] = "suno_music.mp3"
    save_dir: Optional[str] = None

class MusicDownloadResponse(BaseModel):
    status: str
    file_path: str
    message: str
