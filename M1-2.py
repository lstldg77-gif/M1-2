from datetime import datetime
import json
import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore

try:
  from google import genai
  from google.genai import types

  gemini_available = True
except ImportError:
  gemini_available = False

from pydantic import BaseModel, Field

LOCAL_STORE_PATH = os.path.join(os.path.dirname(__file__), "local_store.json")


def read_local_store():
  if not os.path.exists(LOCAL_STORE_PATH):
    return {"data": [], "conversations": []}
  try:
    with open(LOCAL_STORE_PATH, encoding="utf-8") as store_file:
      return json.load(store_file)
  except (OSError, json.JSONDecodeError):
    return {"data": [], "conversations": []}


def write_local_store(store):
  with open(LOCAL_STORE_PATH, "w", encoding="utf-8") as store_file:
    json.dump(store, store_file, ensure_ascii=False, indent=2)

# 환경 변수 로드
load_dotenv()

# Firebase 초기화
cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "serviceAccountKey.json")
db = None
try:
  if not firebase_admin._apps:
    if os.path.exists(cred_path):
      cred = credentials.Certificate(cred_path)
      firebase_admin.initialize_app(cred)
    else:
      firebase_admin.initialize_app()
  db = firestore.client()
except Exception as exc:
  print(f"Firebase를 사용할 수 없습니다: {exc}")

# FastAPI 앱 초기화
app = FastAPI(
    title="일본풍 감성 음악 제작 AI 비서 API",
    description=(
        "Suno/Google Flow/CapCut 음악 제작 데이터 관리 및 제미나이 컨텍스트 주입 챗봇"
    ),
    version="2.1.0",
)

