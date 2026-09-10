import os
import json
import re
from typing import List, Dict, Any, Tuple, Optional
import config
from services.firestore_service import get_data_summary, save_conversation, get_conversation

# Check availability of APIs
HAS_OPENAI = False
HAS_GEMINI = False

try:
    import openai
    if config.OPENAI_API_KEY:
        HAS_OPENAI = True
except ImportError:
    pass

try:
    from google import genai
    from google.genai import types
    if config.GEMINI_API_KEY:
        HAS_GEMINI = True
except ImportError:
    pass


def generate_ai_chat_response(
    user_message: str,
    conv_id: Optional[str] = None
) -> Tuple[str, str, Dict[str, Any], Optional[List[Dict[str, Any]]]]:
    # 1. Fetch data summary for context injection
    summary = get_data_summary()

    metrics = summary.get("metrics", {})
    period = summary.get("period", "N/A")
    count = summary.get("count", 0)
    avg_val = metrics.get("average", 0)
    max_val = metrics.get("max", 0)
    min_val = metrics.get("min", 0)
    trend = summary.get("trend", "보통")

    system_prompt = f"""
당신은 사용자의 기분과 컨디션을 케어하며, 맞춤형 Suno AI 음악을 기획 및 제안하는 '나만의 AI 비서'입니다.

[사용자 데이터 요약 정보]
- 기록 기간: {period}
- 총 기록 수: {count}개
- 평균 컨디션 지수: {avg_val}/10 (최고 {max_val}, 최저 {min_val})
- 최근 트렌드: {trend}

[비서의 핵심 역할 & 응답 원칙]
1. 항상 따뜻하고 친근한 톤으로 사용자의 기분과 컨디션을 먼저 물어보거나 공감해주세요.
2. 저장된 사용자의 최근 컨디션 평균({avg_val})과 추세({trend})를 자연스럽게 언급하여 "내 상황을 잘 파악하고 있는 AI 비서"임을 표현하세요.
3. 사용자가 피곤함, 우울함, 신남, 공부 중 등의 기분/컨디션을 말하면, 어울리는 음악 테마와 힐링 메시지를 전하세요.
4. 음악 제안 시 답변 말미에 항상 다음과 같이 질문하세요:
   "🎵 맞춤 음악 10가지를 기획해 드릴까요?
   선택: [1. 🎤 가사 포함 (보컬 곡)] 또는 [2. 🎹 가사 포함하지 않음 (연주곡/Instrumental)] 중 어떤 스타일을 원하시나요?"
"""

    # 2. Get existing conversation history
    messages_history = []
    if conv_id:
        existing = get_conversation(conv_id)
        if existing:
            messages_history = existing.get("messages", [])

    # Append current user message
    messages_history.append({
        "role": "user",
        "content": user_message
    })

    ai_reply = ""
    suno_prompts = None

    # Check if user asked for music generation / prompt creation
    trigger_words = ["음악", "음원", "노래", "프롬프트", "suno", "만들어", "추천", "기분", "컨디션", "가사"]
    is_music_requested = any(w in user_message.lower() for w in trigger_words)

    # Call AI model
    if config.OPENAI_API_KEY and HAS_OPENAI:
        try:
            client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
            openai_msgs = [{"role": "system", "content": system_prompt}]
            for msg in messages_history[-8:]:  # keep last 8 messages
                openai_msgs.append({"role": msg["role"], "content": msg["content"]})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=openai_msgs,
                temperature=0.7
            )
            ai_reply = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API call failed: {e}. Falling back to Gemini or default response.")

    if not ai_reply and config.GEMINI_API_KEY and HAS_GEMINI:
        try:
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            prompt_content = f"{system_prompt}\n\n[이전 대화 내용]\n"
            for msg in messages_history[-6:]:
                prompt_content += f"{msg['role']}: {msg['content']}\n"
            prompt_content += f"user: {user_message}\nassistant:"

            candidate_models = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-2.0-flash-lite']
            for m in candidate_models:
                try:
                    res = client.models.generate_content(model=m, contents=prompt_content)
                    if res and res.text:
                        ai_reply = res.text.strip()
                        break
                except Exception:
                    continue
        except Exception as e:
            print(f"Gemini API call failed: {e}")

    if not ai_reply:
        # Fallback intelligent rule-based reply if API keys are unreachable
        ai_reply = (
            f"안녕하세요! 최근 기록된 컨디션 평균은 {avg_val}점({trend})입니다. "
            f"오늘 하루 기분과 컨디션은 어떠신가요? 10가지 Suno 음악을 기획해 드릴 수 있어요!\n\n"
            f"선택해 주세요:\n"
            f"1. 🎤 [가사 포함] - 감성 보컬과 4줄 가사로 기획\n"
            f"2. 🎹 [가사 포함하지 않음] - 힐링/집중용 순수 연주곡(Instrumental)으로 기획"
        )

    # Generate 10 Suno prompts if requested
    if is_music_requested:
        # Detect lyrics preference from user message
        is_instrumental = any(w in user_message.lower() for w in ["연주곡", "가사 없이", "가사 미포함", "가사포함하지", "가사없", "instrumental", "bgm"])
        lyrics_opt = not is_instrumental
        suno_prompts = plan_10_suno_prompts(
            mood=user_message,
            condition=f"컨디션 평균 {avg_val}, {trend}",
            include_lyrics=lyrics_opt
        )

    # Append assistant reply to history & save to Firestore
    messages_history.append({
        "role": "assistant",
        "content": ai_reply
    })

    saved_session = save_conversation(
        conv_id=conv_id,
        title=f"대화 ({user_message[:15]}...)" if len(user_message) > 15 else user_message,
        messages=messages_history
    )

    return ai_reply, saved_session["id"], summary, suno_prompts


