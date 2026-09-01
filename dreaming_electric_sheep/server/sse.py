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
            gen = events_provider() if callable(events_provider) and not hasattr(events_provider, "__aiter__") else events_provider
            try:
                async for event in gen:
                    if isinstance(event, (ServerSentEvent, TextServerSentEvent)):
                        yield write_sse(event)
                    elif isinstance(event, bytes):
                        yield event if event.endswith(b"\n\n") else (event + b"\n\n")
                    elif isinstance(event, str):
                        yield write_sse(TextServerSentEvent(event))
                    elif isinstance(event, dict):
                        yield write_sse(ServerSentEvent(event))
                    else:
                        yield write_sse(TextServerSentEvent(str(event)))
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
            gen = data_provider() if callable(data_provider) and not hasattr(data_provider, "__aiter__") else data_provider
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


def sse_stream(
    generator: Any,
    status: int = 200,
    headers: list[tuple[bytes, bytes]] | None = None,
) -> ServerSentEventsResponse:
    """
    Creates an SSE streaming Response from an async generator, sync iterable, or callable.
    """
    if callable(generator) and not hasattr(generator, "__aiter__") and not hasattr(generator, "__iter__"):
        provider = generator
    elif hasattr(generator, "__aiter__"):
        provider = lambda: generator
    elif hasattr(generator, "__iter__"):
        async def _sync_to_async():
            for item in generator:
                yield item
        provider = _sync_to_async
    else:
        provider = generator

    return ServerSentEventsResponse(provider, status=status, headers=headers)


def ndjson_stream(
    generator: Any,
    status: int = 200,
    headers: list[tuple[bytes, bytes]] | None = None,
) -> NDJSONResponse:
    """
    Creates an NDJSON streaming Response from an async generator, sync iterable, or callable.
    """
    if callable(generator) and not hasattr(generator, "__aiter__") and not hasattr(generator, "__iter__"):
        provider = generator
    elif hasattr(generator, "__aiter__"):
        provider = lambda: generator
    elif hasattr(generator, "__iter__"):
        async def _sync_to_async():
            for item in generator:
                yield item
        provider = _sync_to_async
    else:
        provider = generator

    return NDJSONResponse(provider, status=status, headers=headers)
