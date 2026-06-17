import logging
import textwrap
from typing import AsyncIterable

from livekit import rtc
from livekit.agents import Agent, ChatContext, ChatMessage, ModelSettings
from livekit.agents import stt as stt_mod

logger = logging.getLogger(__name__)


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=textwrap.dedent(
                """\
                You are a helpful, concise voice assistant.

                Every user message includes an STT confidence prefix in this format:
                  [STT confidence: X.XX] <what the user said>

                Use the confidence score to decide how to respond:

                - Confidence > 0.8: Respond normally to the user's message.
                - Confidence < 0.6: Do not attempt to answer. Politely ask the user
                  to repeat themselves. Example: "Sorry, I may have misunderstood you.
                  Could you please repeat that?"
                - Confidence between 0.6 and 0.8: You may respond, but briefly
                  acknowledge that you might have misheard before answering.

                Never mention the confidence score, STT, or any technical details to the user.
                Respond in plain conversational text only. Keep replies brief (1-3 sentences).
                """
            ),
        )
        self._last_confidence: float = 1.0

    async def stt_node(
        self,
        audio: AsyncIterable[rtc.AudioFrame],
        model_settings: ModelSettings,
    ) -> AsyncIterable[stt_mod.SpeechEvent] | None:
        """Overrides the default STT pipeline node to capture Deepgram's per-transcript
        confidence score from each FINAL_TRANSCRIPT event. The score is stored in
        ``self._last_confidence`` so that ``on_user_turn_completed`` can inject it
        into the LLM context before the model generates a reply.

        All speech events are yielded unchanged so the rest of the pipeline is unaffected.

        Args:
            audio (AsyncIterable[rtc.AudioFrame]): The audio frames
            model_settings (ModelSettings): The model settings

        Yields:
            Iterator[AsyncIterable[stt_mod.SpeechEvent] | None]: The speech events
        """
        async for event in Agent.default.stt_node(self, audio, model_settings):
            if (
                event.type == stt_mod.SpeechEventType.FINAL_TRANSCRIPT
                and event.alternatives
            ):
                self._last_confidence = event.alternatives[0].confidence
                logger.debug(f"Raw STT confidence: {event.alternatives[0].confidence}")
                logger.info(
                    f"STT | confidence={self._last_confidence:.2f} "
                    f"| transcript={event.alternatives[0].text}"
                )
            yield event

    async def on_user_turn_completed(
        self,
        turn_ctx: ChatContext,
        new_message: ChatMessage,
    ) -> None:
        """Overrides the default turn-completion hook to inject the STT confidence score
        into the user message before it is added to the chat context and sent to the LLM.

        Args:
            turn_ctx (ChatContext): The chat context
            new_message (ChatMessage): The new message
        """
        original = new_message.text_content or ""
        new_message.content = [
            f"[STT confidence: {self._last_confidence:.2f}] {original}"
        ]
        logger.info(
            f"Injected confidence into LLM context: confidence={self._last_confidence:.2f}",
        )
