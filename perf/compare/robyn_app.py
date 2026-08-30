"""
Robyn comparable benchmark application.
"""
from robyn import Robyn, jsonify, Response

app = Robyn(__file__)


@app.get("/plaintext")
async def plaintext():
    return "Hello, World!"


@app.get("/json")
async def handle_json():
    return Response(
        status_code=200,
        headers={"Content-Type": "application/json"},
        description=jsonify({"message": "Hello, World!"}),
    )


if __name__ == "__main__":
    app.start(host="127.0.0.1", port=8000)