# CORS 설정
allowed_origins = [
  origin.strip()
  for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
  if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
  return {
      "status": "ok",
      "firebase": db is not None,
      "gemini": bool(os.getenv("GEMINI_API_KEY")) and gemini_available,
  }


# Pydantic 모델 정의
class MusicProductionItem(BaseModel):
  date: str = Field(..., description="작업 날짜 (YYYY-MM-DD)")
  value: float = Field(..., description="생성 곡 수 또는 작업 소요 시간(분)")
  memo: str = Field(
      "", description="곡 스타일, 15곡 배치 번호, 캡컷 편집 및 유튜브 업로드 상태"
  )


class MusicItemUpdate(BaseModel):
  date: str | None = None
  value: float | None = None
  memo: str | None = None


class ChatRequest(BaseModel):
  message: str = Field(..., description="사용자 질문")
  conversation_id: str | None = Field(
      None, description="기존 대화 ID (없으면 새로 생성)"
  )


# 1. 데이터 관리 API (CRUD)
@app.post("/api/data", status_code=201)
def create_data(item: MusicProductionItem):
  if not db:
    store = read_local_store()
    item_id = str(uuid.uuid4())
    result = {"id": item_id, **item.model_dump()}
    store["data"].append(result)
    write_local_store(store)
    return result
  doc_ref = db.collection("data").document()
  doc_ref.set(item.model_dump())
  return {"id": doc_ref.id, **item.model_dump()}


@app.get("/api/data")
def get_data_list():
  if not db:
    return sorted(read_local_store()["data"], key=lambda item: item["date"])
  docs = db.collection("data").order_by("date").stream()
  result = []
  for doc in docs:
    d = doc.to_dict()
    d["id"] = doc.id
    result.append(d)
  return result


@app.put("/api/data/{item_id}")
def update_data(item_id: str, item: MusicItemUpdate):
  if not db:
    store = read_local_store()
    saved = next((saved for saved in store["data"] if saved["id"] == item_id), None)
    if saved is None:
      raise HTTPException(status_code=404, detail="Data not found")
    saved.update({k: v for k, v in item.model_dump().items() if v is not None})
    write_local_store(store)
    return saved
  doc_ref = db.collection("data").document(item_id)
  if not doc_ref.get().exists:
    raise HTTPException(status_code=404, detail="Data not found")

  update_data = {
      k: v for k, v in item.model_dump().items() if v is not None
  }
  doc_ref.update(update_data)
  return {"id": item_id, **update_data}


@app.delete("/api/data/{item_id}")
def delete_data(item_id: str):
  if not db:
    store = read_local_store()
    original_count = len(store["data"])
    store["data"] = [saved for saved in store["data"] if saved["id"] != item_id]
    if len(store["data"]) == original_count:
      raise HTTPException(status_code=404, detail="Data not found")
    write_local_store(store)
    return {"message": "Successfully deleted", "id": item_id}
  doc_ref = db.collection("data").document(item_id)
  if not doc_ref.get().exists:
    raise HTTPException(status_code=404, detail="Data not found")
  doc_ref.delete()
  return {"message": "Successfully deleted", "id": item_id}


# 2. 데이터 요약 API (프롬프트 주입용)
@app.get("/api/data/summary")
def get_data_summary():
  if not db:
    items = sorted(read_local_store()["data"], key=lambda item: item["date"])
    if not items:
      return {
          "period": "기록 없음", "count": 0,
          "metrics": {"total_songs": 0, "batch_sessions": 0, "average_per_session": 0},
          "trend": "등록된 음악 제작 데이터가 없습니다.",
      }
    values = [float(item.get("value", 0)) for item in items]
    total = sum(values)
    return {
        "period": f"{items[0]['date']} ~ {items[-1]['date']}",
        "count": len(items),
        "metrics": {
            "total_songs": round(total, 2),
            "batch_sessions": len(items),
            "average_per_session": round(total / len(items), 2),
        },
        "trend": "15곡 일괄 생성 배치 활성화" if values[-1] >= 15 else "개별 곡 작업 위주 진행 중",
    }
  docs = list(db.collection("data").order_by("date").stream())

  if not docs:
    return {
        "period": "기록 없음",
        "count": 0,
        "metrics": {
            "total_songs": 0,
            "batch_sessions": 0,
            "average_per_session": 0,
        },
        "trend": "등록된 음악 제작 데이터가 없습니다.",
    }

  values = [doc.to_dict().get("value", 0) for doc in docs]
  dates = [doc.to_dict().get("date", "") for doc in docs]

  total_songs = sum(values)
  count = len(values)
  avg = total_songs / count if count > 0 else 0

  trend = "안정적 제작 진행 중"
  if count >= 2:
    if values[-1] >= 15:
      trend = "15곡 일괄 생성 배치 활성화 및 캡컷 편집 순항 중"
    else:
      trend = "개별 곡 작업 위주 진행 중"

  return {
      "period": f"{dates[0]} ~ {dates[-1]}",
      "count": count,
      "metrics": {
          "total_songs": round(total_songs, 2),
          "batch_sessions": count,
          "average_per_session": round(avg, 2),
      },
      "trend": trend,
  }


# 3. 대화 기록 API
@app.get("/api/conversations")
def get_conversations():
  if not db:
    return sorted(
        read_local_store()["conversations"],
        key=lambda item: item.get("updated_at", ""), reverse=True
    )
  docs = (
      db.collection("conversations")
      .order_by("updated_at", direction=firestore.Query.DESCENDING)
      .stream()
  )
  result = []
  for doc in docs:
    d = doc.to_dict()
    d["id"] = doc.id
    result.append(d)
  return result


@app.get("/api/conversations/{conv_id}")
def get_conversation_detail(conv_id: str):
  if not db:
    conversation = next(
        (item for item in read_local_store()["conversations"] if item["id"] == conv_id), None
    )
    if conversation is None:
      raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
  doc_ref = db.collection("conversations").document(conv_id)
  doc = doc_ref.get()
  if not doc.exists:
    raise HTTPException(status_code=404, detail="Conversation not found")
  return {"id": doc.id, **doc.to_dict()}


@app.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str):
  if not db:
    store = read_local_store()
    original_count = len(store["conversations"])
    store["conversations"] = [
        item for item in store["conversations"] if item["id"] != conv_id
    ]
    if len(store["conversations"]) == original_count:
      raise HTTPException(status_code=404, detail="Conversation not found")
    write_local_store(store)
    return {"message": "Conversation deleted", "id": conv_id}
  doc_ref = db.collection("conversations").document(conv_id)
  if not doc_ref.get().exists:
    raise HTTPException(status_code=404, detail="Conversation not found")
  doc_ref.delete()
  return {"message": "Conversation deleted", "id": conv_id}


