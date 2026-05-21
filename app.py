import streamlit as st
import json
import os
import io
from PIL import Image
from datetime import datetime
import plotly.graph_objects as go

import database as db
import ai_engine as ai

# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Emotion Capture AI",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════
EMOTION_EMOJI = {
    "happy":     "😊", "sad":       "😢", "angry":     "😠",
    "surprised": "😲", "fearful":   "😨", "disgusted": "🤢",
    "neutral":   "😐", "anxious":   "😰", "calm":      "😌",
    "excited":   "🤩", "stressed":  "😤"
}

EMOTION_COLOR = {
    "happy":     "#F5C518", "sad":       "#4A90E2", "angry":     "#E05252",
    "surprised": "#FF9500", "fearful":   "#9B59B6", "disgusted": "#27AE60",
    "neutral":   "#7F8C8D", "anxious":   "#E67E22", "calm":      "#1ABC9C",
    "excited":   "#E91E8C", "stressed":  "#E74C3C"
}

# ═══════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* Hide default Streamlit nav */
    div[data-testid="stSidebarNav"] { display: none !important; }
    
    /* Remove top padding */
    .block-container { padding-top: 1.5rem; }

    /* Cards */
    .card {
        background: #16161F;
        border-radius: 16px;
        padding: 24px 28px;
        margin: 12px 0;
        border: 1px solid #2A2A38;
    }
    .card-sm {
        background: #16161F;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
        border: 1px solid #2A2A38;
    }

    /* Emotion result display */
    .emotion-hero {
        text-align: center;
        padding: 32px 20px 20px;
    }
    .emotion-emoji-big {
        font-size: 80px;
        display: block;
        margin-bottom: 8px;
    }
    .emotion-label {
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin: 0;
    }
    .emotion-confidence {
        font-size: 13px;
        color: #888;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-top: 4px;
    }

    /* Pill badges */
    .badge {
        display: inline-block;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 3px;
    }

    /* Section labels */
    .label {
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #666;
        margin-bottom: 6px;
        display: block;
    }

    /* History items */
    .history-row {
        display: flex;
        align-items: center;
        gap: 14px;
        background: #16161F;
        border-radius: 12px;
        padding: 14px 18px;
        margin: 6px 0;
        border: 1px solid #2A2A38;
        border-left-width: 4px;
    }
    .history-emoji  { font-size: 26px; }
    .history-meta   { font-size: 12px; color: #666; margin-top: 2px; }

    /* Welcome screen */
    .welcome-title {
        font-size: 42px;
        font-weight: 800;
        letter-spacing: -1px;
        margin: 0;
        line-height: 1.1;
    }
    .welcome-sub {
        color: #888;
        font-size: 16px;
        margin: 12px 0 32px;
    }

    /* Streamlit button tweak */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
    }
    .stTextArea > div > div > textarea {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════════
db.init_db()
os.makedirs("captures", exist_ok=True)

# Session state defaults
for key, val in {
    "user_name":       "",
    "last_result":     None,
    "last_reflection": "",
    "pattern_text":    "",
    "reflect_q":       "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ═══════════════════════════════════════════════════════════════════
# WELCOME / LOGIN SCREEN
# ═══════════════════════════════════════════════════════════════════
if not st.session_state.user_name:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([0.5, 2, 0.5])
    with col:
        st.markdown('<p class="welcome-title">🧠<br>Emotion<br>Capture AI</p>', unsafe_allow_html=True)
        st.markdown('<p class="welcome-sub">Track your emotions. Discover your patterns.<br>Grow in self-awareness.</p>', unsafe_allow_html=True)

        name = st.text_input("Your name", placeholder="Enter your name to begin...")
        if st.button("Start Tracking  →", type="primary", use_container_width=True):
            if name.strip():
                st.session_state.user_name = name.strip()
                st.rerun()
            else:
                st.error("Please enter your name.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"### 👋 {st.session_state.user_name}")
    st.markdown("---")

    counts = db.get_emotion_counts(st.session_state.user_name)
    total  = db.get_total_count(st.session_state.user_name)

    col1, col2 = st.columns(2)
    col1.metric("Captures", total)
    if counts:
        top_em = counts[0][0]
        col2.metric("Top Mood", EMOTION_EMOJI.get(top_em, "❓"))

    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["📸  Capture", "📋  History", "📊  Insights", "💭  Reflect"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    if st.button("⇄  Switch User", use_container_width=True):
        for key in ["user_name", "last_result", "last_reflection", "pattern_text", "reflect_q"]:
            st.session_state[key] = "" if key == "user_name" else None if key == "last_result" else ""
        st.rerun()


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════
def emotion_card_html(emotion, emoji, confidence, color):
    return f"""
    <div class="card emotion-hero">
        <span class="emotion-emoji-big">{emoji}</span>
        <p class="emotion-label" style="color:{color}">{emotion}</p>
        <p class="emotion-confidence">Confidence — {confidence}%</p>
    </div>
    """

def badge_html(label, color):
    return f'<span class="badge" style="background:{color}22;color:{color};border:1px solid {color}55">{label}</span>'


# ═══════════════════════════════════════════════════════════════════
# PAGE — CAPTURE
# ═══════════════════════════════════════════════════════════════════
if page == "📸  Capture":
    st.markdown("## Capture Emotion")
    st.caption("Take a photo or upload one — our AI will read your emotional state.")

    tab_cam, tab_upload = st.tabs(["📷  Camera", "📁  Upload"])

    image_bytes = None

    with tab_cam:
        photo = st.camera_input("Look at the camera naturally, then click capture")
        if photo:
            image_bytes = photo.getvalue()

    with tab_upload:
        uploaded = st.file_uploader("Upload a clear photo of your face", type=["jpg", "jpeg", "png"])
        if uploaded:
            image_bytes = uploaded.read()

    if image_bytes:
        st.markdown("---")
        notes = st.text_input("📝 Add a note  *(optional)*", placeholder="What's on your mind right now?")

        if st.button("🔍  Analyze My Emotion", type="primary", use_container_width=True):

            with st.spinner("Reading your expression..."):
                result     = ai.analyze_emotion(image_bytes)
                recent     = db.get_recent_emotions(st.session_state.user_name, 5)
                reflection = ai.generate_reflection_questions(result["primary_emotion"], recent)

            # Save image to disk
            ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
            user_folder = f"captures/{st.session_state.user_name}"
            os.makedirs(user_folder, exist_ok=True)
            img_path    = f"{user_folder}/{ts}.jpg"
            img         = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img.save(img_path, "JPEG")

            # Save to DB
            db.save_emotion(
                user_name            = st.session_state.user_name,
                primary_emotion      = result["primary_emotion"],
                emotion_scores       = result.get("emotion_breakdown", {}),
                ai_analysis          = result["analysis"],
                reflection_questions = reflection,
                image_path           = img_path,
                notes                = notes
            )

            # Store in session
            st.session_state.last_result     = result
            st.session_state.last_reflection = reflection

            # ── Display result ──────────────────────────────────
            emotion    = result["primary_emotion"]
            emoji      = result.get("emoji", EMOTION_EMOJI.get(emotion, "❓"))
            color      = EMOTION_COLOR.get(emotion, "#888")
            confidence = result.get("confidence", 0)

            st.markdown(emotion_card_html(emotion, emoji, confidence, color), unsafe_allow_html=True)
            st.progress(confidence / 100)

            # Breakdown badges
            breakdown = result.get("emotion_breakdown", {})
            if breakdown:
                st.markdown('<span class="label">Emotion Breakdown</span>', unsafe_allow_html=True)
                badges = ""
                for em, pct in sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:5]:
                    c = EMOTION_COLOR.get(em, "#888")
                    e = EMOTION_EMOJI.get(em, "❓")
                    badges += badge_html(f"{e} {em}  {pct}%", c)
                st.markdown(badges, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown('<span class="label">AI Analysis</span>', unsafe_allow_html=True)
            st.info(result["analysis"])

            st.markdown('<span class="label">Reflection Questions</span>', unsafe_allow_html=True)
            with st.expander("See your reflection questions"):
                st.markdown(reflection)

            st.success("✅ Saved to your emotional history.")


# ═══════════════════════════════════════════════════════════════════
# PAGE — HISTORY
# ═══════════════════════════════════════════════════════════════════
elif page == "📋  History":
    st.markdown("## Emotional History")

    history = db.get_user_history(st.session_state.user_name)

    if not history:
        st.info("No captures yet — head to **Capture** to get started.")
    else:
        st.caption(f"{len(history)} record{'s' if len(history) != 1 else ''} found")
        st.markdown("")

        for row in history:
            _, timestamp, emotion, scores_json, analysis, reflection, notes, img_path = row
            color = EMOTION_COLOR.get(emotion, "#888")
            emoji = EMOTION_EMOJI.get(emotion, "❓")

            with st.expander(f"{emoji}  **{emotion.capitalize()}**  ·  {timestamp}"):
                if img_path and os.path.exists(img_path):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.image(img_path, width=160)
                    with c2:
                        st.markdown('<span class="label">Analysis</span>', unsafe_allow_html=True)
                        st.write(analysis)
                        if notes:
                            st.caption(f"📝 {notes}")
                else:
                    st.markdown('<span class="label">Analysis</span>', unsafe_allow_html=True)
                    st.write(analysis)
                    if notes:
                        st.caption(f"📝 {notes}")

                if reflection:
                    st.markdown("---")
                    st.markdown('<span class="label">Reflection Questions</span>', unsafe_allow_html=True)
                    st.markdown(reflection)

                # Breakdown badges
                try:
                    breakdown = json.loads(scores_json) if scores_json else {}
                    if breakdown:
                        st.markdown("---")
                        st.markdown('<span class="label">Breakdown</span>', unsafe_allow_html=True)
                        badges = ""
                        for em, pct in sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:5]:
                            c = EMOTION_COLOR.get(em, "#888")
                            e = EMOTION_EMOJI.get(em, "❓")
                            badges += badge_html(f"{e} {em}  {pct}%", c)
                        st.markdown(badges, unsafe_allow_html=True)
                except Exception:
                    pass


# ═══════════════════════════════════════════════════════════════════
# PAGE — INSIGHTS
# ═══════════════════════════════════════════════════════════════════
elif page == "📊  Insights":
    st.markdown("## Emotional Insights")

    counts  = db.get_emotion_counts(st.session_state.user_name)
    history = db.get_recent_emotions(st.session_state.user_name, 20)

    if not counts:
        st.info("Capture at least 2–3 emotions to unlock your insights.")
    else:
        # ── Bar chart ──────────────────────────────────────────
        emotions = [c[0] for c in counts]
        values   = [c[1] for c in counts]
        colors   = [EMOTION_COLOR.get(e, "#888") for e in emotions]
        labels   = [f"{EMOTION_EMOJI.get(e,'❓')}  {e.capitalize()}" for e in emotions]

        fig = go.Figure(go.Bar(
            x               = values,
            y               = labels,
            orientation     = "h",
            marker_color    = colors,
            text            = values,
            textposition    = "outside",
            textfont        = dict(size=13, color="white")
        ))
        fig.update_layout(
            paper_bgcolor = "rgba(0,0,0,0)",
            plot_bgcolor  = "rgba(0,0,0,0)",
            font          = dict(color="white", size=13),
            margin        = dict(l=10, r=50, t=10, b=10),
            height        = max(220, len(counts) * 52),
            xaxis         = dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis         = dict(showgrid=False, tickfont=dict(size=14))
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🤖 AI Pattern Analysis")
        st.caption("Let the AI analyze your emotional patterns and give you personal insights.")

        if st.button("Generate Pattern Analysis", type="primary", use_container_width=True):
            with st.spinner("Analyzing your emotional journey..."):
                st.session_state.pattern_text = ai.analyze_patterns(
                    st.session_state.user_name, history, counts
                )

        if st.session_state.pattern_text:
            st.markdown(
                f'<div class="card">{st.session_state.pattern_text}</div>',
                unsafe_allow_html=True
            )


# ═══════════════════════════════════════════════════════════════════
# PAGE — REFLECT
# ═══════════════════════════════════════════════════════════════════
elif page == "💭  Reflect":
    st.markdown("## Reflection Space")
    st.caption("A quiet space to think — your writing here is never saved.")

    recent = db.get_recent_emotions(st.session_state.user_name, 5)

    if not recent:
        st.info("Capture your first emotion to unlock personalized reflection questions.")
    else:
        latest_emotion = recent[0][1]
        emoji          = EMOTION_EMOJI.get(latest_emotion, "❓")
        color          = EMOTION_COLOR.get(latest_emotion, "#888")

        st.markdown(
            f'<div class="card-sm">'
            f'<span class="label">Most Recent Emotion</span>'
            f'<span style="font-size:28px">{emoji}</span>&nbsp;&nbsp;'
            f'<span style="font-size:20px;font-weight:700;color:{color}">'
            f'{latest_emotion.capitalize()}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        st.markdown("")
        if st.button("Generate Reflection Questions", type="primary", use_container_width=True):
            with st.spinner("Thinking thoughtfully..."):
                st.session_state.reflect_q = ai.generate_reflection_questions(
                    latest_emotion, recent
                )

        if st.session_state.reflect_q:
            st.markdown(
                f'<div class="card">'
                f'<span class="label">Your Questions for Today</span><br>'
                f'{st.session_state.reflect_q.replace(chr(10), "<br>")}'
                f'</div>',
                unsafe_allow_html=True
            )

            st.markdown("---")
            st.markdown("### ✍️ Journal")
            st.text_area(
                "Write your thoughts freely here...",
                height=200,
                placeholder="Take your time. There are no right answers.",
                label_visibility="collapsed"
            )