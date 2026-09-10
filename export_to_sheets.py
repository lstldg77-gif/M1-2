import os
import csv
from services.ai_service import plan_10_suno_prompts
import config

def export_10_prompts_to_csv(filepath: str = "suno_prompts_10.csv", prompts=None, include_lyrics: bool = True):
    if prompts is None:
        prompts = plan_10_suno_prompts(mood="편안함", condition="보통", custom_request="", include_lyrics=include_lyrics)

    # Ensure parent dir exists
    parent_dir = os.path.dirname(os.path.abspath(filepath))
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    # Use utf-8-sig (UTF-8 with BOM) so Google Sheets & Excel open Korean properly without encoding errors
    with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        # Header matching user request: 항목, 내용, 프롬프트 + 가사옵션 구분
        writer.writerow(["번호", "항목 (곡 제목)", "테마 (분위기)", "가사 옵션", "내용 (가사/설명)", "프롬프트 (Suno AI 스타일 태그)"])

        for idx, item in enumerate(prompts, start=1):
            title = item.get("title", "")
            mood = item.get("mood_keyword", "")
            lyrics = item.get("lyrics", "[Instrumental]")
            prompt = item.get("suno_prompt", "")
            lyrics_type = "가사 포함하지 않음 (연주곡)" if lyrics.strip() == "[Instrumental]" else "가사 포함 (보컬 곡)"
            writer.writerow([idx, title, mood, lyrics_type, lyrics, prompt])

    print(f"[Success] CSV generated for Google Sheets: {os.path.abspath(filepath)}")
    return os.path.abspath(filepath)

if __name__ == "__main__":
    # 1. 가사 포함 10곡 (With Lyrics)
    root_lyrics = os.path.join(os.path.dirname(os.path.abspath(__file__)), "suno_prompts_with_lyrics.csv")
    export_10_prompts_to_csv(root_lyrics, include_lyrics=True)

    # 2. 가사 포함하지 않은 10곡 (Instrumental / Without Lyrics)
    root_inst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "suno_prompts_instrumental.csv")
    export_10_prompts_to_csv(root_inst, include_lyrics=False)

    # 3. 기본 suno_prompts_10.csv 업데이트
    root_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "suno_prompts_10.csv")
    export_10_prompts_to_csv(root_csv, include_lyrics=True)

    # 4. Output 폴더 복사
    out_dir = config.MUSIC_DOWNLOAD_DIR
    export_10_prompts_to_csv(os.path.join(out_dir, "suno_prompts_with_lyrics.csv"), include_lyrics=True)
    export_10_prompts_to_csv(os.path.join(out_dir, "suno_prompts_instrumental.csv"), include_lyrics=False)
    export_10_prompts_to_csv(os.path.join(out_dir, "suno_prompts_10.csv"), include_lyrics=True)
