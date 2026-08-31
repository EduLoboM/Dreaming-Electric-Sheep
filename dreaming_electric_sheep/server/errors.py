from __future__ import annotations

import html
import linecache
import traceback
from typing import Any

from dreaming_electric_sheep.contents import HTMLContent
from dreaming_electric_sheep.messages import Request, Response
from dreaming_electric_sheep.server.asgi import get_request_url
from dreaming_electric_sheep.server.resources import get_resource_file_content

_SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "key",
    "access_token",
    "private_key",
    "certificate",
    "cert",
}


def _sanitize_repr(name: str, value: Any) -> str:
    name_lower = name.lower()
    if any(k in name_lower for k in _SENSITIVE_KEYS):
        return "<redacted (sensitive)>"
    try:
        r = repr(value)
        if len(r) > 200:
            return r[:200] + "... (truncated)"
        return r
    except Exception:
        return "<unprintable object>"


def _load_error_page_template() -> str:
    error_css = get_resource_file_content("error.css")
    error_template = get_resource_file_content("error.html")
    assert "/*STYLES*/" in error_template

    error_css = error_css.replace("{", "{{").replace("}", "}}")
    return error_template.replace("/*STYLES*/", error_css)


class ServerErrorDetailsHandler:
    """
    Produces a rich diagnostic response when the Application is configured
    with show_error_details=True, including sanitized frame locals, source lines,
    and CLI debug suggestions (des why METHOD PATH).
    """

    def __init__(self) -> None:
        self._error_page_template = _load_error_page_template()

    def produce_response(self, request: Request, exc: Exception) -> Response:
        frames_html = []
        tb = exc.__traceback__

        while tb is not None:
            frame = tb.tb_frame
            lineno = tb.tb_lineno
            code = frame.f_code
            filename = code.co_filename
            func_name = code.co_name

            line = linecache.getline(filename, lineno).strip()

            # Extract and sanitize frame locals
            locals_list = []
            for k, v in frame.f_locals.items():
                if k.startswith("__"):
                    continue
                safe_val = _sanitize_repr(k, v)
                locals_list.append(
                    f'<div class="local-var"><span class="var-name">{html.escape(k)}</span> = '
                    f'<span class="var-val">{html.escape(safe_val)}</span></div>'
                )

            locals_html = (
                "".join(locals_list)
                if locals_list
                else '<div class="local-var none">(no local variables)</div>'
            )

            frames_html.append(
                f'<li class="frame-item">'
                f'<div class="frame-header">'
                f'<span class="frame-file">{html.escape(filename)}</span> : '
                f'<span class="frame-line">line {lineno}</span> in '
                f'<span class="frame-func">{html.escape(func_name)}</span>'
                f"</div>"
                f"<pre class=\"frame-code\"><code>{html.escape(line) if line else '(no source available)'}</code></pre>"
                f'<details class="frame-locals"><summary>Local variables ({len(locals_list)})</summary>'
                f'<div class="locals-body">{locals_html}</div>'
                f"</details>"
                f"</li>"
            )
            tb = tb.tb_next

        method = request.method or "GET"
        path = request.path or "/"
        try:
            full_url = get_request_url(request)
        except Exception:
            full_url = path

        mod = exc.__class__.__module__
        if mod and mod != "builtins":
            full_exctype = f"{mod}.{exc.__class__.__name__}"
        else:
            full_exctype = exc.__class__.__name__

        tb_list = traceback.format_exception(exc.__class__, exc, exc.__traceback__)
        raw_traceback = "".join(tb_list)

        content = HTMLContent(
            self._error_page_template.format_map(
                {
                    "info": "".join(frames_html),
                    "raw_traceback": html.escape(raw_traceback),
                    "exctype": html.escape(full_exctype),
                    "excmessage": html.escape(str(exc)),
                    "method": html.escape(method),
                    "path": html.escape(path),
                    "full_url": html.escape(full_url),
                }
            )
        )

        return Response(500, content=content)
