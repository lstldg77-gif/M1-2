import os
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import config

# Try importing firebase_admin
FIREBASE_INITIALIZED = False
db = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    svc_json = config.FIREBASE_SERVICE_ACCOUNT_JSON
    if svc_json:
        if os.path.exists(svc_json):
            cred = credentials.Certificate(svc_json)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            FIREBASE_INITIALIZED = True
        elif svc_json.startswith('{'):
            cred_dict = json.loads(svc_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            FIREBASE_INITIALIZED = True
except Exception as e:
    print(f"⚠️ Firebase initialization skipped or failed: {e}. Falling back to Local DB Store.")
    FIREBASE_INITIALIZED = False

# Local fallback store
LOCAL_DB_FILE = os.path.join(os.path.dirname(__file__), "local_db.json")

def _load_local_db() -> Dict[str, Any]:
    if not os.path.exists(LOCAL_DB_FILE):
        data = {"data": {}, "conversations": {}}
        _save_local_db(data)
        return data
    try:
        with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"data": {}, "conversations": {}}

def _save_local_db(store: Dict[str, Any]):
    try:
        with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving local DB: {e}")

# Initial seed data generator (100+ sample time series data points)
def seed_sample_data_if_empty():
    items = get_all_data()
    if len(items) >= 100:
        return

    print("[Seed] Seeding 100 sample time series mood/condition data points...")
    start_date = datetime.now() - timedelta(days=100)
    memos_pool = [
        "비 오고 나른함. 피아노 음악 필요",
        "컨디션 최상! 기분 매우 밝음",
        "야근 후 극심한 피로. 휴식이 필요함",
        "아침 운동 완료. 잔잔하고 신나는 곡 원함",
        "집중력 저하. 차분한 로파이 BGM 필요",
        "친구들과 만남. 에너제틱한 팝 음악",
        "마음이 불안함. 힐링 오케스트라 사운드",
        "일이 잘 풀림. 자신감 넘치는 비트",
        "카페에서 공부 중. 잔잔한 어쿠스틱",
        "주말 드라이브. 시원한 신스웨이브 음악"
    ]

    for i in range(100):
        d = start_date + timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        # Generates a realistic fluctuating score between 3.0 and 9.5
        val = round(5.5 + 2.5 * ((i % 7) - 3) / 3.0 + (i % 5) * 0.4, 1)
        val = max(1.0, min(10.0, val))
        memo = memos_pool[i % len(memos_pool)]

        add_data({"date": date_str, "value": val, "memo": memo})

# --- DATA CRUD ENGINE ---

