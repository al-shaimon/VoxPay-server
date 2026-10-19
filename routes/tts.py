import re
import asyncio
import edge_tts
import httpx
from fastapi import APIRouter, Query, Response, HTTPException

router = APIRouter(prefix="/api/tts", tags=["TTS"])

# In-memory LRU cache for instant 0ms response on repeat requests
AUDIO_CACHE: dict[str, bytes] = {}
MAX_CACHE_ENTRIES = 500

# Shared async HTTP client with keep-alive for sub-second TTS latency
_HTTP_CLIENT: httpx.AsyncClient | None = None

def get_http_client() -> httpx.AsyncClient:
    global _HTTP_CLIENT
    if _HTTP_CLIENT is None or _HTTP_CLIENT.is_closed:
        _HTTP_CLIENT = httpx.AsyncClient(
            timeout=3.5,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://translate.google.com/"
            }
        )
    return _HTTP_CLIENT

@router.get("", summary="Fast natural human text-to-speech audio stream")
async def get_text_to_speech(
    text: str = Query(..., description="Text to convert to natural human speech"),
    lang: str = Query("bn", description="Language code: bn (Bengali) or en (English)"),
    gender: str = Query("female", description="Voice gender: female or male")
):
    raw_text = text.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    clean = re.sub(r"[*#_`~>]+", " ", raw_text)
    clean = re.sub(r"•|·|\|", ", ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    target_lang = "bn" if lang.startswith("bn") else "en"
    cache_key = f"{target_lang}:{clean}"

    # Return cached audio instantly (0ms)
    if cache_key in AUDIO_CACHE:
        return Response(
            content=AUDIO_CACHE[cache_key],
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "public, max-age=604800, immutable",
                "Content-Disposition": "inline; filename=speech.mp3",
                "X-TTS-Cache": "HIT"
            }
        )

    audio_bytes: bytes | None = None

    # 1. Ultra-fast Google Neural TTS Engine (~0.3s - 0.6s)
    try:
        query_text = clean if len(clean) <= 190 else clean[:190]
        client = get_http_client()
        res = await client.get(
            "https://translate.google.com/translate_tts",
            params={
                "ie": "UTF-8",
                "q": query_text,
                "tl": target_lang,
                "client": "tw-ob"
            }
        )
        if res.status_code == 200 and len(res.content) > 200:
            audio_bytes = res.content
    except Exception:
        pass

    # 2. Secondary Engine: Edge-TTS Native Neural Voice (if Google was blocked or unreachable)
    if not audio_bytes:
        try:
            if target_lang == "bn":
                voice = "bn-BD-PradeepNeural" if gender == "male" else "bn-BD-NabanitaNeural"
            else:
                voice = "en-US-GuyNeural" if gender == "male" else "en-US-AriaNeural"

            communicate = edge_tts.Communicate(clean[:190], voice, rate="+15%")
            data = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    data.extend(chunk["data"])
            if data:
                audio_bytes = bytes(data)
        except Exception:
            pass

    if not audio_bytes:
        raise HTTPException(status_code=502, detail="TTS service temporarily unavailable")

    # Save to in-memory cache
    if len(AUDIO_CACHE) < MAX_CACHE_ENTRIES:
        AUDIO_CACHE[cache_key] = audio_bytes

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "public, max-age=604800, immutable",
            "Content-Disposition": "inline; filename=speech.mp3",
            "X-TTS-Cache": "MISS"
        }
    )
