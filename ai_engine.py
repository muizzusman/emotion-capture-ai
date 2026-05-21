import anthropic
import base64
import json
import os
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-20250514"


# ─────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────

def _to_jpeg_bytes(image_bytes: bytes) -> bytes:
    """Normalize any image format to JPEG bytes."""
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def _encode(image_bytes: bytes) -> str:
    return base64.standard_b64encode(image_bytes).decode("utf-8")


def _clean_json(text: str) -> str:
    """Strip markdown fences if Claude wraps JSON in them."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return text.strip()


# ─────────────────────────────────────────────────
# 1. EMOTION ANALYSIS  (Vision call)
# ─────────────────────────────────────────────────

def analyze_emotion(image_bytes: bytes) -> dict:
    """
    Send a face image to Claude and get a structured emotion analysis.
    Returns a dict with: primary_emotion, confidence, emotion_breakdown,
                         analysis, emoji
    """
    try:
        jpeg_bytes = _to_jpeg_bytes(image_bytes)
        encoded    = _encode(jpeg_bytes)

        response = client.messages.create(
            model=MODEL,
            max_tokens=700,
            system=(
                "You are an expert facial emotion analyst. "
                "Study faces carefully and respond ONLY with valid JSON — "
                "no preamble, no explanation, no markdown."
            ),
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type":       "base64",
                            "media_type": "image/jpeg",
                            "data":       encoded,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Analyze the emotions visible in this person's face.\n"
                            "Return ONLY this JSON structure — no other text:\n"
                            "{\n"
                            '  "primary_emotion": "one of: happy | sad | angry | surprised | fearful | disgusted | neutral | anxious | calm | excited | stressed",\n'
                            '  "confidence": 82,\n'
                            '  "emotion_breakdown": {"happy": 70, "calm": 20, "neutral": 10},\n'
                            '  "analysis": "2-3 warm, empathetic sentences describing what you observe",\n'
                            '  "emoji": "single most fitting emoji"\n'
                            "}"
                        )
                    }
                ]
            }]
        )

        raw  = response.content[0].text
        data = json.loads(_clean_json(raw))
        return data

    except Exception as e:
        return {
            "primary_emotion":  "neutral",
            "confidence":       0,
            "emotion_breakdown": {"neutral": 100},
            "analysis":         f"Could not analyze image. Error: {e}",
            "emoji":            "😐"
        }


# ─────────────────────────────────────────────────
# 2. REFLECTION QUESTIONS
# ─────────────────────────────────────────────────

def generate_reflection_questions(primary_emotion: str, recent_history: list) -> str:
    """
    Given the current emotion and recent history rows
    (each row: timestamp, emotion, analysis),
    return 3 warm introspective questions.
    """
    if recent_history:
        history_text = "\n".join(
            f"  • {row[0]}  →  {row[1]}" for row in recent_history
        )
    else:
        history_text = "  No previous history."

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=(
            "You are a compassionate emotional wellness coach. "
            "Ask warm, non-judgmental, introspective questions. "
            "Never be clinical. Never give advice unless asked. "
            "Just help the user explore their inner world."
        ),
        messages=[{
            "role": "user",
            "content": (
                f"The user is currently feeling: **{primary_emotion}**\n\n"
                f"Their recent emotional history:\n{history_text}\n\n"
                "Write exactly 3 thoughtful, numbered reflection questions "
                "to help them understand why they feel this way. "
                "Keep each question to one sentence. Be gentle and curious."
            )
        }]
    )
    return response.content[0].text.strip()


# ─────────────────────────────────────────────────
# 3. PATTERN ANALYSIS
# ─────────────────────────────────────────────────

def analyze_patterns(user_name: str, recent_history: list, emotion_counts: list) -> str:
    """
    Generate an AI narrative about the user's emotional patterns.
    recent_history: list of (timestamp, emotion, analysis)
    emotion_counts: list of (emotion, count)
    """
    if not recent_history:
        return "No emotional history yet. Capture a few emotions to unlock your pattern analysis."

    counts_text = "\n".join(
        f"  • {emotion}: {count} time{'s' if count > 1 else ''}"
        for emotion, count in emotion_counts
    )
    timeline_text = "\n".join(
        f"  • {row[0]}  →  {row[1]}"
        for row in recent_history
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=(
            "You are an empathetic emotional wellness analyst. "
            "Provide warm, constructive insights — never diagnostic, never alarmist. "
            "Celebrate positive patterns. Gently acknowledge difficult ones."
        ),
        messages=[{
            "role": "user",
            "content": (
                f"Analyze {user_name}'s emotional data:\n\n"
                f"FREQUENCY:\n{counts_text}\n\n"
                f"RECENT TIMELINE:\n{timeline_text}\n\n"
                "Write a 4-part response using these headers exactly:\n"
                "**Pattern Summary** — 2 sentences on the overall trend\n"
                "**Dominant State** — what their most common emotion says about them\n"
                "**Bright Spot** — one genuinely positive observation\n"
                "**One Gentle Suggestion** — one actionable, kind wellness tip\n\n"
                "Be warm, human, and encouraging."
            )
        }]
    )
    return response.content[0].text.strip()