# 4. 제미나이 AI 챗봇 API (컨텍스트 주입)
@app.post("/api/chat")
def chat_with_gemini_ai(req: ChatRequest):
  if not db:
    store = read_local_store()
    summary_data = get_data_summary()
    conversation = next(
        (item for item in store["conversations"] if item["id"] == req.conversation_id), None
    ) if req.conversation_id else None
    messages = conversation["messages"] if conversation else []
    messages.append({"role": "user", "content": req.message})
    reply = (
        f"총 {summary_data['metrics']['total_songs']}개 작업량, "
        f"{summary_data['count']}회 기록입니다. 최근 트렌드는 "
        f"'{summary_data['trend']}'입니다."
    )
    messages.append({"role": "model", "content": reply})
    conversation_id = conversation["id"] if conversation else str(uuid.uuid4())
    saved = {
        "id": conversation_id,
        "title": req.message[:20],
        "messages": messages,
        "updated_at": datetime.utcnow().isoformat(),
    }
    store["conversations"] = [
        item for item in store["conversations"] if item["id"] != conversation_id
    ] + [saved]
    write_local_store(store)
    return {"conversation_id": conversation_id, "reply": reply, "messages": messages}

  summary_data = get_data_summary()

  system_instruction = f"""
당신은 일본풍 감성 음악을 대량 제작(Suno 15곡 배치, Google Flow, 캡컷 편집, 유튜브 업로드)하는 크리에이터의 전문 AI 비서입니다.

[음악 제작 데이터 요약]
- 작업 기간: {summary_data['period']}
- 총 작업 세션: {summary_data['count']}회
- 제작 지표: {summary_data['metrics']}
- 최근 트렌드: {summary_data['trend']}

위 데이터를 바탕으로 일본풍 감성 음악 제작 현황, 배치 작업 효율화, 유튜브 업로드 일정 등에 대해 맞춤형 조언과 답변을 제공하세요.
"""

  messages = []
  conv_ref = None
  if req.conversation_id:
    conv_ref = db.collection("conversations").document(req.conversation_id)
    conv_doc = conv_ref.get()
    if conv_doc.exists:
      messages = conv_doc.to_dict().get("messages", [])

  messages.append({"role": "user", "content": req.message})

  gemini_api_key = os.getenv("GEMINI_API_KEY")
  ai_response_text = ""

  if gemini_api_key and gemini_available:
    try:
      client = genai.Client(api_key=gemini_api_key)
      contents = []
      for m in messages:
        role_label = "user" if m["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role_label,
                parts=[types.Part.from_text(text=m["content"])],
            )
        )

      config = types.GenerateContentConfig(
          system_instruction=system_instruction, temperature=0.7
      )

      response = client.models.generate_content(
          model="gemini-2.5-flash", contents=contents, config=config
      )
      ai_response_text = response.text
    except Exception as e:
      ai_response_text = f"Gemini API 호출 중 오류가 발생했습니다: {str(e)}"
  else:
    ai_response_text = (
        "[Mock AI 응답] GEMINI_API_KEY 미설정. 현재 트렌드:"
        f" {summary_data['trend']}"
    )

  messages.append({"role": "model", "content": ai_response_text})

  current_time = datetime.utcnow().isoformat()
  if not req.conversation_id:
    title = (
        req.message[:20] + "..." if len(req.message) > 20 else req.message
    )
    conv_data = {
        "title": title,
        "messages": messages,
        "updated_at": current_time,
    }
    new_conv_ref = db.collection("conversations").document()
    new_conv_ref.set(conv_data)
    conv_id = new_conv_ref.id
  else:
    conv_id = req.conversation_id
    conv_ref.update({"messages": messages, "updated_at": current_time})

  return {
      "conversation_id": conv_id,
      "reply": ai_response_text,
      "messages": messages,
  }