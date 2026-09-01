from typing import List
import pytest
from des import Application, Request, json
from dreaming_electric_sheep.testing import TestClient


def test_request_get_query_param_direct():
    req = Request.incoming("GET", b"/test", b"name=Alice&age=30&active=true&score=98.5&tags=python&tags=rust&empty=", [])
    
    assert req.get_query_param("name") == "Alice"
    assert req.get_query_param("age") == "30"
    assert req.get_query_param("active") == "true"
    assert req.get_query_param("score") == "98.5"
    assert req.get_query_param("empty") == ""
    assert req.get_query_param("missing") is None
    assert req.get_query_param("missing", "fallback") == "fallback"
    
    # get_query_params list extraction
    tags = req.get_query_params("tags")
    assert tags == ["python", "rust"]
    
    # URL encoded values
    req_encoded = Request.incoming("GET", b"/test", b"q=hello%20world&special=%24100%2B200&plus=foo+bar", [])
    assert req_encoded.get_query_param("q") == "hello world"
    assert req_encoded.get_query_param("special") == "$100+200"
    assert req_encoded.get_query_param("plus") == "foo bar"


@pytest.mark.asyncio
async def test_fast_query_binder_in_app():
    app = Application()

    @app.router.get("/search")
    def search_endpoint(q: str, limit: int = 10, offset: int = 0, exact: bool = False, score: float = 0.0):
        return json({
            "q": q,
            "limit": limit,
            "offset": offset,
            "exact": exact,
            "score": score,
        })

    @app.router.get("/tags")
    def tags_endpoint(tag: List[str]):
        return json({"tags": tag})

    await app.start()
    client = TestClient(app)

    # Defaults
    res = await client.get("/search?q=neural")
    assert res.status == 200
    data = await res.json()
    assert data["q"] == "neural"
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert data["exact"] is False
    assert data["score"] == 0.0

    # Custom typed query params
    res = await client.get("/search?q=sheep&limit=50&offset=5&exact=1&score=99.9")
    assert res.status == 200
    data = await res.json()
    assert data["q"] == "sheep"
    assert data["limit"] == 50
    assert data["offset"] == 5
    assert data["exact"] is True
    assert data["score"] == 99.9

    # List query params
    res = await client.get("/tags?tag=cyber&tag=punk")
    assert res.status == 200
    data = await res.json()
    assert data["tags"] == ["cyber", "punk"]

    # Missing required query param
    res_err = await client.get("/search")
    assert res_err.status == 400

    # Invalid int format
    res_bad = await client.get("/search?q=test&limit=not_an_int")
    assert res_bad.status == 400
