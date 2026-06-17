from livekit.agents import AgentSession, JobContext, inference
from livekit.plugins import deepgram, groq

from .agent import Assistant
from .server import server


@server.rtc_session(agent_name="spsoft-test-voice-agent")
async def spsoft_test_voice_agent(ctx: JobContext):
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="en"),
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=inference.TTS(
            model="elevenlabs/eleven_turbo_v2_5",
            voice="Xb7hH8MSUJpSbSDYk0k2",
            language="en",
        ),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
    )

    await ctx.connect()
