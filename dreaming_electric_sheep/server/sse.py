"""
This module offers built-in functions for Server Sent Events (SSE) and Newline-Delimited JSON (NDJSON) streaming.
"""

from typing import Any, AsyncIterable, Callable

import msgspec.json

from dreaming_electric_sheep.contents import (
    ServerSentEvent,
    StreamedContent,
    TextServerSentEvent,
)
from dreaming_electric_sheep.messages import Response
from dreaming_electric_sheep.scribe import write_sse

__all__ = [
    "ServerSentEvent",
    "TextServerSentEvent",
    "ServerSentEventsContent",
    "ServerSentEventsResponse",
    "EventsProvider",
    "JSONLinesContent",
    "JSONLinesResponse",
    "NDJSONResponse",
    "JSONLinesProvider",
]


EventsProvider = Callable[[], AsyncIterable[ServerSentEvent]]
JSONLinesProvider = Callable[[], AsyncIterable[Any]]


class ServerSentEventsContent(StreamedContent):
    """
    A specialized kind of StreamedContent that can be used to stream
    Server-Sent Events to a client with proper disconnect cancellation.
    """

    def __init__(self, events_provider: EventsProvider):
        super().__init__(b"text/event-stream", self.write_events(events_provider))

    @staticmethod
    def write_events(
        events_provider: EventsProvider,
    ) -> Callable[[], AsyncIterable[bytes]]:
        async def write_events():
            gen = events_provider()
            try:
                async for event in gen:
                    yield write_sse(event)
            except BaseException:
                if hasattr(gen, "aclose"):
                    try:
                        await gen.aclose()
                    except Exception:
                        pass
                raise
            finally:
                if hasattr(gen, "aclose"):
                    try:
                        await gen.aclose()
                    except Exception:
                        pass

        return write_events


class ServerSentEventsResponse(Response):
    """
    A Response type that streams Server-Sent Events to a client (text/event-stream).
    Used for OpenAI-compatible token streaming, vLLM, and TGI serving.
    """

    def __init__(
        self,
        events_provider: EventsProvider,
        status: int = 200,
        headers: list[tuple[bytes, bytes]] | None = None,
    ) -> None:
        if headers is None:
            headers = [
                (b"Cache-Control", b"no-cache"),
                (b"Connection", b"Keep-Alive"),
                (b"Content-Type", b"text/event-stream"),
            ]
        super().__init__(status, headers, ServerSentEventsContent(events_provider))


class JSONLinesContent(StreamedContent):
    """
    A specialized StreamedContent for streaming newline-delimited JSON (application/x-ndjson).
    Ideal for high-throughput batch inference, embedding pipelines, and dataset streaming.
    """

    def __init__(self, data_provider: JSONLinesProvider):
        super().__init__(b"application/x-ndjson", self.write_lines(data_provider))

    @staticmethod
    def write_lines(
        data_provider: JSONLinesProvider,
    ) -> Callable[[], AsyncIterable[bytes]]:
        async def write_lines():
            gen = data_provider()
            try:
                async for item in gen:
                    if isinstance(item, bytes):
                        line = item if item.endswith(b"\n") else item + b"\n"
                    elif isinstance(item, str):
                        line = (
                            item.encode("utf8")
                            if item.endswith("\n")
                            else (item + "\n").encode("utf8")
                        )
                    else:
                        line = msgspec.json.encode(item) + b"\n"
                    yield line
            except BaseException:
                if hasattr(gen, "aclose"):
                    try:
                        await gen.aclose()
                    except Exception:
                        pass
                raise
            finally:
                if hasattr(gen, "aclose"):
                    try:
                        await gen.aclose()
                    except Exception:
                        pass

        return write_lines


class JSONLinesResponse(Response):
    """
    Response type for streaming newline-delimited JSON (application/x-ndjson).
    """

    def __init__(
        self,
        data_provider: JSONLinesProvider,
        status: int = 200,
        headers: list[tuple[bytes, bytes]] | None = None,
    ) -> None:
        if headers is None:
            headers = [
                (b"Cache-Control", b"no-cache"),
                (b"Connection", b"Keep-Alive"),
                (b"Content-Type", b"application/x-ndjson"),
            ]
        super().__init__(status, headers, JSONLinesContent(data_provider))


NDJSONResponse = JSONLinesResponse
