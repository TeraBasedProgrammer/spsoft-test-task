# Spsoft Voice Agent

A confidence-aware voice agent built with LiveKit Agents. The agent uses Deepgram for speech-to-text, Groq (Llama 3.3) as the LLM, and ElevenLabs for text-to-speech. It adjusts its responses based on the STT transcription confidence score returned by Deepgram.

## Pipeline

```
User speech → Deepgram STT → Groq LLM → ElevenLabs TTS → User
```

---

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/TeraBasedProgrammer/spsoft-test-task
cd spsoft-test-task
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment variables

Copy the example file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials (see [API Keys](#api-keys) below).

### 4. Run the agent

```bash
uv run agent dev
```

The agent connects to your LiveKit cloud project and waits for a room to be dispatched to it.

### 5. Test in the browser

1. Go to [cloud.livekit.io](https://cloud.livekit.io) → your project → **Agents**
2. Click **Launch Console**
3. Start a new session — the agent will join automatically
4. Allow microphone access and start talking

---

## API Keys

The following API keys are required. Add each to your `.env` file.

### LiveKit

Used to connect the agent to a LiveKit room.

1. Sign up at [livekit.io/cloud](https://livekit.io/cloud)
2. Create a new project
3. Copy the credentials from the project dashboard

```env
LIVEKIT_URL=wss://<your-project>.livekit.cloud
LIVEKIT_API_KEY=<your-api-key>
LIVEKIT_API_SECRET=<your-api-secret>
```

**Cost:** Free tier available.

---

### Deepgram (STT)

Used for speech-to-text transcription.

1. Sign up at [console.deepgram.com](https://console.deepgram.com)
2. Go to **API Keys** and create a new key

```env
DEEPGRAM_API_KEY=<your-api-key>
```

**Cost:** $200 free credit on sign-up.

---

### Groq (LLM)

Used for LLM inference. Groq provides fast, free-tier access to Llama 3.3.

1. Sign up at [console.groq.com](https://console.groq.com)
2. Go to **API Keys** and create a new key

```env
GROQ_API_KEY=<your-api-key>
```

**Cost:** Free tier available.

---

### ElevenLabs (TTS)

Used for text-to-speech synthesis.

1. Sign up at [elevenlabs.io](https://elevenlabs.io)
2. Go to **Profile → API Keys** and create a new key

```env
ELEVEN_API_KEY=<your-api-key>
```

**Cost:** Free tier includes 10,000 characters/month.

---

## How STT confidence is passed to the LLM

Deepgram returns a confidence score (0.0–1.0) with every final transcription result, indicating how accurately the audio was recognised acoustically.

The agent intercepts this at two points in the LiveKit pipeline:

**1. `stt_node` (in `app/agent.py`)**
Overrides the default STT pipeline node. Each time a `FINAL_TRANSCRIPT` event is received, the confidence score is read from `event.alternatives[0].confidence` and stored on the agent instance:

```python
self._last_confidence = event.alternatives[0].confidence
```

**2. `on_user_turn_completed` (in `app/agent.py`)**
Overrides the turn-completion hook, which fires after STT finishes but before the LLM call. The user's message is modified to include the confidence score as a prefix:

```python
new_message.content = [f"[STT confidence: {self._last_confidence:.2f}] {original}"]
```

This means the LLM receives messages in the following format:

```
[STT confidence: 0.90] I need help with my order
```

The agent's system prompt instructs the LLM to use this value to decide how to respond:

| Confidence | Behaviour |
|---|---|
| > 0.8 | Respond normally |
| 0.6 – 0.8 | Respond but acknowledge possible mishearing |
| < 0.6 | Ask the user to repeat themselves |

**Example — low confidence:**
```
User (mumbled, background music on):  "I need help"
STT confidence:  0.55
LLM receives:    [STT confidence: 0.55] I need help
Agent response:  "Sorry, I may have misunderstood you. Could you please repeat that?"
```

**Example — high confidence:**
```
User (clear):    "What is the weather like today?"
STT confidence:  0.97
LLM receives:    [STT confidence: 0.97] What is the weather like today?
Agent response:  "I don't have access to live weather data, but you can check a weather app for the latest forecast."
```