def add_data(item_dict: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = str(uuid.uuid4())
    item_dict["id"] = doc_id
    if "created_at" not in item_dict:
        item_dict["created_at"] = datetime.now().isoformat()

    if FIREBASE_INITIALIZED and db is not None:
        try:
            db.collection("data").document(doc_id).set(item_dict)
            return item_dict
        except Exception as e:
            print(f"Firestore add_data failed, using local DB: {e}")

    store = _load_local_db()
    store["data"][doc_id] = item_dict
    _save_local_db(store)
    return item_dict

def get_all_data() -> List[Dict[str, Any]]:
    if FIREBASE_INITIALIZED and db is not None:
        try:
            docs = db.collection("data").stream()
            res = []
            for doc in docs:
                d = doc.to_dict()
                d["id"] = doc.id
                res.append(d)
            res.sort(key=lambda x: x.get("date", ""))
            return res
        except Exception as e:
            print(f"Firestore get_all_data failed, using local DB: {e}")

    store = _load_local_db()
    res = list(store.get("data", {}).values())
    res.sort(key=lambda x: x.get("date", ""))
    return res

def get_data_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
    if FIREBASE_INITIALIZED and db is not None:
        try:
            doc = db.collection("data").document(doc_id).get()
            if doc.exists:
                d = doc.to_dict()
                d["id"] = doc.id
                return d
            return None
        except Exception as e:
            print(f"Firestore get_data_by_id failed: {e}")

    store = _load_local_db()
    return store.get("data", {}).get(doc_id)

def update_data(doc_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    existing = get_data_by_id(doc_id)
    if not existing:
        return None

    existing.update({k: v for k, v in updates.items() if v is not None})
    existing["updated_at"] = datetime.now().isoformat()

    if FIREBASE_INITIALIZED and db is not None:
        try:
            db.collection("data").document(doc_id).set(existing, merge=True)
            return existing
        except Exception as e:
            print(f"Firestore update_data failed: {e}")

    store = _load_local_db()
    store["data"][doc_id] = existing
    _save_local_db(store)
    return existing

def delete_data(doc_id: str) -> bool:
    if FIREBASE_INITIALIZED and db is not None:
        try:
            db.collection("data").document(doc_id).delete()
            return True
        except Exception as e:
            print(f"Firestore delete_data failed: {e}")

    store = _load_local_db()
    if doc_id in store.get("data", {}):
        del store["data"][doc_id]
        _save_local_db(store)
        return True
    return False

def get_data_summary() -> Dict[str, Any]:
    items = get_all_data()
    if not items:
        return {
            "period": "N/A",
            "count": 0,
            "metrics": {"total": 0, "average": 0, "max": 0, "min": 0},
            "trend": "데이터 없음"
        }

    items_sorted = sorted(items, key=lambda x: x.get("date", ""))
    first_date = items_sorted[0].get("date", "N/A")
    last_date = items_sorted[-1].get("date", "N/A")
    period_str = f"{first_date} ~ {last_date}"

    values = [float(item.get("value", 0)) for item in items_sorted]
    total_val = round(sum(values), 2)
    count_val = len(values)
    avg_val = round(total_val / count_val, 2)
    max_val = round(max(values), 2)
    min_val = round(min(values), 2)

    # Calculate recent trend (compare last 10 vs previous 10)
    if count_val >= 10:
        recent = values[-5:]
        previous = values[-10:-5]
        recent_avg = sum(recent) / len(recent)
        prev_avg = sum(previous) / len(previous)
        diff_pct = round(((recent_avg - prev_avg) / (prev_avg or 1)) * 100, 1)

        if diff_pct > 3:
            trend_str = f"상승 추세 (최근 평균 대비 +{diff_pct}%)"
        elif diff_pct < -3:
            trend_str = f"하락 추세 (최근 평균 대비 {diff_pct}%)"
        else:
            trend_str = f"보유/유지 추세 (변동폭 {diff_pct}%)"
    else:
        trend_str = "데이터 수집 중 (안정 상태)"

    return {
        "period": period_str,
        "count": count_val,
        "metrics": {
            "total": total_val,
            "average": avg_val,
            "max": max_val,
            "min": min_val
        },
        "trend": trend_str
    }

# --- CONVERSATIONS CRUD ENGINE ---

def save_conversation(conv_id: Optional[str], title: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not conv_id:
        conv_id = str(uuid.uuid4())

    now_str = datetime.now().isoformat()
    doc_dict = {
        "id": conv_id,
        "title": title or "기분 & 음악 대화",
        "messages": messages,
        "updated_at": now_str
    }

    if FIREBASE_INITIALIZED and db is not None:
        try:
            ref = db.collection("conversations").document(conv_id)
            existing = ref.get()
            if not existing.exists:
                doc_dict["created_at"] = now_str
            else:
                doc_dict["created_at"] = existing.to_dict().get("created_at", now_str)
            ref.set(doc_dict, merge=True)
            return doc_dict
        except Exception as e:
            print(f"Firestore save_conversation failed: {e}")

    store = _load_local_db()
    existing = store.get("conversations", {}).get(conv_id)
    if existing:
        doc_dict["created_at"] = existing.get("created_at", now_str)
    else:
        doc_dict["created_at"] = now_str

    store.setdefault("conversations", {})[conv_id] = doc_dict
    _save_local_db(store)
    return doc_dict

def list_conversations() -> List[Dict[str, Any]]:
    if FIREBASE_INITIALIZED and db is not None:
        try:
            docs = db.collection("conversations").stream()
            res = []
            for doc in docs:
                d = doc.to_dict()
                d["id"] = doc.id
                res.append(d)
            res.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return res
        except Exception as e:
            print(f"Firestore list_conversations failed: {e}")

    store = _load_local_db()
    res = list(store.get("conversations", {}).values())
    res.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return res

def get_conversation(conv_id: str) -> Optional[Dict[str, Any]]:
    if FIREBASE_INITIALIZED and db is not None:
        try:
            doc = db.collection("conversations").document(conv_id).get()
            if doc.exists:
                d = doc.to_dict()
                d["id"] = doc.id
                return d
            return None
        except Exception as e:
            print(f"Firestore get_conversation failed: {e}")

    store = _load_local_db()
    return store.get("conversations", {}).get(conv_id)

def delete_conversation(conv_id: str) -> bool:
    if FIREBASE_INITIALIZED and db is not None:
        try:
            db.collection("conversations").document(conv_id).delete()
            return True
        except Exception as e:
            print(f"Firestore delete_conversation failed: {e}")

    store = _load_local_db()
    if conv_id in store.get("conversations", {}):
        del store["conversations"][conv_id]
        _save_local_db(store)
        return True
    return False
