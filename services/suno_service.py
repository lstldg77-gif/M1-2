import os
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional
import config

def generate_suno_music(prompt: str, tags: str = "", title: str = "", lyrics: str = "") -> Dict[str, Any]:
    api_key = config.APIFRAME_API_KEY
    if not api_key:
        raise ValueError("APIFRAME_API_KEY가 설정되지 않았습니다. .env 파일에 키를 입력해주세요.")

    url = "https://api.apiframe.ai/v2/music/generate"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    full_prompt = prompt
    if lyrics and lyrics.strip() != "[Instrumental]":
        full_prompt = f"Lyrics:\n{lyrics}\n\nStyle: {tags}\n\nTitle: {title}\n\nPrompt: {prompt}"
    else:
        if tags:
            full_prompt = f"Style: {tags}\n\n" + full_prompt
        if title:
            full_prompt = f"Title: {title}\n\n" + full_prompt

    payload = {
        "model": "suno",
        "prompt": full_prompt
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            job_id = result.get('jobId') or result.get('task_id') or result.get('id', '')
            return {
                "task_id": job_id,
                "status": result.get('status', 'PENDING'),
                "message": "Suno 음원 생성 요청이 성공적으로 접수되었습니다.",
                "raw_result": result
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8') if e.fp else str(e)
        print(f"Apiframe Suno Generate HTTP Error: {e.code} - {err_body}")
        raise RuntimeError(f"Suno API 오류 (HTTP {e.code}): {err_body}")
    except Exception as e:
        print(f"Apiframe Suno Generate Error: {e}")
        raise RuntimeError(f"Suno 음원 생성 중 오류 발생: {str(e)}")


def check_suno_status(task_id: str) -> Dict[str, Any]:
    api_key = config.APIFRAME_API_KEY
    if not api_key:
        return {"status": "ERROR", "message": "APIFRAME_API_KEY가 설정되지 않았습니다."}

    url = f"https://api.apiframe.ai/v2/jobs/{task_id}"
    req = urllib.request.Request(url, method='GET')
    req.add_header('X-API-Key', api_key)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)

        api_status = str(res_json.get('status', '')).upper()

        audio_url = None
        video_url = None

        if api_status in ['COMPLETED', 'SUCCESS']:
            api_status = 'SUCCESS'
            tracks = res_json.get('result', {}).get('tracks', [])
            if tracks and len(tracks) > 0:
                audio_url = tracks[0].get('audioUrl') or tracks[0].get('audio_url')
                video_url = tracks[0].get('videoUrl') or tracks[0].get('imageUrl')

        return {
            "status": api_status,
            "audio_url": audio_url,
            "video_url": video_url,
            "message": f"현재 작업 상태: {api_status}"
        }
    except Exception as e:
        print(f"Check Suno Status Error: {e}")
        return {
            "status": "PROCESSING",
            "audio_url": None,
            "video_url": None,
            "message": f"상태 확인 중 (진행 중): {str(e)}"
        }


from datetime import datetime

def download_audio_to_pc(audio_url: str, file_name: str = "suno_music.mp3", save_dir: Optional[str] = None) -> Dict[str, Any]:
    base_dir = save_dir or config.MUSIC_DOWNLOAD_DIR
    today_str = datetime.now().strftime("%Y-%m-%d")
    target_dir = os.path.join(base_dir, today_str)
    os.makedirs(target_dir, exist_ok=True)

    if not file_name.endswith('.mp3'):
        file_name += '.mp3'

    # Sanitize file name
    safe_filename = "".join(c for c in file_name if c.isalnum() or c in (' ', '_', '-', '.')).strip()
    full_path = os.path.join(target_dir, safe_filename)

    try:
        req = urllib.request.Request(audio_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp, open(full_path, 'wb') as out_file:
            out_file.write(resp.read())

        return {
            "status": "SUCCESS",
            "file_path": full_path,
            "message": f"음원 파일이 내 PC 저장 폴더({full_path})에 성공적으로 다운로드되었습니다."
        }
    except Exception as e:
        print(f"Download Audio Error: {e}")
        raise RuntimeError(f"음원 다운로드 실패: {str(e)}")
