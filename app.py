from flask import Flask, request, Response
from flask_cors import CORS
from openai import OpenAI
import os
import json

app = Flask(__name__)
CORS(app)

client = OpenAI(
    api_key=os.getenv("AIPIPE_TOKEN"),
    base_url="https://api.aipipe.org/v1"
)

@app.route("/stream", methods=["POST"])
def stream():

    data = request.get_json()
    prompt = data.get("prompt", "")

    def generate():
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

            for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'content': delta.content})}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        },
        direct_passthrough=True
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, threaded=True)
