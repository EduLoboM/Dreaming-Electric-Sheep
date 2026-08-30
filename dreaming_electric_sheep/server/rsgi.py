"""
RSGI (Rust Server Gateway Interface) support for Dreaming Electric Sheep.
Enables direct protocol integration with Granian RSGI interface.
"""
from __future__ import annotations

import logging
from typing import Any, List, Tuple

from dreaming_electric_sheep.contents import Content, RSGIContent, StreamedContent
from dreaming_electric_sheep.messages import Request, Response

logger = logging.getLogger("dreaming_electric_sheep.server")


def _extract_rsgi_headers(scope) -> List[Tuple[bytes, bytes]]:
    headers: List[Tuple[bytes, bytes]] = []
    for name, value in scope.headers.items():
        name_bytes = name.encode("latin-1") if isinstance(name, str) else name
        value_bytes = value.encode("latin-1") if isinstance(value, str) else value
        headers.append((name_bytes, value_bytes))
    return headers


def instantiate_rsgi_request(scope, protocol) -> Request:
    method: str = scope.method
    path_str: str = scope.path
    raw_path: bytes = path_str.encode("utf-8")
    query_str: str = scope.query_string
    raw_query: bytes = query_str.encode("latin-1") if query_str else b""

    headers = _extract_rsgi_headers(scope)

    request = Request.incoming(
        method,
        raw_path,
        raw_query,
        headers,
    )
    request.scope = scope
    request.content = RSGIContent(protocol)
    return request


_CT_CACHE: dict[bytes, str] = {
    b"text/html; charset=utf-8": "text/html; charset=utf-8",
    b"text/html": "text/html",
    b"application/json": "application/json",
    b"text/plain": "text/plain",
    b"text/plain; charset=utf-8": "text/plain; charset=utf-8",
}


async def send_rsgi_response(response: Response, protocol: Any) -> None:
    resp_headers = response.headers
    if resp_headers:
        headers = [
            (
                h.name.decode("latin-1") if isinstance(h.name, bytes) else str(h.name),
                h.value.decode("latin-1") if isinstance(h.value, bytes) else str(h.value),
            )
            for h in resp_headers
        ]
    else:
        headers = []

    content: Content = response.content
    if content is not None:
        if content.type and not any(h[0].lower() == "content-type" for h in headers):
            ct_bytes = content.type
            ct_str = _CT_CACHE.get(ct_bytes)
            if ct_str is None:
                ct_str = ct_bytes.decode("latin-1") if isinstance(ct_bytes, bytes) else str(ct_bytes)
            headers.append(("content-type", ct_str))

        body = content.body
        if body is not None:
            if isinstance(body, bytes):
                protocol.response_bytes(response.status, headers, body)
                return
            elif isinstance(body, str):
                protocol.response_str(response.status, headers, body)
                return
            elif isinstance(body, (memoryview, bytearray)):
                protocol.response_bytes(response.status, headers, bytes(body))
                return
            else:
                protocol.response_str(response.status, headers, str(body))
                return

        if isinstance(content, StreamedContent):
            trx = await protocol.response_stream(response.status, headers)
            async for chunk in content.stream():
                if chunk:
                    if isinstance(chunk, bytes):
                        await trx.send_bytes(chunk)
                    elif isinstance(chunk, str):
                        await trx.send_str(chunk)
                    else:
                        await trx.send_bytes(bytes(chunk))
            return

    protocol.response_empty(response.status, headers)
