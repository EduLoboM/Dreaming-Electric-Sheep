"""
Dreaming Electric Sheep comparable benchmark application.
"""
from dreaming_electric_sheep import Application, get, json, text

app = Application()


@get("/plaintext")
async def plaintext():
    return text("Hello, World!")


@get("/json")
async def handle_json():
    return json({"message": "Hello, World!"})
