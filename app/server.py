from livekit.agents import AgentServer, JobProcess
from livekit.plugins import silero

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm
