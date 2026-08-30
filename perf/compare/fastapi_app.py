"""
FastAPI comparable benchmark application.
"""
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)


@app.get("/plaintext", response_class=PlainTextResponse)
async def plaintext():
    return "Hello, World!"


@app.get("/json")
async def handle_json():
    return {"message": "Hello, World!"}
