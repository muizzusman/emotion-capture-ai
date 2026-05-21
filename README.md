# 🧠 Emotion Capture AI

> Track your emotions over time, discover patterns, and grow in self-awareness — powered by Claude AI.

---

## What It Does

Emotion Capture AI lets you photograph your face and receive an instant AI-powered emotional analysis.
Over time, it builds a personal emotional history and identifies your emotional patterns,
while offering thoughtful reflection questions to deepen self-awareness.

### Core Features

* **📸 Emotion Capture** — Take a photo or upload one; Claude Vision analyzes your facial expression
* **📋 History** — View your full emotional timeline with images and AI notes
* **📊 Insights** — See frequency charts and AI-generated pattern analysis
* **💭 Reflect** — Personalized introspective questions and a private journal space

---

## Tech Stack

| Layer     | Technology                                                |
| --------- | --------------------------------------------------------- |
| Frontend  | Python + Streamlit                                        |
| AI Engine | Anthropic Claude claude-sonnet-4-20250514 (Vision + Text) |
| Database  | SQLite (local, no setup needed)                           |
| Charts    | Plotly                                                    |

---

## Setup & Installation

### Prerequisites

* Python 3.9 or higher
* An Anthropic API key ([get one here](https://console.anthropic.com))

### Steps

**1. Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/emotion-capture-ai.git
cd emotion-capture-ai
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure your API key**

Create a `.env` file in the root folder:

```env
ANTHROPIC_API_KEY=your_key_here
```

**4. Run the app**

```bash
streamlit run app.py
```

**5. Open in browser**

Navigate to:

```text
http://localhost:8501
```

---

## Folder Structure

```text
emotion-capture-ai/
├── app.py              # Main Streamlit application
├── database.py         # SQLite operations
├── ai_engine.py        # Claude API functions
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .streamlit/
│   └── config.toml     # Theme configuration
└── captures/           # Saved face images (local only, gitignored)
```

---

## Environment Variables

| Variable            | Description            |
| ------------------- | ---------------------- |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

---

## Team

* Abdul Muizz Usman | 23018065001
* Daniyal Shams | 23018065071
* Muhammad Tahir | 23018065012

---

## Demo

[Link to 5-minute screen recording]