def plan_10_suno_prompts(
    mood: str,
    condition: str,
    custom_request: str = "",
    include_lyrics: bool = True,
    count: int = 10
) -> List[Dict[str, Any]]:
    target_count = count if count in (1, 5, 10, 15) else 10
    lyrics_rule = (
        "- [가사 옵션: 가사 포함 (보컬 곡)]\n"
        "  10곡 모두 각 테마에 어울리는 한국어 4줄 감성 가사를 반드시 작성해줘.\n"
        "  suno_prompt에는 어울리는 보컬 스타일 태그(예: warm female vocal, soft vocal, indie pop vocal 등)를 반드시 포함해줘."
        if include_lyrics else
        "- [가사 옵션: 가사 포함하지 않음 (연주곡/Instrumental)]\n"
        "  10곡 모두 가사가 없는 순수 연주곡으로 기획해줘.\n"
        "  lyrics 필드는 반드시 '[Instrumental]'로 지정해줘.\n"
        "  suno_prompt 맨 앞에 'instrumental' 태그를 반드시 넣고 보컬(vocal) 관련 단어는 일체 제외해줘."
    )

    prompt = f"""
너는 사용자의 기분과 컨디션에 가장 완벽하게 어울리는 음악을 기획하는 전문 Suno AI 프로듀서야.
제시된 [기분], [컨디션], [가사 옵션], [요청사항]을 바탕으로 **서로 다른 느낌의 Suno AI 전용 음악 프롬프트 {target_count}가지**를 JSON 배열 형식으로 반환해 줘.

[입력 정보]
- 기분: {mood}
- 컨디션: {condition}
- 추가 요청: {custom_request}
- 가사 설정:
{lyrics_rule}

[응답 JSON 형식]
[
  {{
    "id": 1,
    "title": "노래 제목 (한국어)",
    "lyrics": "4줄짜리 짧은 감성 가사 또는 [Instrumental]",
    "suno_prompt": "Suno AI 전용 영어 스타일 태그 (예: lo-fi chill hop, soft acoustic guitar, relaxing, 75 bpm)",
    "mood_keyword": "테마 키워드 (예: 깊은 휴식, 에너지 충전, 새벽 센치)"
  }},
    ... (총 {target_count}개)
]

반드시 다른 설명 없이 오직 JSON 배열만 반환해. 마크다운 코드 블록(```json 등)도 제외하고 순수 JSON만 응답해.
"""

    result_text = ""

    # Call Gemini first if available (fast and high quality prompt gen)
    if config.GEMINI_API_KEY and HAS_GEMINI:
        try:
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            candidate_models = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-2.0-flash-lite']
            for m in candidate_models:
                try:
                    res = client.models.generate_content(model=m, contents=prompt)
                    if res and res.text:
                        result_text = res.text.strip()
                        break
                except Exception:
                    continue
        except Exception as e:
            print(f"Gemini prompt plan error: {e}")

    if not result_text and config.OPENAI_API_KEY and HAS_OPENAI:
        try:
            client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            result_text = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI prompt plan error: {e}")

    # Parse JSON
    if result_text:
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        try:
            prompts_list = json.loads(result_text.strip())
            if isinstance(prompts_list, list) and len(prompts_list) >= target_count:
                return prompts_list[:target_count]
        except Exception as pe:
            print(f"Failed to parse AI prompt JSON: {pe}")

    # Rule-based 10 default prompts fallback
    base_prompts = [
        {
            "id": 1,
            "title": "새벽녘의 따뜻한 온기",
            "lyrics": "조용한 새벽 하늘 아래\n작은 온기가 찾아와\n지친 마음에 차오르는\n은은한 안식의 시간",
            "suno_prompt": "soft acoustic guitar, lo-fi piano, soothing melody, warm female vocal, relaxing ambient, 70 bpm",
            "mood_keyword": "깊은 휴식"
        },
        {
            "id": 2,
            "title": "비 내리는 카페 테라스",
            "lyrics": "창가를 두드리는 빗소리\n따뜻한 라떼 한 잔의 여유\n천천히 흐르는 시간 속에\n생각을 내려놓아",
            "suno_prompt": "chill jazz hop, rain sound effect, warm electric piano, smooth female vocal, smooth bass, 75 bpm",
            "mood_keyword": "감성/비"
        },
        {
            "id": 3,
            "title": "오늘도 잘 견뎌낸 너에게",
            "lyrics": "긴 하루의 끝자락에서\n수고했다고 말해줄게\n내일은 더 빛날 테니\n편안히 눈을 감아",
            "suno_prompt": "emotional ballad, acoustic piano, soft strings, warm female vocal, slow tempo",
            "mood_keyword": "위로/응원"
        },
        {
            "id": 4,
            "title": "마인드 리셋 (Focus Flow)",
            "lyrics": "복잡한 생각 잠시 비우고\n차분한 숨결로 나를 채워\n맑아진 마음으로 다시\n새로운 집중을 시작해",
            "suno_prompt": "ambient chill synth, binaural beats, focus study music, soft vocal hums, atmospheric, 60 bpm",
            "mood_keyword": "집중력 강화"
        },
        {
            "id": 5,
            "title": "햇살 가득한 주말 아침",
            "lyrics": "커튼 사이로 쏟아지는 햇살\n새로운 바람이 불러오는 기쁨\n가벼운 걸음으로 시작해\n오늘의 주인공은 나야",
            "suno_prompt": "bright indie pop, cheerful acoustic strumming, joyful whistling, upbeat bright vocal, 110 bpm",
            "mood_keyword": "에너지 리프레시"
        },
        {
            "id": 6,
            "title": "노을빛 드라이브",
            "lyrics": "붉게 물드는 저 하늘 너머\n시원하게 달리는 도로 위에\n모든 걱정은 바람에 날리고\n자유로움을 느껴봐",
            "suno_prompt": "synthwave, 80s retro pop, energetic synth, driving beat, nostalgic male vocal, 120 bpm",
            "mood_keyword": "드라이브/기분전환"
        },
        {
            "id": 7,
            "title": "별빛 아래 딥 슬립",
            "lyrics": "밤하늘 가득 수놓은 별들\n지친 하루를 따스히 감싸네\n편안한 꿈속으로 걸어가\n아침이 올 때까지 잘 자렴",
            "suno_prompt": "deep ambient pad, quiet lullaby piano, meditation soundscape, angelic soft vocal, ultra relaxing, 50 bpm",
            "mood_keyword": "수면/숙면"
        },
        {
            "id": 8,
            "title": "시원한 파도와 트로피컬 바이브",
            "lyrics": "하얀 파도가 부서지는 바다\n푸른 바람과 함께 춤추자\n가장 뜨거운 여름날의 추억\n가슴 속 깊이 간직해",
            "suno_prompt": "tropical house, summer dance pop, marimba beat, bright vocals, uplifting, 124 bpm",
            "mood_keyword": "청량/신남"
        },
        {
            "id": 9,
            "title": "고요한 숲속의 숨결",
            "lyrics": "푸른 바람이 뺨을 스치고\n숲의 속삭임이 나를 반겨\n자연의 품에 안겨 쉬어가는\n평화로운 치유의 시간",
            "suno_prompt": "forest nature sounds, celtic flute, peaceful acoustic harp, healing soft vocal, 65 bpm",
            "mood_keyword": "자연 힐링"
        },
        {
            "id": 10,
            "title": "당당한 걸음의 시티 바이브",
            "lyrics": "화려한 도시의 조명 아래\n나만의 박자로 걸어가지\n흔들리지 않는 내 모습 그대로\n당당하게 전진해",
            "suno_prompt": "hiphop beat, trendy R&B groove, deep bassline, cool vocal hooks, confident vibe, 95 bpm",
            "mood_keyword": "자신감/동기부여"
        }
    ]

    while len(base_prompts) < target_count:
        source = base_prompts[(len(base_prompts) - 10) % 10]
        variation = dict(source)
        variation["id"] = len(base_prompts) + 1
        variation["title"] = f"{source['title']} - 버전 {len(base_prompts) - 9}"
        base_prompts.append(variation)

    base_prompts = base_prompts[:target_count]

    if not include_lyrics:
        for item in base_prompts:
            item["lyrics"] = "[Instrumental]"
            tags = item["suno_prompt"]
            for v_tag in ["warm female vocal", "smooth female vocal", "emotional female vocal", "soft vocal hums", "bright vocal", "nostalgic male vocal", "angelic soft vocal", "bright vocals", "healing soft vocal", "cool vocal hooks"]:
                tags = tags.replace(v_tag, "")
            cleaned_tags = ", ".join([t.strip() for t in tags.split(",") if t.strip()])
            item["suno_prompt"] = f"instrumental, {cleaned_tags}"

    return base_prompts

